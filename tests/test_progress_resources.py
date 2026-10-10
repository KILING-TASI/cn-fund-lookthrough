import io,json,unittest
from pathlib import Path
from cnlookthrough import analyze
from cnlookthrough.progress import Progress
from cnlookthrough.report import html_report
class Tests(unittest.TestCase):
    def sample(self):return json.loads((Path(__file__).parents[1]/'examples/demo.json').read_text('utf-8'))
    def test_callback_preserves_numeric_result_and_reports_stages(self):
        events=[];spec=self.sample();plain=analyze(spec);observed=analyze(spec,progress=lambda *e:events.append(e))
        self.assertEqual(plain,observed);self.assertEqual(events[0][0],'input-check');self.assertEqual(events[-1][0],'complete')
    def test_auto_progress_waits_and_throttles(self):
        times=iter([0,0,11,11.5,12]);stream=io.StringIO();p=Progress(stream=stream,clock=lambda:next(times))
        p('input-check');self.assertEqual(stream.getvalue(),'')
        p('traverse',1000);p('traverse',2000);p('complete',3000)
        self.assertEqual(len(stream.getvalue().splitlines()),2);self.assertNotIn('2000',stream.getvalue())
    def test_long_text_warns_without_changing_issuer_mapping(self):
        spec=self.sample();name='公司'+('X'*50000);spec['securities']['CN-SSE:DEMO-A']['issuer']=name
        r=analyze(spec);self.assertIn(name,r['issuerExposure']);self.assertTrue(any(w['code']=='long-display-text' for w in r['inputDiagnostics']['warnings']))
        page=html_report(r,spec);self.assertIn('影响结论的关键缺口',page);self.assertIn('<details>',page)
    def test_layered_report_keeps_input_and_all_unknown_paths(self):
        spec=self.sample();r=analyze(spec);page=html_report(r,spec)
        self.assertIn('本次结论',page);self.assertIn('保存的输入与方法摘要',page)
        for row in r['unknown']:self.assertIn(row['reason'],page)
