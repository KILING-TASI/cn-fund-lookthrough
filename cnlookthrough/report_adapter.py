# Copyright (c) 2026 research-workbench contributors
# SPDX-License-Identifier: MIT
# Derived from research-workbench a00ace5/scripts/fund_report_holdings.py; see THIRD_PARTY_NOTICES.md.
"""Bounded Ruiyuan complete-equity adapter, derived from the author's MIT research-workbench parser.
No source PDF is bundled. Six-column annual/interim tables only, explicit NAV denominator.
"""
import datetime,hashlib,re
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse
def clean(s): return re.sub(r'\s+','',s or '')
def number(s):
    value=Decimal(clean(s).replace(',',''))
    if not value.is_finite():raise ValueError('原文金额或数量为非有限值')
    return value

def issuer_order_values(groups,values,declared,hk_scope):
    """Validate the explicitly disclosed A/H ranking convention, not issuer identity."""
    result=[];i=0
    while i<len(groups):
        group=groups[i]
        if declared and hk_scope and len(group)==1 and i+1<len(groups) and len(groups[i+1])==1:
            a,b=group[0],groups[i+1][0]
            if a['cells'][2]==b['cells'][2] and sorted([len(a['cells'][1]),len(b['cells'][1])])==[5,6]:
                if i+2<len(groups) and any(x['cells'][2]==a['cells'][2] for x in groups[i+2]):raise ValueError('A/H排序组超过明确双行，需复核')
                pair=[a['cells'][1],b['cells'][1]]
                a['issuerOrderPairCodes']=pair;b['issuerOrderPairCodes']=pair
                result.append(values[i]+values[i+1]);i+=2;continue
        result.append(values[i]);i+=1
    return result

def domestic_rows(doc):
    rows=[];started=False;finished=False;segment='indexInvestment';sequences={}
    hk_scope=any(re.search(r'(?m)^[78]\.2\.[23]\s*报告期末按行业分类的港股通投资股票投资组合\s*$',p.extract_text() or '') for p in doc.pages)
    issuer_order_declared=any('对于同时在A+H股上市的股票，合并计算公允价值参与排序，并按照不同股票分别披露。' in clean(p.extract_text() or '') for p in doc.pages)
    for page_no,page in enumerate(doc.pages,1):
        text=page.extract_text() or '';normalized=clean(text)
        if re.search(r'^(?:[78]\.3(?:\.[12])?\s*)?(?:报告)?期末按[^\n]*所有股票投资明细\s*$',text,re.M):
            started=True
            segment='indexInvestment' if '指数投资' in normalized else 'allEquity'
        if not started or finished:continue
        ends=page.search(r'(?m)^(?:[78]\.4\s*)?报告期内股票投资组合的重大变动\s*$')
        end_top=ends[0]['top'] if ends else float('inf')
        for table in page.find_tables():
            if table.bbox[1]>=end_top:continue
            for row_position,cells in enumerate(table.extract(),1):
                c=[clean(x) for x in cells if clean(x)]
                reported_code=c[1] if len(c)>1 else None
                if hk_scope and len(c)==6 and re.fullmatch(r'H\d{5}',c[1]):c[1]=c[1][1:]
                if len(c)!=6 or not c[0].isdigit() or not (re.fullmatch(r'\d{6}',c[1]) or hk_scope and re.fullmatch(r'\d{5}',c[1])):continue
                rank=int(c[0])
                if rank==1 and rows and rows[-1]["rank"]!=1:
                    if segment!='indexInvestment' or 'activeInvestment' in sequences:raise ValueError('出现未知排名重置，不能合并股票表')
                    segment='activeInvestment'
                sequences.setdefault(segment,[]).append(rank)
                rows.append({'rank':rank,'segment':segment,'cells':c,'reportedCode':reported_code,'pages':[page_no],'tableBBox':list(table.bbox),'tableRowIndex':row_position})
        if ends and rows:finished=True
    if not started or not finished or not rows:raise ValueError('未找到完整7.3股票表至7.4边界')
    for segment,ranks in sequences.items():
        # Some reports use dense ranks for exactly equal fair values.
        section=[r for r in rows if r['segment']==segment]
        if ranks[0]!=1:raise ValueError(segment+'未从1开始')
        groups=[]
        for row in section:
            if not groups or groups[-1][0]['rank']!=row['rank']:groups.append([row])
            else:groups[-1].append(row)
        ranked_values=[]
        for group in groups:
            amounts=[number(x['cells'][4]) for x in group]
            if len(set(amounts))>1:
                if not hk_scope or len(group)!=2 or sorted(len(x['cells'][1]) for x in group)!=[5,6]:raise ValueError(segment+'非等值共享序号缺少明确境内/港股双行结构')
                ranked_values.append(sum(amounts,Decimal(0)))
            else:ranked_values.append(amounts[0])
        for before,after in zip(groups,groups[1:]):
            delta=after[0]['rank']-before[0]['rank']
            competition_tie=len(before)>1 and len({number(x['cells'][4]) for x in before})==1 and delta==len(before)
            if delta!=1 and not competition_tie:raise ValueError(segment+'股票序号缺失或逆序')
        ordered_values=issuer_order_values(groups,ranked_values,issuer_order_declared,hk_scope)
        if any(b>a for a,b in zip(ordered_values,ordered_values[1:])):raise ValueError(segment+'权益公允价值排序逆序')
    if 'indexInvestment' in sequences and 'activeInvestment' not in sequences:raise ValueError('指数/积极双表未完整取得')
    return rows,sequences

