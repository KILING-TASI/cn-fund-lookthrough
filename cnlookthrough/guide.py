"""Chinese stock-disclosure preparation; no guessed identities or source dates."""
import argparse,json,os,tempfile
from pathlib import Path
from .csv_import import FORMAT,convert
from .preflight import inspect
from .__main__ import pairs

QUESTIONS=[('positionId','这份持仓属于哪只基金？填写你确认的名称'),('source','持仓来自哪份报告或导出文件？填写来源与可定位说明'),('reportDate','持仓对应哪天？例如季度末日期，YYYY-MM-DD'),('publishedAt','这份资料哪天公开？与持仓日期不同，YYYY-MM-DD'),('asOf','这次研究截止哪天？YYYY-MM-DD'),('currency','是否为人民币？确认填“人民币”；其他币种或不知道时先停止'),('weightBasis','权重相对什么？1=基金净资产；2=股票部分；不知道填“未知”'),('disclosureScope','资料范围是什么？1=仅部分持仓；2=用户声明全部；不知道填“未知”')]

def config_from_answers(answers):
    if not isinstance(answers,dict):raise ValueError('回答须为对象')
    required={key for key,_ in QUESTIONS}
    if set(answers)!=required:raise ValueError('回答须包含且仅包含 '+','.join(sorted(required)))
    for key in required:
        if not isinstance(answers[key],str) or not answers[key].strip():raise ValueError('尚未确认 '+key+'；不要用教学值补齐')
    answers=dict(answers)
    answers['currency']={'人民币':'CNY','1':'CNY'}.get(answers['currency'],answers['currency'])
    answers['weightBasis']={'1':'parent-net-assets','基金净资产':'parent-net-assets'}.get(answers['weightBasis'],answers['weightBasis'])
    answers['disclosureScope']={'1':'top-holdings','仅部分持仓':'top-holdings','2':'declared-full','用户声明全部':'declared-full'}.get(answers['disclosureScope'],answers['disclosureScope'])
    return dict(format=FORMAT,nodeId='user-disclosed-fund',**answers)

def main(argv=None):
    import sys
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='中文资料准备：先确认口径，再生成输入；不联网、不猜交易所')
    p.add_argument('command',choices=['wizard','init-config']);p.add_argument('--csv',type=Path);p.add_argument('--answers',type=Path);p.add_argument('--out',type=Path);p.add_argument('--out-dir',type=Path)
    a=p.parse_args(argv)
    try:
        if a.command=='init-config':
            if not a.out or a.out_dir or a.csv or a.answers:raise ValueError('init-config 仅接受 --out 新配置文件')
            template=dict(format=FORMAT,nodeId='user-disclosed-fund',**{key:'' for key,_ in QUESTIONS})
            a.out.parent.mkdir(parents=True,exist_ok=True)
            with a.out.open('x',encoding='utf-8') as f:json.dump(template,f,ensure_ascii=False,indent=2)
            print('配置模板已保存；空白项需要真实资料确认。模板尚未通过预检，不要直接计算。')
            for key,label in QUESTIONS:print(key+'：'+label)
            return 0
        if not a.csv or not a.out_dir or a.out:raise ValueError('wizard 需要 --csv 持仓表 和 --out-dir 新结果目录')
        if a.out_dir.exists():raise FileExistsError('结果目录已存在，请换一个新名字')
        if a.answers:
            if a.answers.stat().st_size>1024*1024:raise ValueError('回答文件过大')
            answers=json.loads(a.answers.read_text('utf-8-sig'),object_pairs_hook=pairs)
        else:
            print('先确认资料：CSV 的 weightPercent 填3.18表示3.18%；JSON weight 为0.0318。证券须含明确交易所标识，公司未知可留空，不会按数字前缀猜身份。')
            answers={key:input(label+'：').strip() for key,label in QUESTIONS}
        config=config_from_answers(answers)
        if a.csv.stat().st_size>16*1024*1024:raise ValueError('CSV 超过16MiB')
        spec=convert(a.csv.read_bytes(),config);preflight=inspect(spec)
        from .engine import analyze
        from .report import markdown,html_report
        result=analyze(spec)
        a.out_dir.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.guide-',dir=a.out_dir.parent) as temp:
            stage=Path(temp)/'result';stage.mkdir()
            values={'config.json':config,'input.json':spec,'preflight.json':preflight,'result.json':result,'preparation.json':dict(status='calculated-from-declared-input',inputConfirmed=answers,sourceVerification='not-verified',scope='单基金披露股票；单基金占组合100%，不是用户真实账户',nextSteps=['打开 report.html 查看已知与未知；换组合比例时需另组织组合输入','资料缺项先查原表；本向导没有自动取得真实持仓'])}
            for name,value in values.items():(stage/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
            (stage/'holdings.csv').write_bytes(a.csv.read_bytes())
            (stage/'report.md').write_text(markdown(result),encoding='utf-8');(stage/'report.html').write_text(html_report(result,spec),encoding='utf-8')
            if a.out_dir.exists():raise FileExistsError('输出已被创建，旧结果不覆盖')
            os.rename(stage,a.out_dir)
        print('声明口径已确认，报告已生成：'+str((a.out_dir/'report.html').resolve())+'。原始来源与完整性尚未核验。')
        return 0
    except (ValueError,TypeError,KeyError,OSError,EOFError) as e:
        print('未完成资料准备：'+str(e)+'\n下一步：核对持仓日期、公开日期、净资产百分数和显式交易所；未知项不补造。',file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
