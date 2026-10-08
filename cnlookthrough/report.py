def markdown(r):
    known=r['knownExposure']*100;unknown=r['unknownExposure']*100
    text=f"# 基金持仓穿透\n\n本次能解释{known:.2f}%的组合权重，另有{unknown:.2f}%仍未知。买了多只基金，不代表底层风险已经分散。\n\n"
    effective=r['effectiveMappedEquityIssuers']
    if effective is not None:text+=f'已映射的股票部分，按公司集中度折算约{effective:.2f}个等权主体；不是整个组合的独立风险来源数。\n\n'
    text+='证券先逐项记录，再按有依据的公司身份汇总；不自动把AH股票或不同份额并成同一证券。\n\n## 已映射公司敞口\n\n'
    for name,value in sorted(r['issuerExposure'].items(),key=lambda x:-x[1]):text+=f'- {name}：占组合{value*100:.2f}%\n'
    text+='\n## 哪些持仓给了相同的公司暴露\n\n'
    for row in r['redundancy']:
        ratio=row['replicatedShare'];value='未取得可比较的公司映射' if ratio is None else f"已映射股票中，约{ratio*100:.2f}%能在其余持仓找到对应公司暴露"
        text+='- '+row['rootPosition']+'：'+value+'。这不等于没有配置作用。\n'
    text+='\n## 未知部分\n\n'
    for row in r['unknown']:text+=f"- {' → '.join(row['path'])}：{row['weight']*100:.2f}%，{row['reason']}\n"
    text+='\n报告期：'+', '.join(r['reportDates'])+'。不同披露时点不能当作同时持仓。\n\n'
    return text+'\n'.join('- '+x for x in r['limitations'])+'\n'
