import datetime as dt
import math
from collections import defaultdict


def weight(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:
        raise ValueError('权重须为0至1小数，不接受百分数文字')
    return float(value)


def day(value):
    if not isinstance(value,str) or dt.date.fromisoformat(value).isoformat()!=value:
        raise ValueError('日期须为YYYY-MM-DD')
    return dt.date.fromisoformat(value)


def analyze(spec):
    if not isinstance(spec,dict):raise ValueError('输入须为对象，证券映射字段为securities')
    if spec.get('inputSchema') not in (None,'cnlookthrough-nodes-v1'):raise ValueError('未知输入schema，须显式转换，不能静默按旧版解释')
    cutoff=day(spec['asOf']);nodes=spec['nodes'];roots=spec['positions'];master=spec.get('securities',{})
    if not isinstance(nodes,dict) or not isinstance(master,dict) or not isinstance(roots,list) or not roots:
        raise ValueError('需要持仓列表、节点和证券映射')
    from .input_diagnostics import inspect_fields,VERSION
    diagnostics=inspect_fields(spec)
    currency=spec.get('currency')
    if not isinstance(currency,str) or len(currency)!=3 or not currency.isascii() or not currency.isalpha() or not currency.isupper():raise ValueError('须明确三字母币种')
    if len(roots)>100 or len(nodes)>1000:raise ValueError('首版最多100项根持仓、1000个节点')
    total=math.fsum(weight(row['weight']) for row in roots)
    if abs(total-1)>1e-9:raise ValueError('根持仓权重须合计为1，现金也应明确记录')
    ids=[r['id'] for r in roots]
    if any(not isinstance(x,str) or not x.strip() for x in ids) or len(set(ids))!=len(ids):raise ValueError('根持仓标识须唯一')
    traces=[];unknown=[];periods=set();visits=0
    def gap(amount,path,root,reason):unknown.append(dict(weight=amount,path=path,rootPosition=root,reason=reason))
    def walk(key,amount,path,root):
        nonlocal visits
        visits+=1
        if visits>100000:raise ValueError('投资路径过多，需缩小输入范围')
        if amount==0:return
        if key in path:gap(amount,path+[key],root,'循环投资关系');return
        if len(path)>=20:gap(amount,path+[key],root,'穿透深度上限');return
        if key not in nodes:gap(amount,path+[key],root,'子基金资料缺失');return
        node=nodes[key]
        if node.get('weightBasis') not in (None,'parent-net-assets') or node.get('renormalized') not in (None,False):raise ValueError('持仓须基于父节点净资产，不接受按权益/已知持仓重新归一')
        report=day(node['reportDate']);published=day(node['publishedAt'])
        if report>published or published>cutoff:raise ValueError('披露时间或报告期超出截止日')
        if node.get('currency')!=currency:raise ValueError('节点币种不一致；不得隐含汇率换算')
        if not isinstance(node.get('source'),str) or not node['source'].strip():raise ValueError('节点来源缺失')
        holdings=node['holdings']
        if not isinstance(holdings,list) or len(holdings)>5000:raise ValueError('节点持仓列表无效')
        used=math.fsum(weight(row['weight']) for row in holdings)
        if used>1+1e-9:raise ValueError('首版不支持毛额超过100%的杠杆持仓，不能截断')
        periods.add(report.isoformat())
        branch=path+[key]
        for row in holdings:
            if row.get('kind') not in ('fund','stock','bond','cash','other'):raise ValueError('持仓类型无效')
            part=amount*weight(row['weight'])
            if row.get('kind')=='fund':walk(row['node'],part,branch,root)
            else:
                security=row['security']
                if security not in master:gap(part,branch+[security],root,'证券身份或分类缺失');continue
                meta=master[security]
                if not isinstance(meta,dict):raise ValueError('securities每项须为含kind、issuer（可为null）、source的对象')
                if meta.get('kind') not in ('stock','bond','cash','other'):raise ValueError('证券类型无效')
                if meta['kind']!=row['kind']:raise ValueError('持仓与证券映射分类冲突')
                if not isinstance(meta.get('source'),str) or not meta['source'].strip():raise ValueError('证券映射须注明依据')
                traces.append(dict(security=security,issuer=meta.get('issuer'),kind=meta['kind'],weight=part,
                    path=branch+[security],rootPosition=root,source=node['source'],reportDate=node['reportDate']))
        if used<1:gap(amount*(1-used),branch,root,'未披露或未解析余额')
    for row in roots:walk(row['node'],weight(row['weight']),[],row['id'])
    security_totals=defaultdict(float);issuer_totals=defaultdict(float);by_root=defaultdict(lambda:defaultdict(float))
    missing_issuer=0.
    for trace in traces:
        security_totals[trace['security']]+=trace['weight']
        if trace['kind']=='stock':
            if isinstance(trace['issuer'],str) and trace['issuer'].strip():
                issuer_totals[trace['issuer']]+=trace['weight'];by_root[trace['rootPosition']][trace['issuer']]+=trace['weight']
            else:missing_issuer+=trace['weight']
    known=math.fsum(t['weight'] for t in traces);unresolved=math.fsum(t['weight'] for t in unknown)
    if abs(known+unresolved-1)>1e-8:raise ValueError('穿透权重不守恒')
    stock_known=math.fsum(issuer_totals.values())
    effective=1/math.fsum((v/stock_known)**2 for v in issuer_totals.values()) if stock_known else None
    redundancy=[]
    for root in ids:
        own=by_root[root];denom=math.fsum(own.values())
        replicated=math.fsum(min(v,math.fsum(by_root[r].get(key,0) for r in ids if r!=root)) for key,v in own.items())
        unique=math.fsum(v for key,v in own.items() if not any(by_root[r].get(key,0)>0 for r in ids if r!=root))
        redundancy.append(dict(rootPosition=root,mappedEquityExposure=denom,
            replicatedShare=replicated/denom if denom else None,uniqueIssuerShare=unique/denom if denom else None))
    result=dict(toolVersion='cn-fund-lookthrough-0.2.0',inputSchema='cnlookthrough-nodes-v1',rulesVersion='disclosed-paths-2',asOf=spec['asOf'],currency=currency,securityExposure=dict(security_totals),issuerExposure=dict(issuer_totals),
        knownExposure=known,unknownExposure=unresolved,unmappedStockIssuerExposure=missing_issuer,
        effectiveMappedEquityIssuers=effective,reportDates=sorted(periods),paths=traces,unknown=unknown,redundancy=redundancy,
        limitations=['仅已披露输入快照，不代表当前真实完整持仓','证券与发行人层分别汇总；AH或不同份额不会自动并成同证券',
                    '冗余与独有贡献仅描述已映射股票证券结构，不说明边际风险或是否该卖',
                    '不同报告期的嵌套权重可能不同时点；覆盖率不是准确率'])
    if diagnostics:result['inputDiagnostics']=dict(version=VERSION,warnings=diagnostics)
    return result
