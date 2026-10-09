"""Explicit source-bound identity for one disclosed snapshot, not historical master data."""
import copy
import datetime as dt
import hashlib
from pathlib import Path
from urllib.parse import urlparse


def apply_snapshot_mappings(spec, mapping):
    if mapping.get('inputSchema') != 'issuer-snapshot-map-v1':
        raise ValueError('未知发行人快照映射schema')
    if mapping.get('methodVersion') != 'source-bound-snapshot-1':
        raise ValueError('未知发行人快照映射方法')
    result = copy.deepcopy(spec)
    cutoff = dt.date.fromisoformat(spec['asOf'])
    decisions = []
    seen = set()
    for row in mapping['mappings']:
        security = row['security']
        if security in seen or security not in spec['securities']:
            raise ValueError('映射证券重复或不在披露集合中')
        seen.add(security)
        if spec['securities'][security].get('kind') != 'stock' or not isinstance(row.get('issuerName'), str) or not row['issuerName'].strip():
            raise ValueError('只映射有明确发行人名称的股票')
        start, end = dt.date.fromisoformat(row['validFrom']), dt.date.fromisoformat(row['validUntil'])
        if row.get('basis') != 'snapshot-identity-only' or start != end:
            raise ValueError('首版只认证明确的单日披露快照，不外推身份历史区间')
        periods = [dt.date.fromisoformat(node['reportDate']) for node in spec['nodes'].values()
                   if any(h.get('security') == security for h in node['holdings'])]
        status = 'not-applied-period-or-publication-gap'
        if periods and all(day == start for day in periods) and dt.date.fromisoformat(row['publishedAt']) <= cutoff:
            if urlparse(row['source']).scheme != 'https':
                raise ValueError('发行人依据须保留HTTPS来源')
            evidence = row['evidence'];quote = evidence['quote']
            if row['code'] not in quote or row['issuerName'] not in quote or security != 'CN-equity:' + row['code']:
                raise ValueError('证券代码/发行人名称未绑定原文短引句')
            status = 'not-applied-original-not-verified'
            if evidence.get('pdfPath'):
                import pdfplumber
                path = Path(evidence['pdfPath'])
                if not path.is_file() or path.stat().st_size > 64 * 1024 * 1024 or hashlib.sha256(path.read_bytes()).hexdigest() != evidence['documentSha256']:
                    raise ValueError('发行人原文摘要或文件不一致')
                page = evidence['page']
                if isinstance(page, bool) or not isinstance(page, int) or page < 1:
                    raise ValueError('页码无效')
                with pdfplumber.open(path) as doc:
                    if page > len(doc.pages) or ''.join(quote.split()) not in ''.join((doc.pages[page-1].extract_text() or '').split()):
                        raise ValueError('发行人短引句未在绑定原页找到')
                preserved = {k:v for k,v in row.items() if k!='evidence'}
                preserved['evidence'] = {k:v for k,v in evidence.items() if k!='pdfPath'}
                result['securities'][security].update(issuer=row['issuerName'], issuerEvidence=preserved)
                status = 'applied-source-bound-snapshot'
        decisions.append(dict(security=security, status=status, validFrom=row['validFrom'], validUntil=row['validUntil'],
                              source=row.get('source'), evidence={k:v for k,v in row.get('evidence', {}).items() if k!='pdfPath'}))
    return dict(input=result, mappingDecisions=decisions, methodVersion='source-bound-snapshot-1',
                limitations=['仅选定证券与单日报告快照；其他发行人未知', '不还原更名、重组、A/H全历史或法律发行人有效期间',
                             '无本地原文不把声明升级为已核映射；不输出全组合有效发行人数'])
