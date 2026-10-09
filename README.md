# 中国基金持仓穿透 · cn-fund-lookthrough

独立可运行的披露持仓分析工具。**v0.1.0，研究预览版**。回答“我的基金是否重复持有同一批公司”，保留ETF联接、FOF子基金的投资路径与未知余额。

Python 3.10+，计算核心只用标准库，不依赖research-workbench、行情账户或API密钥。输入由使用者或AI从公开报告整理，本版不自动下载或解析基金PDF。

## 五分钟试用

下载仓库，在仓库目录运行：

```bash
python -m cnlookthrough examples/demo.json
python -m cnlookthrough examples/demo.json --format markdown
python -m cnlookthrough examples/demo.json --format html --out local-data/report.html
python -m unittest discover -s tests -v
```

也可以 `python -m pip install .` 后在其他目录运行。示例是虚构基金和公司，不是投资推荐。输出文件必须不存在。HTML是可直接打开的轻量文字报告，不需要启动服务。

## 交付什么

- 沿根持仓→联接基金→ETF或FOF子基金递归乘权重，保留逐条路径。
- 子基金缺报告、循环引用、深度上限及未披露余额列为未知，不填零。
- 证券敞口与发行人敞口分别汇总。AH证券或不同份额不会仅凭名字自动合并；公司映射由调用者提供依据。
- 已映射股票部分的公司集中度等效数量 `1/HHI`，不是整个组合的独立风险来源数。
- 每项根持仓被其余持仓复制的公司暴露，以及独有公司暴露占比。独有公司为零不表示产品没有作用，更不等于应该卖出。
- 中文说明与JSON底稿；报告期不同明确保留，不当作同时持仓。

## 输入

完整格式见 [examples/demo.json](examples/demo.json)。金额组合应先按同一估值日的市值换算根权重；不能把份额和市值混用。

`asOf`为截止日，`currency`为统一币种；`positions`列根持仓唯一id、node和weight，权重用小数且合计1，现金也要明确记录。`nodes`列各披露快照的currency、source、reportDate、publishedAt和holdings。基金边填写kind=fund、node、weight；证券边填写kind、security、weight。节点持仓不足100%的余额留为未知。

`securities`提供证券到kind、issuer、source的映射；明确区分证券和发行人。kind为stock、bond、cash或other。发行人映射缺失时股票证券金额仍保留，但不虚构公司集中度。

首版不支持外币隐含换算、超过100%的毛资产杠杆、衍生品Delta穿透、发行人自动识别、全市场扫描或收益回测。持仓表直接股票可作为一个持仓节点输入。每条权重必须相对于其父节点资产口径，前十大权重不能重新归一到100%。

## 验证与开发

本地已验证嵌套乘权重、未知守恒、循环、未来披露、币种冲突、杠杆拒绝、证券/发行人分层及输出不覆盖。CI在Windows/Linux、Python 3.10/3.12运行同一测试和示例；CI成功不等于真实基金报表全覆盖。

后续优先增加真实基金报告适配与发行人关系证据核验，不承诺完整实时持仓。可与 [research-workbench](https://github.com/KILING-TASI/research-workbench) 的取数与报告流程配合，也可独立使用。两者当前接口不同，不假设自动互换输入。

原创部分采用MIT，见 [LICENSE](LICENSE)。数据与公告使用权属于各自提供方；本仓库不附第三方报告、账户资料或作者行情缓存，不构成投资建议。

## 免责声明

本项目仅供学习与研究，不构成投资建议或交易指令，不保证收益或结果准确性。请在使用前阅读[免责声明与使用边界](DISCLAIMER.md)，并结合本次数据来源、假设与缺口独立判断。代码许可不包含第三方数据使用授权。
