"""Static declared-field preflight, without exposure traversal or source access."""
from .engine import weight, day
import math

def inspect(spec):
    errors=[];warnings=[]
    def issue(path,message):errors.append(dict(fieldPath=path,message=message))
    def valid_day(value,path):
        try:return day(value)
        except (ValueError,TypeError):issue(path,'须为YYYY-MM-DD');return None
    def valid_weight(value,path):
        try:return weight(value)
        except (ValueError,TypeError):issue(path,'须为0至1有限小数，不接受百分数文字或布尔值');return None
    if not isinstance(spec,dict):issue('$','输入须为对象');spec={}
    if spec.get('inputSchema') not in (None,'cnlookthrough-nodes-v1'):issue('inputSchema','仅支持cnlookthrough-nodes-v1')
    cutoff=valid_day(spec.get('asOf'),'asOf');currency=spec.get('currency')
    if not isinstance(currency,str) or len(currency)!=3 or not currency.isascii() or not currency.isalpha() or not currency.isupper():issue('currency','须为三字母大写币种')
    nodes=spec.get('nodes');roots=spec.get('positions');master=spec.get('securities',{})
    if not isinstance(nodes,dict) or len(nodes)>1000:issue('nodes','须为对象，最多1000个节点');nodes={}
    if not isinstance(master,dict):issue('securities','须为映射对象');master={}
    if not isinstance(roots,list) or not 1<=len(roots)<=100:issue('positions','须为1至100项列表');roots=[]
    ids=set();amounts=[]
    for i,row in enumerate(roots):
        path=f'positions[{i}]'
        if not isinstance(row,dict):issue(path,'须为对象');continue
        identity=row.get('id')
        if not isinstance(identity,str) or not identity.strip() or identity in ids:issue(path+'.id','须为唯一非空文字')
        else:ids.add(identity)
        value=valid_weight(row.get('weight'),path+'.weight')
        if value is not None:amounts.append(value)
        key=row.get('node')
        if not isinstance(key,str) or not key.strip():issue(path+'.node','须为非空节点标识')
        elif key not in nodes:warnings.append(dict(fieldPath=path+'.node',message='子基金资料缺失，运行时保留未知'))
    if roots and len(amounts)==len(roots) and abs(math.fsum(amounts)-1)>1e-9:issue('positions','权重须合计1，现金也应明确记录')
    for key,node in nodes.items():
        path=f'nodes[{key}]'
        if not isinstance(node,dict):issue(path,'须为对象');continue
        report=valid_day(node.get('reportDate'),path+'.reportDate');published=valid_day(node.get('publishedAt'),path+'.publishedAt')
        if report and published and (report>published or cutoff and published>cutoff):issue(path,'披露时间或报告期超出截止日')
        if node.get('currency')!=currency:issue(path+'.currency','须与根币种一致，不隐含换汇')
        if not isinstance(node.get('source'),str) or not node['source'].strip():issue(path+'.source','来源必填')
        if node.get('weightBasis') not in (None,'parent-net-assets') or node.get('renormalized') not in (None,False):issue(path+'.weightBasis','须按父节点净资产，不能将已知持仓重新归一')
        rows=node.get('holdings')
        if not isinstance(rows,list) or len(rows)>5000:issue(path+'.holdings','须为列表，最多5000项');continue
        values=[]
        for i,row in enumerate(rows):
            hp=path+f'.holdings[{i}]'
            if not isinstance(row,dict):issue(hp,'须为对象');continue
            w=valid_weight(row.get('weight'),hp+'.weight')
            if w is not None:values.append(w)
            kind=row.get('kind')
            if kind not in ('fund','stock','bond','cash','other'):issue(hp+'.kind','须为fund/stock/bond/cash/other')
            target=row.get('node' if kind=='fund' else 'security')
            if not isinstance(target,str) or not target.strip():issue(hp,'缺少对应node或security标识');continue
            if kind=='fund':
                if target not in nodes:warnings.append(dict(fieldPath=hp+'.node',message='子基金资料缺失，运行时保留未知'))
            elif target not in master:warnings.append(dict(fieldPath=hp+'.security',message='证券映射缺失，运行时保留未知'))
            elif isinstance(master[target],dict) and master[target].get('kind')!=kind:issue(hp+'.kind','与证券映射分类冲突')
        if math.fsum(values)>1+1e-9:issue(path+'.holdings','权重超过1，不能截断')
        elif math.fsum(values)<1:warnings.append(dict(fieldPath=path+'.holdings',message='未披露余额保留未知，不归一或填零'))
    for key,meta in master.items():
        path=f'securities[{key}]'
        if not isinstance(meta,dict):issue(path,'须为对象');continue
        if meta.get('kind') not in ('stock','bond','cash','other'):issue(path+'.kind','分类无效')
        if not isinstance(meta.get('source'),str) or not meta['source'].strip():issue(path+'.source','映射依据必填')
        if meta.get('kind')=='stock' and not isinstance(meta.get('issuer'),str):warnings.append(dict(fieldPath=path+'.issuer',message='无公司映射，证券金额不等于已认证公司敞口'))
    from .input_diagnostics import inspect_fields
    warnings.extend(inspect_fields(dict(spec,positions=roots,nodes=nodes,securities=master)))
    return dict(type='input-preflight',contract='cnlookthrough-nodes-v1',status='invalid' if errors else 'declared-fields-valid',errors=errors,warnings=warnings,networkAccess=False,filesWritten=False,originalVerified=False,calculationPerformed=False,limitations=['检查全部声明节点；不执行穿透、循环/深度/路径数量或守恒验收，运行仍可能受限','来源、身份及完整持仓未认证；限额不是已验证性能上限'])

CONTRACT={'contract':'cnlookthrough-nodes-v1','required':['asOf','currency','positions','nodes'],'positionRequired':['id','node','weight'],'nodeRequired':['currency','source','reportDate','publishedAt','holdings'],'holdingKinds':['fund','stock','bond','cash','other'],'weight':'0至1小数，按父节点净资产；不是百分数或已披露部分归一值','limits':{'rootPositions':100,'nodes':1000,'holdingsPerNode':5000},'scope':'静态契约索引，不是JSON Schema或穿透运行保证'}


def main():
    import sys
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,"reconfigure"):stream.reconfigure(encoding="utf-8")
    import argparse,json
    p=argparse.ArgumentParser(description='本地输入契约索引；不联网、不写文件')
    p.add_argument('--contract',action='store_true',required=True)
    p.parse_args()
    print(json.dumps(CONTRACT,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
