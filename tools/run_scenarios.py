"""Run bounded teaching cases through the public CLI; never overwrite a batch."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def check(actual, expected, label):
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise AssertionError(f'{label}: keys {set(actual)} != {set(expected)}')
        for key, value in expected.items():
            check(actual[key], value, label + '.' + key)
    elif isinstance(expected, (float, int)):
        if abs(actual - expected) > 1e-10:
            raise AssertionError(f'{label}: {actual} != {expected}')
    elif actual != expected:
        raise AssertionError(f'{label}: {actual} != {expected}')


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    index = json.loads((ROOT / 'examples/scenarios/index.json').read_text('utf-8'))
    receipt = {k: v for k, v in index.items() if k != 'cases'}
    receipt['cases'] = []
    for case in index['cases']:
        folder = out / case['id']
        folder.mkdir()
        source = ROOT / case['input']
        payload = source.read_bytes()
        (folder / 'input.json').write_bytes(payload)
        expected = case['expected']
        (folder / 'expected.json').write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding='utf-8')
        cmd = [sys.executable, '-m', 'cnlookthrough', str(folder / 'input.json')]
        result = subprocess.run(cmd + ['--out', str(folder / 'actual.json')], cwd=ROOT, capture_output=True)
        stderr = result.stderr.decode('utf-8').replace('\r\n', '\n')
        (folder / 'stderr.txt').write_text(stderr, encoding='utf-8')
        if 'errorContains' in expected:
            if result.returncode != 2 or expected['errorContains'] not in stderr or (folder / 'actual.json').exists():
                raise AssertionError(case['id'] + ': failure must leave no report')
        else:
            if result.returncode != 0:
                raise AssertionError(stderr)
            actual = json.loads((folder / 'actual.json').read_text('utf-8'))
            for key, value in expected.items():
                if key == 'pathCount':
                    observed = len(actual['paths'])
                elif key == 'unknownReasons':
                    observed = {}
                    for row in actual['unknown']:
                        observed[row['reason']] = observed.get(row['reason'], 0) + row['weight']
                else:
                    observed = actual[key]
                check(observed, value, case['id'] + '.' + key)
            for key in ('toolVersion', 'inputSchema', 'rulesVersion'):
                check(actual[key], index[key], case['id'] + '.' + key)
            check(actual['knownExposure'] + actual['unknownExposure'], 1, 'conservation')
            html = subprocess.run(cmd + ['--format', 'html', '--out', str(folder / 'report.html')], cwd=ROOT, capture_output=True)
            if html.returncode:
                raise AssertionError(html.stderr.decode('utf-8'))
            before = (folder / 'actual.json').read_bytes()
            duplicate = subprocess.run(cmd + ['--out', str(folder / 'actual.json')], cwd=ROOT, capture_output=True)
            if duplicate.returncode != 2 or before != (folder / 'actual.json').read_bytes():
                raise AssertionError('repeat CLI changed existing report')
        receipt['cases'].append(dict(id=case['id'], passed=True, exitCode=result.returncode,
                                     inputSha256=hashlib.sha256(payload).hexdigest(), expected=expected))
    receipt['sourceSha256'] = {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted((ROOT / 'cnlookthrough').glob('*.py'))}
    receipt['visualAcceptance'] = 'not-performed'
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    args = parser.parse_args()
    receipt = run(args.out_dir)
    print(f"Passed {len(receipt['cases'])} bounded CLI scenarios")
