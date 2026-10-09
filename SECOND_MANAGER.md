# 第二管理人限定样本：华夏成长2025年报

仅新增已实测的000001/2025年年报版式，不承诺其他产品、季度或管理人通用解析。原睿远入口保留。来源为华夏基金官网2026-03-31公开PDF，完整原件不加入源码包。

```sh
python -m cnlookthrough.report_cli /data/report.pdf --profile chinaamc-growth-2025 --report-date 2025-12-31 --published-at 2026-03-31 --source-url https://www.chinaamc.com.cn/upload/resources/file/2026/03/31/8b7d455376d9421b805f62a6d27cbffd.pdf --net-assets 2936772770.95 --equity-value 2332302763.09 --as-of 2026-10-09 --format analysis --out local-data/new-analysis.json
```

原文净资产分母29.37亿元，与权益投资23.32亿元分开；原资产配置表78.25%为总资产占比，不能当净资产权重。实际股票/NAV约79.42%，未穿透20.58%不是零。物理页5与46的分母/权益表格位置、标签、金额及比较年度核对；132条完整股票行与权益金额逐分一致。旧工作台同系列解析算法五字段逐条一致，属于回归交集核对，不称独立审计。

`cnlookthrough.issuer_snapshot.apply_snapshot_mappings` 接受 issuer-snapshot-map-v1/source-bound-snapshot-1。仅中际旭创300308按2025-12-31单日快照映射，来源为公司官方披露年报物理页7的代码与法定名称，绑定SHA/短引句/公布日。没有本地原文、超出披露日或快照日期时不应用。单日快照不是证券身份全历史有效期间。未映射证券保持未知，有效发行人数不得解释为全组合数字。

[限定核验记录](validation/chinaamc-growth-validation.json)、[公开计算输入](validation/chinaamc-growth-engine-input.json)、[未知余额结果](validation/chinaamc-growth-result.json)、[选定映射](validation/chinaamc-issuer-map.json)、[本地原页核验结果](validation/chinaamc-mapped-result.json)。公开映射无私人原文路径，重新运行时不直接认证已核。

缺口：扫描件、其他期版式、全部发行人、A/H身份历史、债券与其他资产穿透、浏览器视觉均未完成。没有将债券余额填成现金，也没有把本次输入写为用户账户。
