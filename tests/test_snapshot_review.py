import unittest,json,copy
from pathlib import Path
from cnlookthrough.snapshot_review import compare
ROOT=Path(__file__).resolve().parents[1]
class SnapshotTests(unittest.TestCase):
 def spec(self):return json.loads((ROOT/'examples/expansion-teaching/compare.json').read_text(encoding='utf-8'))
 def test_missing_not_zero_or_trade(self):
  r=compare(self.spec());self.assertIsNone(r['rows'][1]['afterWeight']);self.assertIsNone(r['rows'][1]['weightChange'])
 def test_wrong_scope(self):
  s=self.spec();s['after']['portfolioScope']='A-share-class'
  with self.assertRaises(ValueError):compare(s)
 def test_duplicates(self):
  s=self.spec();s['after']['holdings'].append(s['after']['holdings'][0])
  with self.assertRaises(ValueError):compare(s)
 def test_renormalized_blocked(self):
  s=self.spec();s['after']['renormalized']=True
  with self.assertRaises(ValueError):compare(s)