def domestic_result(doc,raw,code,report_date,published_at,source_url,net_assets,equity_value):
    rows,sequences=domestic_rows(doc);total=sum((number(r['cells'][4]) for r in rows),Decimal(0))
    if total!=equity_value:raise ValueError(f'权益市值合计不一致：{total} vs {equity_value}')
    merged={};segments={}
    for r in rows:
        c=r['cells'];mv=number(c[4]);weight=mv/net_assets;shown=number(c[5]);qty=number(c[3])
        if mv<0 or qty<0 or qty!=qty.to_integral_value():raise ValueError('市值/股数不合法')
        if abs(weight*100-shown)>Decimal('.00501'):raise ValueError(c[1]+'权重与金额分母不匹配')
        segments[r['segment']]=segments.get(r['segment'],Decimal(0))+mv
        component={'reportedCode':r.get('reportedCode',c[1]),'segment':r['segment'],'rank':r['rank'],'quantity':int(qty),'marketValueCNY':float(mv),'reportedWeightPct':float(shown),'locator':'PDF页'+str(r['pages'][0]),'tableBBox':r['tableBBox'],'tableRowIndex':r['tableRowIndex'],'rawCells':c}
        if r.get('issuerOrderPairCodes'):component['issuerOrderPairCodes']=r['issuerOrderPairCodes'];component['rankingBasis']='报告明示A/H合并公允价值排序，证券仍分列；非全市场发行人身份认证'
        if c[1] not in merged:merged[c[1]]={'code':c[1],'name':c[2],'market':'HK-exchange-unresolved' if len(c[1])==5 else 'CN-exchange-unresolved','securityNamespace':'HK-equity' if len(c[1])==5 else 'CN-equity','shareClass':'ordinary','industry':'','components':[],'amount':Decimal(0),'quantity':0}
        h=merged[c[1]]
        if h['name']!=c[2]:raise ValueError('同代码跨表名称冲突')
        if any(x['segment']==r['segment'] for x in h['components']):raise ValueError('同表股票代码重复')
        h['components'].append(component);h['amount']+=mv;h['quantity']+=int(qty)
    holdings=[]
    for h in merged.values():
        amount=h.pop('amount');h.update({'weight':float(amount/net_assets),'marketValueCNY':float(amount),'locator':'；'.join(x['locator'] for x in h['components'])});holdings.append(h)
    holdings.sort(key=lambda h:-h['weight'])
    rank_ties=[{'segment':x['segment'],'rank':x['rank'],'codes':[p['cells'][1],x['cells'][1]],'marketValueCNY':float(number(x['cells'][4])) if number(p['cells'][4])==number(x['cells'][4]) else None,'valuesCNY':[float(number(p['cells'][4])),float(number(x['cells'][4]))],'basis':'equal-values' if number(p['cells'][4])==number(x['cells'][4]) else 'reported-shared-rank-distinct-securities','locator':'PDF页'+str(x['pages'][0])} for p,x in zip(rows,rows[1:]) if p['segment']==x['segment'] and p['rank']==x['rank']]
    return {'id':code,'allocation':1,'currency':'CNY','reportDate':report_date,'publishedAt':published_at,'sourceUrl':source_url,'locator':'中报§7.3/年报§8.3全部股票表；金额为人民币','disclosureScope':'completeEquity','equityWeight':float(equity_value/net_assets),'netAssetsCNY':float(net_assets),'equityMarketValueCNY':float(equity_value),'holdings':holdings,'rawRowCount':len(rows),'segments':{k:{'rows':len(sequences[k]),'marketValueCNY':float(v)} for k,v in segments.items()},'rankTies':rank_ties,'portfolioScope':'fund-all-share-classes','sourceSha256':hashlib.sha256(raw).hexdigest(),'parserVersion':'complete-equity-9','verification':'逐行权重、各表序号、跨表合并与总市值逐分勾稽通过；报告身份/日期/分母仍需原文核验','limitations':['持仓分母为基金全部份额合计净资产，不是某份额类净资产','市场命名空间依据原文股票代码及明确港股通章节区分；具体交易所尚未核验，不猜板块','非股票资产未穿透；不是实时持仓或交易流水','行业未分类，不输出行业集中度结论']}

