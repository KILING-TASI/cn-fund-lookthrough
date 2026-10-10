"""Additive declared-input diagnostics; never translate or infer identities."""
VERSION = 'declared-input-fields-1'
METADATA = {'metadata', 'extensions', 'notes'}
FIELDS = {
    'root': {'inputSchema', 'asOf', 'currency', 'positions', 'nodes', 'securities',
             'adapterVersion', 'conversionRulesVersion', 'teachingAccount', 'name', 'source'},
    'position': {'id', 'node', 'weight', 'name', 'source'},
    'node': {'currency', 'source', 'reportDate', 'publishedAt', 'holdings',
             'weightBasis', 'renormalized', 'disclosureScope', 'name'},
    'holding': {'kind', 'node', 'security', 'weight', 'name', 'source', 'locator'},
    'security': {'kind', 'issuer', 'source', 'name', 'issuerEvidence'},
}


def inspect_fields(spec):
    warnings = []

    def add(code, path, message):
        warnings.append(dict(code=code, fieldPath=path, message=message))

    def inspect(value, role, prefix):
        if not isinstance(value, dict):
            return
        for key, item in value.items():
            if key in {'name', 'issuer', 'id', 'node', 'security'} and isinstance(item, str) and len(item) > 512:
                add('long-display-text', prefix + str(key),
                    '身份或展示文字超过512字符；请核对是否误贴正文。仅告警，不截断、不改公司映射或金额。')
        for key in value:
            if key in FIELDS[role] or key in METADATA:
                continue
            path = prefix + str(key)
            if role == 'root' and key == 'issuerMap':
                add('unused-issuer-map', path,
                    'issuerMap未被读取；证券映射应放在securities，每项为kind、issuer（可为null）、source对象。请核对依据后自行修正，不会自动转换或补source。')
            else:
                add('unused-field', path,
                    '此字段未用于计算；请核对名称和所在层级。附加元数据仍保留兼容，可放在metadata或extensions中；不据此认定其内容有效。')

    inspect(spec, 'root', '')
    if 'securities' not in spec:
        add('securities-missing', 'securities',
            '未提供securities；证券身份或分类缺失的敞口保留未知。issuerMap和其他同义名称不会代替此字段，不猜交易所或公司。')
    for i, row in enumerate(spec['positions']):
        inspect(row, 'position', f'positions[{i}].')
    for key, node in spec['nodes'].items():
        inspect(node, 'node', f'nodes[{key}].')
        if isinstance(node, dict) and isinstance(node.get('holdings'), list):
            for i, row in enumerate(node['holdings']):
                inspect(row, 'holding', f'nodes[{key}].holdings[{i}].')
    for key, meta in spec.get('securities', {}).items():
        inspect(meta, 'security', f'securities[{key}].')
        if isinstance(meta, dict) and meta.get('issuer') is not None and not isinstance(meta['issuer'], str):
            add('invalid-issuer-type', f'securities[{key}].issuer',
                'issuer须为有依据的公司名称文字或null；当前类型未用于公司映射，证券金额仍按原输入计算。不会将对象、代码或数值猜成公司。')
    return warnings
