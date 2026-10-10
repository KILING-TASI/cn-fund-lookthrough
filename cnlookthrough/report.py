def markdown(r):
    known=r['knownExposure']*100;unknown=r['unknownExposure']*100
    text=f"# 基金持仓穿透\n\n本次能解释{known:.2f}%的组合权重，另有{unknown:.2f}%仍未知。买了多只基金，不代表底层风险已经分散。\n\n"
    if r.get('inputDiagnostics'):
        text+='## 输入需要核对的地方\n\n'
        for warning in r['inputDiagnostics']['warnings']:
            text+='- '+warning['fieldPath']+'：'+warning['message']+'\n'
        text+='\n'
    if r['unmappedStockIssuerExposure']>0:
        text+=f"另有{r['unmappedStockIssuerExposure']*100:.2f}%是有证券分类声明、但没有有效公司映射的股票敞口；证券身份或分类缺失则列入未知。金额权重能计算，不代表证券或公司身份已经认证。\n\n"
    effective=r['effectiveMappedEquityIssuers']
    if effective is not None:text+=f'已映射的股票部分，按公司集中度折算约{effective:.2f}个等权主体；不是整个组合的独立风险来源数。\n\n'
    text+='证券先逐项记录，再按有依据的公司身份汇总；不自动把AH股票或不同份额并成同一证券。\n\n## 已映射公司敞口\n\n'
    for name,value in sorted(r['issuerExposure'].items(),key=lambda x:-x[1]):text+=f'- {name}：占组合{value*100:.2f}%\n'
    text+='\n## 哪些持仓给了相同的公司暴露\n\n'
    for row in r['redundancy']:
        ratio=row['replicatedShare'];value='未取得可比较的公司映射' if ratio is None else f"已映射股票中，约{ratio*100:.2f}%能在其余持仓找到对应公司暴露"
        text+='- '+row['rootPosition']+'：'+value+'。这不等于没有配置作用。\n'
    text+='\n上述比例按每家公司本持仓与其余持仓的较小敞口配对，再除以本持仓已映射股票敞口。因此两个方向可能不同；这是已知部分的配对比例，不是完整基金持仓相似度。\n'
    text+='\n## 未知部分\n\n'
    for row in r['unknown']:text+=f"- {' → '.join(row['path'])}：{row['weight']*100:.2f}%，{row['reason']}\n"
    text+='\n报告期：'+', '.join(r['reportDates'])+'。不同披露时点不能当作同时持仓。\n\n'
    return text+'\n'.join('- '+x for x in r['limitations'])+'\n'


def html_report(r, spec=None):
    from html import escape
    import json,hashlib
    from pathlib import Path
    from .html_controls import table
    body=table(['已映射公司','占组合权重'],[[name,f'{value*100:.2f}%'] for name,value in sorted(r['issuerExposure'].items(),key=lambda x:-x[1])])
    files=['engine.py','input_diagnostics.py','report.py','html_controls.py','__main__.py']
    hashes={f:hashlib.sha256((Path(__file__).parent/f).read_bytes()).hexdigest() for f in files}
    frozen='<details><summary>保存的输入与方法摘要（分享前检查隐私）</summary><pre>'+escape(json.dumps({'input':spec,'methodSha256':hashes},ensure_ascii=False,indent=2,allow_nan=False))+'</pre></details>'
    teaching=bool(spec and spec.get('nodes')) and all(('教学' in n.get('source','') or '虚构' in n.get('source','')) for n in spec['nodes'].values())
    summary='<section aria-label="本次结论"><h1>基金持仓穿透</h1><p>已分类证券敞口 '+f"{r['knownExposure']*100:.2f}%"+'；未知部分 '+f"{r['unknownExposure']*100:.2f}%"+'。</p><h2>影响结论的关键缺口</h2><p>无公司映射的股票敞口 '+f"{r['unmappedStockIssuerExposure']*100:.2f}%"+'。已知仅限导入披露，不能代表当前完整持仓或真实风险分散。</p><p>各持仓报告期：'+escape(', '.join(r['reportDates']))+'；不同时点不能当作同时持仓。</p></section>'
    summary=summary.replace('<h1>','<p>'+('原创教学样本，非真实研究结论。' if teaching else '按输入声明观察；来源与完整性仍须核对。')+'</p><h1>',1)
    meta='截止日 '+str(r['asOf'])+'；方法 '+r['toolVersion']+' / '+r['inputSchema']+' / '+r['rulesVersion']
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>研究结果</title><style>body{max-width:1000px;margin:32px auto;padding:0 20px;font:17px/1.7 system-ui,sans-serif;color:#203047}pre{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:10px;text-align:left;overflow-wrap:anywhere}input,select{font:inherit;max-width:100%}</style><body><p>'+escape(meta)+'</p>'+summary+body+'<details><summary>完整说明、未知路径与核查提示</summary><pre>'+escape(markdown(r))+'</pre></details>'+frozen+'</body></html>'
