import copy,json,unittest
from pathlib import Path
from cnlookthrough.report import html_report
from cnlookthrough.engine import analyze
class Tests(unittest.TestCase):
 def test_filter_sort_retains_input_method_and_unknown_not_recomputed(self):
  spec=json.loads((Path(__file__).resolve().parents[1]/'examples/demo.json').read_text(encoding='utf-8'));r=analyze(spec);before=copy.deepcopy(r);html=html_report(r,spec)
  self.assertEqual(r,before);self.assertIn('result-filter',html);self.assertIn('result-sort',html);self.assertIn('methodSha256',html);self.assertIn('不重新计算',html)
 def test_markup_is_escaped(self):
  from cnlookthrough.html_controls import table
  self.assertIn('&lt;script&gt;',table(['列'],[['<script>']]));self.assertNotIn('<td><script>',table(['列'],[['<script>']]))
if __name__=='__main__':unittest.main()
