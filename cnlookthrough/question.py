"""Bounded fund-overlap question and explicit allocation follow-up, offline."""
import argparse,copy,hashlib,json,math,os,tempfile
from pathlib import Path
from .__main__ import pairs
from .engine import analyze
from .preflight import inspect
from .report import markdown,html_report

def load(path):
    p=Path(path)
    if p.stat().st_size>16*1024*1024:raise ValueError('输入超过16MiB')
    raw=p.read_bytes()
    value=json.loads(raw.decode('utf-8-sig'),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('不能含非有限数值')))
    return value,hashlib.sha256(raw).hexdigest()

def allocations(values,count):
    if not isinstance(values,list) or len(values)!=count or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in values):raise ValueError('逐基金配置百分数须为正数，数量与基金一致')
    if abs(math.fsum(values)-100)>1e-8:raise ValueError('本入口需明确配置合计100%；不能替你填未声明余额或现金')
    return [v/100 for v in values]

def compose(inputs,weights,as_of):
    spec=dict(asOf=as_of,currency='CNY',positions=[],nodes={},securities={},metadata=dict(scope='用户明确选定的披露快照，非自动下载或真实账户认证'))
    for i,source in enumerate(inputs):
        check=inspect(source)
        if check['errors']:raise ValueError('第'+str(i+1)+'份声明输入无效：'+str(check['errors']))
        if source['currency']!='CNY' or len(source['positions'])!=1 or source['positions'][0]['weight']!=1:raise ValueError('每份输入须为单基金占100%的CNY研究快照；不静默重算来源组合')
        if source['asOf']!=as_of:raise ValueError('截止日必须相同；更新截止日请先明确组织新资料，不能悄悄修改')
        prefix='fund'+str(i)+':'
        root=copy.deepcopy(source['positions'][0]);root.update(id=prefix+root['id'],node=prefix+root['node'],weight=weights[i]);spec['positions'].append(root)
        for key,node in source['nodes'].items():
            node=copy.deepcopy(node)
            for row in node['holdings']:
                if row['kind']=='fund':row['node']=prefix+row['node']
            spec['nodes'][prefix+key]=node
        for security,meta in source.get('securities',{}).items():
            if security in spec['securities']:
                old=spec['securities'][security]
                if any(old.get(k)!=meta.get(k) for k in ('kind','issuer')):raise ValueError('同一证券存在分类或公司映射冲突：'+security+'；先核对原文，不能自动选值')
                if old.get('source')!=meta.get('source'):old['source']=old['source']+'；另一输入依据：'+meta['source']
            else:spec['securities'][security]=copy.deepcopy(meta)
    return spec