def parse_ruiyuan(pdf,report_date,published_at,source_url,net_assets,equity_value):
    import pdfplumber
    if datetime.date.fromisoformat(report_date)>datetime.date.fromisoformat(published_at):raise ValueError('披露早于报告期')
    if report_date[5:] not in ('06-30','12-31'):raise ValueError('仅支持半年报/年报，不处理季报十大')
    parsed=urlparse(source_url)
    if parsed.scheme!='https' or parsed.hostname not in ('www.foresightfund.com','foresightfund.com'):raise ValueError('限定管理人来源，不隐含支持其他版式')
    nav,equity=number(str(net_assets)),number(str(equity_value))
    if nav<=0 or equity<0 or equity>nav:raise ValueError('NAV/权益金额或分母不合法')
    if not Path(pdf).is_file() or Path(pdf).stat().st_size>64*1024*1024:raise ValueError('PDF缺失或过大')
    raw=Path(pdf).read_bytes()
    if len(raw)>64*1024*1024:raise ValueError('PDF过大')
    with pdfplumber.open(pdf) as doc:
        header=clean(''.join(page.extract_text() or '' for page in doc.pages[:3]))
        if '睿远成长价值混合型证券投资基金' not in header or not ('中期报告' in header or '年度报告' in header):raise ValueError('非限定产品或报告类型')
        alltext=clean(''.join(page.extract_text() or '' for page in doc.pages))
        if '007119' not in alltext:raise ValueError('基金代码未找到')
        date=datetime.date.fromisoformat(report_date)
        if not re.search(rf'{date.year}年0?{date.month}月0?{date.day}日',alltext):raise ValueError('声明报告日未在原件找到')
        result=domestic_result(doc,raw,'007119',report_date,published_at,source_url,nav,equity)
    result['adapterProfile']='ruiyuan-growth-six-column-v1'
    result.update(toolVersion='cnlookthrough-report-0.1.dev1',inputSchema='explicit-report-totals-v1',rulesVersion='six-column-equity-1')
    result['sourceVerification']='local-report-identity-and-amount-check; not-live-source-authentication'
    return result


def parse_chinaamc_growth(pdf,report_date,published_at,source_url,net_assets,equity_value):
    """One additionally verified manager/report profile; no universal parser promise."""
    import pdfplumber
    if report_date != '2025-12-31' or published_at != '2026-03-31':
        raise ValueError('本轮华夏成长仅验收2025年年报，其他期需另核版式')
    if urlparse(source_url).scheme != 'https' or urlparse(source_url).hostname not in ('www.chinaamc.com.cn', 'www.chinaamc.com'):
        raise ValueError('限定华夏管理人公开来源')
    path = Path(pdf)
    if not path.is_file() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('本地PDF缺失或过大')
    raw = path.read_bytes();nav = number(str(net_assets));equity = number(str(equity_value))
    if nav <= 0 or equity < 0 or equity > nav:
        raise ValueError('分母或权益金额无效')
    with pdfplumber.open(path) as doc:
        header = clean(''.join(page.extract_text() or '' for page in doc.pages[:5]))
        if any(value not in header for value in ('华夏成长证券投资基金', '华夏基金管理有限公司', '2025年年度报告', '000001', '2025年12月31日')):
            raise ValueError('限定报告身份、期间或基金代码未匹配')
        selectors = [(5, 3, 10, 2, '期末基金资产净值', nav), (46, 4, 2, 3, '权益投资', equity)]
        denominator_evidence = []
        for page_no, table_no, row_no, column_no, label, expected in selectors:
            tables = doc.pages[page_no-1].find_tables()
            if len(tables) < table_no:
                raise ValueError('已验收表格位置不再匹配')
            table = tables[table_no-1];rows = table.extract()
            if len(rows) < row_no or len(rows[row_no-1]) < column_no:
                raise ValueError('金额位置缺失')
            row = rows[row_no-1]
            if label not in [clean(x) for x in row] or number(row[column_no-1]) != expected:
                raise ValueError('原文分母/权益金额与输入不同')
            if page_no == 5 and not any('2025年' in clean(x) for row_header in rows[:3] for x in row_header):
                raise ValueError('净资产比较年度表头不匹配')
            denominator_evidence.append(dict(page=page_no, tableIndex=table_no, rowIndex=row_no,
                                             columnIndex=column_no, label=label, rawCells=row, rawHeader=rows[:3], tableBBox=list(table.bbox)))
        result = domestic_result(doc, raw, '000001', report_date, published_at, source_url, nav, equity)
    result.update(adapterProfile='chinaamc-growth-2025-six-column-v1',
                  toolVersion='cnlookthrough-report-0.2.dev1', inputSchema='explicit-report-totals-v1',
                  rulesVersion='six-column-equity-and-explicit-denominator-2', denominatorEvidence=denominator_evidence,
                  sourceVerification='local-report-identity-and-selected-total-cells; not-live-authentication')
    return result

