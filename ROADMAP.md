# 真实持仓适配路线与转换契约

更新日期：2026-10-09。开发版0.2.0.dev1，尚未发布。

已有：显式JSON节点穿透、证券/发行人分层、未知守恒与浓度度量。首批新增：睿远成长价值(007119)管理人可解析年报/中报六列完整股票表；只对已验证版式提供本地PDF适配，不下载、不接实时持仓，不把季报十大当完整表。

## 原文→独立引擎
保留基金全部份额净资产分母、股票金额合计、连续序号、证券原始代码/命名空间、原文页和表格位置。每行金额/分母核对披露权重，金额与权益合计逐分勾稽。非股票部分保留未知，不把股票重新归一为100%。AH保留两个证券，无证据不合并发行人。

转换输出按nodes/holdings/securities契约填写，节点source绑定URL+SHA256+物理页；securities先只声明证券类型，issuer未核时留空。根positions由使用者明确权重，单基金适配示例只用于该报告快照，不暗示个人账户。

跨期：比较同一产品、同口径NAV和证券命名空间的两快照，输出新增、消失及权重差；不将消失判卖出，披露期内交易无法还原。口径更换、缺表或缺期不输出完整变化结论。

## 首批验收
真实2025年报与2026中报，原文页、行数、金额合计、未知守恒；错管理人、十大表、断号、金额/权重冲突、未知证券映射拒绝或显式列缺口。真实原件仅用于本地验收，不随开源包分发。

后续：第二管理人独立版式、FOF基金投资表及更强页坐标；不承诺任意PDF、全量数据或发行人自动识别。


首批本地验收记录见[限定真实样本](validation/limited-real-samples.json)，数值与版式验证不等于来源实时认证或全部原页完成。

## 开发接口示例

安装可选组件 `python -m pip install .[pdf]`。调用 `cnlookthrough.report_adapter.parse_ruiyuan(pdf, report_date, published_at, source_url, net_assets, equity_value)`，金额须为人民币元且对应全部份额；总额由调用者原文核对。`to_spec(parsed, as_of)`只创建单基金快照输入，传给`cnlookthrough.engine.analyze`。公司发行人未核时保留空值，不计算公司集中度。`compare_snapshots(before, after)`仅输出证券披露变化。

解析与转换代码复用同作者research-workbench的MIT持仓解析逻辑并限定适配，不依赖主工作台安装；未复制外部项目或打包原始报告。

本次开发结果分别记录toolVersion、inputSchema和rulesVersion。未发布开发接口不与既有v0.1.0发布包混称；主工作台转换需明确适配版本。

独立命令入口（不下载PDF）：
```bash
python -m cnlookthrough.report_cli report.pdf --report-date 2026-06-30 --published-at 2026-08-27 --source-url ORIGINAL_HTTPS_URL --net-assets ALL_SHARE_CLASS_NAV_CNY --equity-value EQUITY_TOTAL_CNY --as-of 2026-10-09 --format engine --out new-input.json
python -m cnlookthrough new-input.json --format markdown --out new-report.md
```
`--format parsed`保留原表与定位；engine输出可供独立引擎/主包显式桥接，analysis/markdown/html可直接穿透。仅来源、版式和金额核对符合限定范围时使用；其他报告走人工整理原JSON接口，不能更换单位/总额绕过失败。
