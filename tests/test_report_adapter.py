import unittest,copy
from cnlookthrough.report_adapter import to_spec,compare_snapshots
from cnlookthrough.engine import analyze
class Tests(unittest.TestCase):
 def parsed(self):return {'id':'007119','adapterProfile':'ruiyuan-growth-six-column-v1','disclosureScope':'completeEquity','portfolioScope':'fund-all-share-classes','currency':'CNY','reportDate':'2025-12-31','publishedAt':'2026-03-27','sourceUrl':'https://example.org/a.pdf','sourceSha256':'a'*64,'holdings':[{'code':'600001','securityNamespace':'CN-equity','weight':.2,'locator':'PDF页1'},{'code':'00001','securityNamespace':'HK-equity','weight':.3,'locator':'PDF页1'}]}
 def test_conversion_preserves_unknown_and_no_invented_issuers(self):
  result=analyze(to_spec(self.parsed(),'2026-10-09'))
  self.assertAlmostEqual(result['knownExposure'],.5);self.assertAlmostEqual(result['unknownExposure'],.5);self.assertIsNone(result['effectiveMappedEquityIssuers'])
 def test_quarterly_or_late_conversion_rejected(self):
  parsed=self.parsed();parsed['disclosureScope']='top10'
  with self.assertRaises(ValueError):to_spec(parsed,'2026-10-09')
  with self.assertRaises(ValueError):to_spec(self.parsed(),'2025-12-31')
 def test_comparison_keeps_new_missing_unknown_not_transaction(self):
  a=self.parsed();b=copy.deepcopy(a);b['reportDate']='2026-06-30';b['publishedAt']='2026-08-27';b['holdings']=b['holdings'][:1];b['holdings'][0]['weight']=.25
  result=compare_snapshots(a,b);self.assertTrue(any(r['status']=='no-longer-disclosed' and r['afterWeight'] is None for r in result['rows']));self.assertIn('不等于实际买卖',result['limitation'])
  b['portfolioScope']='fund-A-only'
  with self.assertRaises(ValueError):compare_snapshots(a,b)
if __name__=='__main__':unittest.main()
