import json,copy,unittest
from pathlib import Path
from cnlookthrough.engine import analyze
class Tests(unittest.TestCase):
 def spec(self):return json.loads((Path(__file__).resolve().parents[1]/'examples/demo.json').read_text(encoding='utf-8'))
 def test_unknown_schema_rejected_and_legacy_unchanged(self):
  s=self.spec();baseline=analyze(s);s['inputSchema']='cnlookthrough-nodes-v1';self.assertEqual(analyze(s),baseline);s['inputSchema']='future-999'
  with self.assertRaises(ValueError):analyze(s)
  self.assertEqual(s['inputSchema'],'future-999')
 def test_wrong_denominator_cannot_hide_unreported_balance(self):
  s=self.spec();s['nodes']['etf']['weightBasis']='equity'
  with self.assertRaises(ValueError):analyze(s)
  s=self.spec();s['nodes']['etf']['renormalized']=True
  with self.assertRaises(ValueError):analyze(s)
 def test_disclosure_unavailable_at_cutoff_rejected(self):
  s=self.spec();s['asOf']='2026-07-01'
  with self.assertRaises(ValueError):analyze(s)
if __name__=='__main__':unittest.main()
