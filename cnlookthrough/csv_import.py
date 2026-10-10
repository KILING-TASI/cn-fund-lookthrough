"""Explicit user-exported stock holdings format; no source discovery or inference."""
import argparse,csv,hashlib,io,json,re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .preflight import inspect

FORMAT='user-stock-holdings-csv-v1'
COLUMNS=['security','weightPercent','issuer','identitySource']

def convert(raw,config):
    if not isinstance(config,dict) or config.get('format')!=FORMAT:raise ValueError('format须为'+FORMAT+'；不自动识别交易所PCF、PDF或其他CSV格式')
    if len(raw)>16*1024*1024:raise ValueError('CSV超过16MB')
    for key in ['asOf','currency','positionId','nodeId','source','reportDate','publishedAt','weightBasis','disclosureScope']:
        if not isinstance(config.get(key),str) or not config[key].strip():raise ValueError('导入配置必填：'+key)
    if config['weightBasis']!='parent-net-assets':raise ValueError('weightBasis须为parent-net-assets，不能把股票部分或前十大持仓归一成100%')
    if config['disclosureScope'] not in ['top-holdings','declared-full']:raise ValueError('disclosureScope须为top-holdings或declared-full；声明不等于完整性核验')
    if config['currency']!='CNY':raise ValueError('此版本只接受显式CNY口径，不换汇')
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''),strict=True)
    if reader.fieldnames!=COLUMNS:raise ValueError('CSV列及顺序须为'+','.join(COLUMNS)+'；未知列不静默丢弃')
    holdings=[];master={};original=[];seen=set();total=Decimal(0)
    for row in reader:
        if len(holdings)>=5000:raise ValueError('最多5000行持仓')
        if None in row or any(v is None for v in row.values()):raise ValueError('CSV行字段数量不匹配')
        security=row['security']
        if not re.fullmatch(r'CN-(SSE|SZSE|BSE):[0-9]{6}',security):raise ValueError('security须为显式CN-SSE:/CN-SZSE:/CN-BSE:加六位代码；不猜交易所')
        if security in seen:raise ValueError('重复证券行须先核对，不自动合并：'+security)
        seen.add(security)
        try:percent=Decimal(row['weightPercent'])
        except InvalidOperation as e:raise ValueError('weightPercent须为数字百分数，例如3.18，不带%') from e
        if not percent.is_finite() or not 0<=percent<=100:raise ValueError('weightPercent须为0至100有限数字')
        total+=percent
        if total>100:raise ValueError('持仓合计超过100%，不截断或归一')
        if row['issuer'].strip() and not row['identitySource'].strip():raise ValueError('声明公司映射须提供identitySource；未知公司保留空白')
        holdings.append(dict(kind='stock',security=security,weight=float(percent/100)))
        if row['identitySource'].strip():master[security]=dict(kind='stock',issuer=row['issuer'].strip() or None,source=row['identitySource'])
        original.append(dict(csvLine=reader.line_num,values=dict(row)))
    if not holdings:raise ValueError('CSV无持仓行')
    node=config['nodeId']
    spec=dict(inputSchema='cnlookthrough-nodes-v1',asOf=config['asOf'],currency='CNY',positions=[dict(id=config['positionId'],node=node,weight=1)],
        nodes={node:dict(currency='CNY',source=config['source'],reportDate=config['reportDate'],publishedAt=config['publishedAt'],weightBasis='parent-net-assets',renormalized=False,disclosureScope=config['disclosureScope'],holdings=holdings)},securities=master,
        metadata=dict(importFormat=FORMAT,conversionRulesVersion='percent-to-parent-weight-1',inputCsvSha256=hashlib.sha256(raw).hexdigest(),config=dict(config),originalRows=original,sourceVerified=False))
    check=inspect(spec)
    if check['errors']:raise ValueError('转换后声明字段无效：'+json.dumps(check['errors'],ensure_ascii=False))
    return spec

def main():
    from .__main__ import pairs
    p=argparse.ArgumentParser(description='本地股票持仓CSV导入；不联网、不猜身份、不归一权重')
    p.add_argument('input',type=Path);p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path)
    p.add_argument('--validate-only','--dry-run',action='store_true',help='只检查转换契约，不写输出；不进行穿透计算')
    a=p.parse_args()
    try:
        if a.input.stat().st_size>16*1024*1024 or a.config.stat().st_size>1024*1024:raise ValueError('CSV或配置过大')
        if a.validate_only and a.out:raise ValueError('预检不接受--out；不会写文件')
        config=json.loads(a.config.read_text('utf-8-sig'),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('非有限JSON数值')))
        spec=convert(a.input.read_bytes(),config)
        value=inspect(spec) if a.validate_only else spec
        text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)
        if a.out:
            a.out.parent.mkdir(parents=True,exist_ok=True)
            with a.out.open('x',encoding='utf-8') as f:f.write(text+'\n')
        else:print(text)
    except (ValueError,KeyError,TypeError,OSError,ArithmeticError,UnicodeError,csv.Error) as e:p.exit(2,'未能导入：'+str(e)+'；未覆盖旧输出。\n')

if __name__=='__main__':main()
