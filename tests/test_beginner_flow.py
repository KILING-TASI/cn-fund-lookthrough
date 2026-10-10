import copy,json,tempfile,unittest
from pathlib import Path
from cnlookthrough.guide import config_from_answers,prepare_csv,main as guide
from cnlookthrough.question import compose,allocations,publish,main as question

ROOT=Path(__file__).resolve().parents[1]

class BeginnerFlow(unittest.TestCase):
    def test_explicit_chinese_columns_keep_raw_and_do_not_guess_market(self):
        raw='证券代码,交易所,权重百分数,公司,身份依据\n600519,上交所,3.18%,教学公司,教学身份声明\n'.encode('utf-8')
        converted,record=prepare_csv(raw)
        self.assertIn(b'CN-SSE:600519,3.18',converted)
        self.assertEqual(record['originalRows'][0]['values']['权重百分数'],'3.18%')
        self.assertFalse(record['identityVerified'])
        with self.assertRaisesRegex(ValueError,'不能按代码猜'):prepare_csv(raw.replace('上交所'.encode(),b''))
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

    def test_no_company_mapping_does_not_become_no_overlap(self):
        source=json.loads((ROOT/'examples/demo.json').read_text(encoding='utf-8'));source['positions']=[dict(source['positions'][0],weight=1)];source['securities']={}
        with tempfile.TemporaryDirectory() as t:
            spec=compose([source,source],[.5,.5],source['asOf'])
            result=publish(spec,Path(t)/'no-mapping',{},[source,source])
            self.assertIn('暂不能判断',result['questionAnswer']['answer'])
            self.assertNotIn('尚未发现',result['questionAnswer']['answer'])

if __name__=='__main__':unittest.main()
