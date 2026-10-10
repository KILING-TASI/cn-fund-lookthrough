# 输入契约与股票持仓导入

| 入口 | 支持格式 | 输出与边界 |
|---|---|---|
| `python -m cnlookthrough.preflight --contract` | 无输入，列出契约 | stdout契约索引；不是JSON Schema |
| `python -m cnlookthrough input.json --validate-only` | cnlookthrough-nodes-v1 | JSON预检；不联网、不读PDF、不写文件、不做穿透；错误退出码2 |
| `python -m cnlookthrough.csv_import holdings.csv --config config.json --validate-only` | user-stock-holdings-csv-v1 | 校验本地CSV转换；不写文件，不执行敞口计算 |
| `python -m cnlookthrough.csv_import holdings.csv --config config.json --out imported.json` | 同上 | 新JSON，已有文件拒绝覆盖；原值、配置和原CSV字节SHA256保留在metadata |

`--dry-run`是`--validate-only`的别名。预检通过是declared-fields-valid，不是来源、原文或完整性核验通过；全部声明节点均检查，循环、路径规模、深度和权重守恒仍由正式运行处理。

CSV仅支持用户明确整理的股票清单，不自动解析交易所PCF、PDF、基金联接比例或在线数据源。列及顺序固定为security,weightPercent,issuer,identitySource；权重按父基金净资产，数字3.18表示3.18%。不得把前十大或股票部分重新归一。交易所前缀必须明确，公司未知时issuer留空；无identitySource时整个证券映射保留未知。重复证券、未知列、未来披露、合计超过100%均拒绝。

配置须明确format、asOf、currency、positionId、nodeId、source、reportDate、publishedAt、weightBasis和disclosureScope。此版本仅CNY，weightBasis固定parent-net-assets，disclosureScope仅top-holdings或declared-full，后者只是用户声明。生成的是单基金占100%的研究输入，不等于用户真实组合；需要嵌套其他基金时仍明确组织positions/nodes。

```powershell
python -m cnlookthrough.csv_import examples/holdings-import.csv --config examples/holdings-import-config.json --validate-only
python -m cnlookthrough.csv_import examples/holdings-import.csv --config examples/holdings-import-config.json --out reports/import-first.json
python -m cnlookthrough reports/import-first.json --format html --out reports/import-first.html
```

示例只有35%已分类证券，65%未披露余额保持未知，其中15%没有公司映射；代码仅演示中国证券身份格式。所有教学数值为原创模拟。导入成功不证明原始数据取得权利、证券身份或声明持仓正确；分享导入JSON前检查metadata中的来源、配置和原值。
