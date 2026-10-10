import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from cnlookthrough import analyze

ROOT = Path(__file__).resolve().parents[1]


class InputDiagnostics(unittest.TestCase):
    def spec(self):
        return json.loads((ROOT / 'examples/demo.json').read_text('utf-8'))

    def cli(self, spec, out=None):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'input.json'
            source.write_text(json.dumps(spec, ensure_ascii=False), encoding='utf-8')
            args = [sys.executable, '-m', 'cnlookthrough', str(source)]
            if out is not None:
                args += ['--out', str(out)]
            return subprocess.run(args, cwd=ROOT, capture_output=True)

    def test_frozen_normal_result_and_metadata_compatibility(self):
        spec = self.spec()
        expected = json.loads((ROOT / 'validation/scenarios-20261010/existing-demo/actual.json').read_text('utf-8'))
        self.assertEqual(analyze(spec), expected)
        spec.update(adapterVersion='legacy-adapter', conversionRulesVersion='declared-metadata',
                    teachingAccount={'anything': True}, metadata={'issuerMap': {}}, extensions={'professionalFields': [1]})
        spec['nodes']['etf']['notes'] = 'legacy note'
        spec['securities']['CN-SSE:DEMO-A']['issuerEvidence'] = {'historical': True}
        self.assertEqual(analyze(spec), expected)
        spec['customResearchContext'] = {'privateValue': 'not copied into warnings'}
        result = self.cli(spec)
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed['knownExposure'], expected['knownExposure'])
        self.assertEqual(parsed['inputDiagnostics']['warnings'][0]['code'], 'unused-field')
        self.assertNotIn('privateValue', result.stderr.decode('utf-8'))

    def test_issuer_map_typo_is_diagnosed_without_conversion(self):
        spec = self.spec()
        spec['issuerMap'] = spec.pop('securities')
        before = copy.deepcopy(spec)
        result = self.cli(spec)
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed['knownExposure'], 0)
        self.assertAlmostEqual(parsed['unknownExposure'], 1)
        codes = {w['code'] for w in parsed['inputDiagnostics']['warnings']}
        self.assertEqual(codes, {'unused-issuer-map', 'securities-missing'})
        self.assertIn('kind、issuer', result.stderr.decode('utf-8'))
        self.assertEqual(spec, before)
        valid = self.spec()
        valid['issuerMap'] = {'notUsed': 'not an automatic alias'}
        parsed = json.loads(self.cli(valid).stdout)
        self.assertAlmostEqual(parsed['knownExposure'], .84)
        self.assertEqual(parsed['inputDiagnostics']['warnings'][0]['code'], 'unused-issuer-map')

    def test_true_missing_security_and_missing_issuer_are_different(self):
        spec = self.spec()
        del spec['securities']
        result = json.loads(self.cli(spec).stdout)
        self.assertEqual(result['unknownExposure'], 1)
        self.assertEqual(result['unmappedStockIssuerExposure'], 0)
        spec = self.spec()
        for meta in spec['securities'].values():
            meta.pop('issuer')
        result = json.loads(self.cli(spec).stdout)
        self.assertAlmostEqual(result['knownExposure'], .84)
        self.assertAlmostEqual(result['unknownExposure'], .16)
        self.assertAlmostEqual(result['unmappedStockIssuerExposure'], .84)
        self.assertIsNone(result['effectiveMappedEquityIssuers'])

    def test_bad_mapping_shape_source_and_schema_fail_without_output(self):
        for patch in ('shape', 'source', 'schema'):
            spec = self.spec()
            if patch == 'shape':
                spec['securities']['CN-SSE:DEMO-A'] = 'company-name-only'
            elif patch == 'source':
                spec['securities']['CN-SSE:DEMO-A'].pop('source')
            else:
                spec['inputSchema'] = 'future-999'
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / 'not-created.json'
                result = self.cli(spec, out)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b'')
                self.assertFalse(out.exists())

    def test_nested_miswrite_and_malformed_issuer_are_not_silent(self):
        spec = self.spec()
        meta = spec['securities']['CN-SSE:DEMO-A']
        meta['issuerName'] = meta.pop('issuer')
        result = analyze(spec)
        self.assertAlmostEqual(result['unmappedStockIssuerExposure'], .524)
        self.assertIn('issuerName', result['inputDiagnostics']['warnings'][0]['fieldPath'])
        meta['issuer'] = {'name': 'unsupported object'}
        result = analyze(spec)
        self.assertIn('invalid-issuer-type', {w['code'] for w in result['inputDiagnostics']['warnings']})

    def test_existing_output_keeps_digest_despite_diagnosed_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'old.json'
            out.write_bytes(b'frozen old output')
            before = hashlib.sha256(out.read_bytes()).hexdigest()
            spec = self.spec()
            spec['issuerMap'] = spec.pop('securities')
            result = self.cli(spec, out)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(before, hashlib.sha256(out.read_bytes()).hexdigest())