def to_spec(parsed,as_of):
    """One disclosed fund snapshot, not a customer account or issuer mapping."""
    if parsed.get('adapterProfile') not in ('ruiyuan-growth-six-column-v1','chinaamc-growth-2025-six-column-v1') or parsed.get('disclosureScope')!='completeEquity':raise ValueError('需先完成限定完整股票表适配')
    if parsed.get('portfolioScope')!='fund-all-share-classes':raise ValueError('限定转换须为基金全部份额合计口径，不接受单份额类或缺失范围')
    if parsed.get('weightBasis') not in (None,'parent-net-assets') or parsed.get('renormalized') not in (None,False):raise ValueError('限定转换须使用基金净资产分母，不接受权益分母或重新归一')
    if datetime.date.fromisoformat(parsed['publishedAt'])>datetime.date.fromisoformat(as_of):raise ValueError('披露晚于截止日')
    key='fund:'+parsed['id']+':'+parsed['reportDate'];holdings=[];securities={}
    for row in parsed['holdings']:
        security=row['securityNamespace']+':'+row['code'];holdings.append({'kind':'stock','security':security,'weight':row['weight']})
        securities[security]={'kind':'stock','issuer':None,'source':parsed['sourceUrl']+' # '+row['locator']}
    return {'inputSchema':'cnlookthrough-nodes-v1','conversionRulesVersion':'complete-equity-all-classes-nav-2','adapterVersion':parsed.get('toolVersion','cnlookthrough-report-0.1.dev1'),'asOf':as_of,'currency':'CNY','positions':[{'id':'disclosed-fund','node':key,'weight':1}],
            'nodes':{key:{'currency':'CNY','source':parsed['sourceUrl']+' sha256='+parsed['sourceSha256'],'reportDate':parsed['reportDate'],'publishedAt':parsed['publishedAt'],'holdings':holdings}},'securities':securities}

def compare_snapshots(before,after):
    for key in ('id','currency','adapterProfile','disclosureScope','portfolioScope'):
        if before.get(key)!=after.get(key):raise ValueError('跨期口径不同：'+key)
    if before['reportDate']>=after['reportDate']:raise ValueError('报告期须按先后排序')
    index=lambda doc:{row['securityNamespace']+':'+row['code']:row for row in doc['holdings']}
    a,b=index(before),index(after)
    rows=[{'security':key,'beforeWeight':a[key]['weight'] if key in a else None,'afterWeight':b[key]['weight'] if key in b else None,
           'weightChange':b[key]['weight']-a[key]['weight'] if key in a and key in b else None,
           'status':'both-disclosed' if key in a and key in b else 'newly-disclosed' if key in b else 'no-longer-disclosed'} for key in sorted(set(a)|set(b))]
    return {'toolVersion':'cnlookthrough-report-0.1.dev1','inputSchema':'two-disclosed-snapshots-v1','rulesVersion':'same-scope-snapshot-diff-1','beforeReportDate':before['reportDate'],'afterReportDate':after['reportDate'],'rows':rows,
            'beforeSourceSha256':before['sourceSha256'],'afterSourceSha256':after['sourceSha256'],
            'limitation':'仅披露快照变化；新增/消失不等于实际买卖，非股票部分保留未知'}


def legacy_domestic_rows(doc):
    rows,sequences=domestic_rows(doc)
    for row in rows:
        row.pop('tableBBox',None);row.pop('tableRowIndex',None)
    return rows,sequences


def legacy_domestic_result(doc,raw,code,report_date,published_at,source_url,net_assets,equity_value):
    result=domestic_result(doc,raw,code,report_date,published_at,source_url,net_assets,equity_value)
    for holding in result['holdings']:
        for component in holding['components']:
            for key in ('tableBBox','tableRowIndex','rawCells'):component.pop(key,None)
    return result
