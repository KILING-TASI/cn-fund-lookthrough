# SPDX-License-Identifier: MIT
from .review_io import cli,day,number
from .report_adapter import compare_snapshots
def compare(spec):
    a,b=spec['before'],spec['after']
    cutoff=day(spec['asOf'])
    for d in (a,b):
        if d.get('disclosureScope')!='completeEquity' or d.get('portfolioScope')!='fund-all-share-classes':raise ValueError('需要已核对完整股票表与全部份额净资产分母')
        if d.get('renormalized') not in (None,False) or d.get('weightBasis') not in (None,'parent-net-assets'):raise ValueError('不接受重新归一或股票资产分母')
        for k in ('id','adapterProfile','currency','sourceSha256','publishedAt','reportDate'):
            if not d.get(k):raise ValueError('跨期资料缺字段：'+k)
        keys=[r['securityNamespace']+':'+r['code'] for r in d['holdings']]
        if len(keys)!=len(set(keys)):raise ValueError('证券重复，不能覆盖')
        if day(d['publishedAt'])>cutoff or day(d['publishedAt'])<day(d['reportDate']):raise ValueError('披露晚于截止或早于报告期')
        sha=d['sourceSha256']
        if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('来源摘要无效')
        if any(not 0<=number(r['weight'])<=1 for r in d['holdings']):raise ValueError('持仓权重范围无效')
        if sum((number(r['weight']) for r in d['holdings']))>1:raise ValueError('已披露股票权重超过净资产；需另核口径')
    result=compare_snapshots(a,b)
    result['conclusion']='只看两次完整股票披露的变化；新增、消失或权重变化不直接等于实际买卖。'
    result['humanRows']=[[r['security'],r['status']+'；权重变化'+str(r['weightChange'])] for r in result['rows']]
    result['limitations']=[result['limitation'],'口径、报告身份和来源版本依赖输入底稿；不替代原文核验','两份持仓无法唯一分解价格、交易及申赎归因，非股票部分仍未知']
    return result
if __name__=='__main__':raise SystemExit(cli({'compare':compare},'基金跨期披露比较'))
