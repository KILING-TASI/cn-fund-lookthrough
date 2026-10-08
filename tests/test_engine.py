import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from cnlookthrough import analyze
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
    def spec(self):return json.loads((ROOT/'examples/demo.json').read_text('utf-8'))
    def test_nested_weights_and_unknown_conserve_total(self):
        r=analyze(self.spec());self.assertAlmostEqual(r['issuerExposure']['教学公司A'],.524)
        self.assertAlmostEqual(r['unknownExposure'],.16);self.assertAlmostEqual(r['knownExposure']+r['unknownExposure'],1)
    def test_missing_child_is_unknown(self):
        s=self.spec();del s['nodes']['etf'];r=analyze(s);self.assertAlmostEqual(r['unknownExposure'],.7)
    def test_cycle_is_not_zero(self):
        s=self.spec();s['nodes']['etf']['holdings']=[dict(kind='fund',node='feeder',weight=1)]
        r=analyze(s);self.assertTrue(any(x['reason']=='循环投资关系' for x in r['unknown']))
    def test_future_and_currency_rejected(self):
        for patch in [dict(publishedAt='2027-01-01'),dict(currency='USD')]:
            s=self.spec();s['nodes']['etf'].update(patch)
            with self.assertRaises(ValueError):analyze(s)
    def test_leverage_not_truncated(self):
        s=self.spec();s['nodes']['etf']['holdings'][0]['weight']=.9
        with self.assertRaises(ValueError):analyze(s)
    def test_weight_invalid_and_root_not_normalized(self):
        for w in [True,-.1,float('nan'),50]:
            s=self.spec();s['positions'][0]['weight']=w
            with self.assertRaises(ValueError):analyze(s)
    def test_securities_remain_separate_for_one_issuer(self):
        s=self.spec();s['securities']['CN-SSE:DEMO-B']['issuer']='教学公司A';r=analyze(s)
        self.assertIn('CN-SSE:DEMO-B',r['securityExposure']);self.assertAlmostEqual(r['issuerExposure']['教学公司A'],.74)
    def test_unknown_issuer_does_not_fake_effective_count(self):
        s=self.spec()
        for v in s['securities'].values():v.pop('issuer')
        r=analyze(s);self.assertIsNone(r['effectiveMappedEquityIssuers']);self.assertAlmostEqual(r['unmappedStockIssuerExposure'],.84)
    def test_zero_unique_not_interpreted_as_useless(self):
        from cnlookthrough.report import markdown
        self.assertIn('不等于没有配置作用',markdown(analyze(self.spec())))
    def test_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'报告.html';cmd=[sys.executable,'-m','cnlookthrough',str(ROOT/'examples/demo.json'),'--format','html','--out',str(out)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0);before=out.read_bytes()
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2);self.assertEqual(before,out.read_bytes())
if __name__=='__main__':unittest.main()
