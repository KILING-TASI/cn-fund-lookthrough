import copy,json,tempfile,unittest
from pathlib import Path
from cnlookthrough.guide import config_from_answers,main as guide
from cnlookthrough.question import compose,allocations,publish,main as question

ROOT=Path(__file__).resolve().parents[1]

class BeginnerFlow(unittest.TestCase):
    def test_unknown_basis_never_becomes_confirmed(self):
        config=json.loads((ROOT/'examples/holdings-import-config.json').read_text(encoding='utf-8'))
        answers={k:config[k] for k in ['positionId','source','reportDate','publishedAt','asOf','currency','weightBasis','disclosureScope']}
        answers.update(currency='人民币',weightBasis='未知',disclosureScope='1')
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);file=p/'answers.json';file.write_text(json.dumps(answers),encoding='utf-8')
            self.assertEqual(guide(['wizard','--csv',str(ROOT/'examples/holdings-import.csv'),'--answers',str(file),'--out-dir',str(p/'output')]),2)
            self.assertFalse((p/'output').exists())

    def test_follow_preserves_old_and_rejects_mutated_input(self):
        source=json.loads((ROOT/'examples/demo.json').read_text(encoding='utf-8'))
        # Original teaching sources are explicitly adapted into single-fund snapshots.
        inputs=[]
        for root in source['positions']:
            s=copy.deepcopy(source);s['positions']=[dict(root,weight=1)];inputs.append(s)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);spec=compose(inputs,allocations([60,40],2),source['asOf'])
            result=publish(spec,p/'first',dict(type='fund-overlap-question-v1',asOf=source['asOf'],allocationPercent=[60,40]),inputs)
            self.assertGreater(result['unknownExposure'],0)
            frozen=(p/'first/result.json').read_bytes()
            self.assertEqual(question(['follow','--continue-from',str(p/'first'),'--weights','50','50','--out-dir',str(p/'second')]),0)
            self.assertEqual((p/'first/result.json').read_bytes(),frozen)
            self.assertNotEqual((p/'second/result.json').read_bytes(),frozen)
            (p/'first/source-inputs.json').write_text('[]',encoding='utf-8')
            self.assertEqual(question(['follow','--continue-from',str(p/'first'),'--weights','50','50','--out-dir',str(p/'third')]),2)
            self.assertFalse((p/'third').exists())

    def test_mapping_conflict_is_not_silently_selected(self):
        source=json.loads((ROOT/'examples/demo.json').read_text(encoding='utf-8'));source['positions']=[dict(source['positions'][0],weight=1)]
        other=copy.deepcopy(source);other['securities']['CN-SSE:DEMO-A']['issuer']='另一教学公司'
        with self.assertRaisesRegex(ValueError,'映射冲突'):compose([source,other],[.6,.4],source['asOf'])

if __name__=='__main__':unittest.main()
