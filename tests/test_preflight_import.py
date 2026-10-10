import copy,json,tempfile,unittest,subprocess,sys,hashlib
from pathlib import Path
from cnlookthrough.preflight import inspect
from cnlookthrough.csv_import import convert
from cnlookthrough.engine import analyze
ROOT=Path(__file__).resolve().parents[1]
class InputTests(unittest.TestCase):
    def config(self):return json.loads((ROOT/'examples/holdings-import-config.json').read_text('utf-8'))
    def raw(self):return (ROOT/'examples/holdings-import.csv').read_bytes()
    def test_import_preserves_percent_source_unknown_and_identity_gap(self):
        raw=self.raw();spec=convert(raw,self.config());r=analyze(spec)
        self.assertAlmostEqual(r['knownExposure'],.35);self.assertAlmostEqual(r['unknownExposure'],.65)
        self.assertAlmostEqual(r['unmappedStockIssuerExposure'],.15)
        self.assertAlmostEqual(r['issuerExposure']['教学公司A'],.2)
        self.assertEqual(spec['metadata']['inputCsvSha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(spec['metadata']['originalRows'][0]['values']['weightPercent'],'20')
        self.assertFalse(spec['metadata']['sourceVerified'])
    def test_missing_mapping_is_not_fabricated(self):
        spec=convert(self.raw().replace('教学身份声明（非真实研究）'.encode(),b'').replace('教学公司A'.encode(),b''),self.config())
        self.assertNotIn('CN-SSE:600000',spec['securities'])
        self.assertAlmostEqual(analyze(spec)['unknownExposure'],.85)
    def test_invalid_source_formats_are_rejected(self):
        for raw in [self.raw().replace(b'20,',b'20%,',1),self.raw().replace(b'CN-SSE:600000',b'600000'),self.raw()+self.raw().split(b'\n')[1]+b'\n',self.raw().replace(b'20,',b'90,',1),self.raw().replace(b'identitySource',b'unknown')]:
            with self.assertRaises(ValueError):convert(raw,self.config())
        for patch in [{'weightBasis':'equity-only'},{'publishedAt':'2027-01-01'},{'format':'PCF'}]:
            with self.assertRaises(ValueError):convert(self.raw(),dict(self.config(),**patch))
    def test_preflight_lists_fields_without_exposure_computation(self):
        spec=convert(self.raw(),self.config());spec['positions'][0].pop('weight');spec['nodes']['teaching-fund'].pop('source')
        r=inspect(spec);self.assertEqual(r['status'],'invalid')
        self.assertEqual({e['fieldPath'] for e in r['errors']},{'positions[0].weight','nodes[teaching-fund].source'})
        self.assertFalse(r['calculationPerformed']);self.assertFalse(r['originalVerified'])
    def test_preflight_valid_still_has_unknown_and_runtime_limits(self):
        r=inspect(convert(self.raw(),self.config()));self.assertEqual(r['status'],'declared-fields-valid')
        self.assertTrue(r['warnings']);self.assertNotIn('knownExposure',r)
    def test_cli_preflight_and_import_refuse_output_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'import.json'
            args=[sys.executable,'-m','cnlookthrough.csv_import',str(ROOT/'examples/holdings-import.csv'),'--config',str(ROOT/'examples/holdings-import-config.json')]
            p=subprocess.run(args+['--validate-only'],capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
            self.assertFalse(out.exists())
            p=subprocess.run(args+['--out',str(out)],capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
            before=out.read_bytes();p=subprocess.run(args+['--out',str(out)],capture_output=True)
            self.assertEqual(p.returncode,2);self.assertEqual(before,out.read_bytes())
            p=subprocess.run([sys.executable,'-m','cnlookthrough',str(out),'--validate-only','--out',str(Path(d)/'blocked.json')],capture_output=True)
            self.assertEqual(p.returncode,2);self.assertFalse((Path(d)/'blocked.json').exists())
