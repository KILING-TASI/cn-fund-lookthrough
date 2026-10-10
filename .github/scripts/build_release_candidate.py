"""Build exact-HEAD public assets and verify an offline installed teaching run."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

VERSION = '0.2.0'
REPO = Path(__file__).resolve().parents[2]


def build(out, work):
    out, work = Path(out).resolve(), Path(work).resolve()
    out.mkdir(parents=True, exist_ok=False)
    work.mkdir(parents=True, exist_ok=False)
    record = {'version': VERSION, 'status': 'candidate-not-published', 'checks': []}

    def run(args, cwd=work):
        result = subprocess.run(list(map(str, args)), cwd=cwd, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
        return result

    record['sourceCommit'] = run(['git', 'rev-parse', 'HEAD'], REPO).stdout.decode().strip()
    prefix = f'cn-fund-lookthrough-v{VERSION}'
    source_zip = out / (prefix + '-source.zip')
    run(['git', 'archive', '--format=zip', '--prefix=' + prefix + '/', '-o', source_zip, 'HEAD'], REPO)
    with zipfile.ZipFile(source_zip) as archive:
        names = archive.namelist()
        for name in names:
            parts = Path(name).parts
            if any(p in {'.git', '.venv', '__pycache__', 'build', 'dist', 'outputs', 'local-data'} or p.endswith('.egg-info') for p in parts) or name.endswith(('.pdf', '.pyc')):
                raise AssertionError('Unexpected private/cache/source asset: ' + name)
        for required in ('SKILL.md', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'examples/demo.json', 'cnlookthrough/engine.py', 'RELEASE_NOTES.md'):
            assert prefix + '/' + required in names, required
        archive.extractall(work / 'export')
    source = work / 'export' / prefix
    record['checks'].append('exact Git HEAD source ZIP; complete Skill/demo/license resources; no PDF/git/cache/local outputs')
    # Build using the declared setuptools backend, without modifying the user's installation.
    backend = "import setuptools.build_meta as b; b.build_sdist(" + repr(str(out)) + ")"
    run([sys.executable, '-X', 'utf8', '-c', backend], source)
    sdist = out / ('cn_fund_lookthrough-' + VERSION + '.tar.gz')
    with tarfile.open(sdist) as archive:
        members = archive.getmembers()
        for member in members:
            assert not member.issym() and not member.islnk() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
        assert any(m.name.endswith('/SKILL.md') for m in members)
        assert any(m.name.endswith('/examples/demo.json') for m in members)
        if hasattr(tarfile, 'data_filter'):
            archive.extractall(work / 'sdist', filter='data')
        else:
            archive.extractall(work / 'sdist')
    sdist_source = next((work / 'sdist').iterdir())
    backend = "import setuptools.build_meta as b; b.build_wheel(" + repr(str(out)) + ")"
    run([sys.executable, '-X', 'utf8', '-c', backend], sdist_source)
    wheel = out / ('cn_fund_lookthrough-' + VERSION + '-py3-none-any.whl')
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert any(n.endswith('/share/cn-fund-lookthrough/examples/demo.json') for n in names)
        assert len([n for n in names if n.endswith(('/LICENSE', '/THIRD_PARTY_NOTICES.md'))]) == 2
        metadata = archive.read(next(n for n in names if n.endswith('/METADATA'))).decode()
        assert 'Version: ' + VERSION in metadata.splitlines()
        assert not any(n.endswith(('.pdf', '.pyc')) for n in names)
    record['checks'].append('sdist complete Skill/demo resources; wheel built from sdist; version and both license files checked')
    run([sys.executable, '-m', 'venv', work / 'venv'])
    python = work / 'venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    run([python, '-m', 'pip', 'install', '--no-index', '--no-deps', wheel])
    probe = run([python, '-I', '-c', 'import cnlookthrough,sys,json;print(json.dumps(dict(version=cnlookthrough.__version__,origin=cnlookthrough.__file__,prefix=sys.prefix)))'])
    installed = json.loads(probe.stdout)
    assert installed['version'] == VERSION and Path(installed['origin']).is_relative_to(work / 'venv')
    demo = Path(installed['prefix']) / 'share/cn-fund-lookthrough/examples/demo.json'
    assert demo.read_bytes() == (source / 'examples/demo.json').read_bytes()
    cmd = [python, '-I', '-m', 'cnlookthrough', demo]
    result = json.loads(run(cmd).stdout)
    assert result['toolVersion'] == 'cn-fund-lookthrough-' + VERSION
    assert result['rulesVersion'] == 'disclosed-paths-2' and abs(result['unknownExposure'] - .16) < 1e-12
    frozen = json.loads((source / 'validation/scenarios-20261010/existing-demo/actual.json').read_text('utf-8'))
    result_without_version, frozen_without_version = dict(result), dict(frozen)
    result_without_version.pop('toolVersion'); frozen_without_version.pop('toolVersion')
    assert result_without_version == frozen_without_version
    report = work / 'teaching.html'
    run(cmd + ['--format', 'html', '--out', report])
    before = hashlib.sha256(report.read_bytes()).hexdigest()
    repeated = subprocess.run(list(map(str, cmd + ['--format', 'html', '--out', report])), cwd=work, capture_output=True)
    assert repeated.returncode == 2 and before == hashlib.sha256(report.read_bytes()).hexdigest()
    assert '教学' in report.read_text('utf-8')
    typo = json.loads(demo.read_text('utf-8')); typo['issuerMap'] = typo.pop('securities')
    typo_file = work / 'typo.json'; typo_file.write_text(json.dumps(typo), encoding='utf-8')
    warned = run([python, '-I', '-m', 'cnlookthrough', typo_file])
    diagnosed = json.loads(warned.stdout)
    assert diagnosed['unknownExposure'] == 1 and 'issuerMap' in warned.stderr.decode('utf-8')
    record['checks'].append('fresh venv/offline wheel install; bundled demo outside repository; pure JSON, frozen numerical result, HTML, no-overwrite and installed typo diagnostics')
    record['runtime'] = installed
    record['teachingHTMLSha256'] = before
    assets = [source_zip, sdist, wheel]
    record['assets'] = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in assets}
    sums = out / 'SHA256SUMS.txt'
    sums.write_text(''.join(value['sha256'] + '  ' + name + '\n' for name, value in record['assets'].items()), encoding='utf-8', newline='\n')
    record['visualAcceptance'] = 'not performed'
    (out / 'candidate-receipt.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'sourceCommit': record['sourceCommit'], 'version': VERSION, 'assets': record['assets']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--work-dir', required=True)
    args = parser.parse_args()
    build(args.out_dir, args.work_dir)