def publish(spec,out,request,source_inputs):
    import sys
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    out=Path(out)
    if out.exists():raise FileExistsError('结果目录已存在，改用新目录；旧报告不覆盖')
    check=inspect(spec)
    if check['errors']:raise ValueError('合并输入无效：'+str(check['errors']))
    result=analyze(spec)
    # These answer words reflect computed disclosed scope, not a future investment recommendation.
    comparable=any(row['replicatedShare'] is not None for row in result['redundancy'])
    shared=any(row['replicatedShare'] is not None and row['replicatedShare']>0 for row in result['redundancy'])
    conclusion='缺少可比较的公司映射，暂不能判断是否重合。' if not comparable else '已映射的股票公司敞口有重合。' if shared else '已映射部分尚未发现公司敞口重合。'
    answer=conclusion+f"本次已分类证券权重{result['knownExposure']:.2%}，另有{result['unknownExposure']:.2%}未知。"
    if result['unmappedStockIssuerExposure']>0:answer+=f"已分类股票中另有{result['unmappedStockIssuerExposure']:.2%}组合权重没有有效公司映射。"
    answer+='这不是完整基金相似度或未来风险结论。'
    result['questionAnswer']=dict(question='这些基金是否重复配置了同一批公司？',answer=answer,dataAcquisition='provided-inputs',calculationComplete=True,sourceVerification='not-verified',scope='同截止日的用户披露输入；报告期可能不同',nextSteps=['查看公司敞口与未知路径；日期不同不能当作同时真实持仓','换比例用 follow，复用选定快照并另存，不自动刷新资料'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.question-',dir=out.parent) as temp:
        stage=Path(temp)/'result';stage.mkdir()
        for name,data in [('input.json',spec),('source-inputs.json',source_inputs),('result.json',result),('research-request.json',request),('preflight.json',check)]:
            (stage/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
        (stage/'answer.md').write_text('# 基金重合问题\n\n'+answer+'\n\n'+markdown(result),encoding='utf-8')
        page=html_report(result,spec)
        from html import escape
        teaching=all('教学' in node.get('source','') or '虚构' in node.get('source','') for node in spec['nodes'].values())
        badge='原创教学输入，非真实研究结论。' if teaching else '基于用户提供的披露声明；原始来源尚未核验。'
        page=page.replace('<body>','<body><section style="padding:20px;max-width:1100px;margin:auto"><p>'+escape(badge)+'</p><h1>基金重合问题</h1><p>'+escape(answer)+'</p></section>',1)
        (stage/'report.html').write_text(page,encoding='utf-8')
        request_hash=hashlib.sha256((stage/'research-request.json').read_bytes()).hexdigest()
        receipt=dict(requestSha256=request_hash,files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir()},methodFiles={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('question.py','engine.py','report.py')},scope='内容完整性，不认证来源真实性')
        (stage/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
        if out.exists():raise FileExistsError('输出已创建，不覆盖')
        os.rename(stage,out)
    print(answer+'\n请打开：'+str((out/'report.html').resolve()))
    return result

def main(argv=None):
    import sys
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='按用户已提供的单基金输入回答重合问题；不联网，不冒充当前持仓')
    p.add_argument('command',choices=['compare','follow']);p.add_argument('--input',type=Path);p.add_argument('--continue-from',type=Path);p.add_argument('--weights',type=float,nargs='+');p.add_argument('--out-dir',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        if a.command=='compare':
            if not a.input or a.continue_from or a.weights:raise ValueError('compare 仅用 --input 声明基金输入清单')
            request,_=load(a.input)
            if not isinstance(request,dict) or set(request)!= {'asOf','funds'} or not isinstance(request['funds'],list) or not 2<=len(request['funds'])<=10:raise ValueError('需asOf及2至10份funds，每份声明input和allocationPercent')
            source_inputs=[];bindings=[];values=[]
            for row in request['funds']:
                if not isinstance(row,dict) or set(row)!= {'input','allocationPercent'} or not isinstance(row['input'],str):raise ValueError('每份funds需input路径和allocationPercent')
                path=(a.input.parent/row['input']).resolve();spec,digest=load(path);source_inputs.append(spec);bindings.append(dict(fileName=path.name,sha256=digest));values.append(row['allocationPercent'])
            weights=allocations(values,len(source_inputs));as_of=request['asOf']
            stored=dict(type='fund-overlap-question-v1',asOf=as_of,allocationPercent=values,sourceBindings=bindings,networkAccess=False)
        else:
            if not a.continue_from or not a.weights or a.input:raise ValueError('follow 需要 --continue-from 已选报告 与 --weights 明确新百分数')
            folder=a.continue_from;receipt,_=load(folder/'receipt.json')
            for name in ('research-request.json','source-inputs.json','input.json'):
                _,digest=load(folder/name)
                if receipt['files'].get(name)!=digest:raise ValueError('旧研究输入或请求已变化，不能静默复用：'+name)
            stored,_=load(folder/'research-request.json');source_inputs,_=load(folder/'source-inputs.json')
            changes=[name for name,digest in receipt.get('methodFiles',{}).items() if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest]
            weights=allocations(a.weights,len(source_inputs));as_of=stored['asOf'];stored=dict(stored,allocationPercent=a.weights,continuedFrom=str(folder.resolve()),methodChanges=changes,networkAccess=False)
            if changes:print('方法文件已有变化，将按当前代码重新计算：'+','.join(changes)+'；旧结果保留。',file=sys.stderr)
        spec=compose(source_inputs,weights,as_of)
        publish(spec,a.out_dir,stored,source_inputs);return 0
    except (ValueError,KeyError,TypeError,OSError) as e:
        print('未完成基金问答：'+str(e)+'\n下一步：补齐明确来源的单基金披露输入，核对相同截止日、百分数和证券映射；不会自动取数或覆盖旧报告。',file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
