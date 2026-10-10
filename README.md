# 中国基金持仓穿透 · cn-fund-lookthrough

看清多只基金背后是否重复持有同一批公司；嵌套路径与未知余额一起保留。

## 先看结果，再试一次

[实际生成的教学HTML预览（下载后打开）](examples/readme-preview.html) · [对应输入](examples/demo.json) · [生成与版本记录](examples/readme-preview-manifest.json)

教学样本可解释84%的组合，16%未知；已映射股票约等效2.13个等权公司。这不是整个组合的风险来源数，也不是实际账户。 预览生成于2026-10-09，尚未取得截图或完成浏览器视觉验收；不是已发布版本的验收证明。

在仓库根目录运行，Python 3.10+，此教学demo只用标准库、不联网：

```bash
python -m cnlookthrough examples/demo.json --format html --out local-data/report.html
```

打开 `local-data/report.html`。输出目录/文件须不存在；重复运行请换新路径，不覆盖旧结果。限定PDF接口需要另装可选依赖，下面的教学demo不需要。

[返回主包按问题导航](https://github.com/KILING-TASI/research-workbench/blob/codex/bounded-research-extensions/references/tool-navigation.md)；本工具可单独使用，不强制安装主包。

独立可运行的披露持仓分析工具。回答“我的基金是否重复持有同一批公司”，保留ETF联接、FOF子基金的投资路径与未知余额。

Python 3.10+，计算核心只用标准库，不依赖research-workbench、行情账户或API密钥。输入由使用者或AI从公开报告整理，本版不自动下载基金PDF。首批开发版可用可选pdf组件解析限定睿远成长价值年报/中报完整股票表，具体验收范围见ROADMAP.md；不适用于任意管理人或季报。

## 版本状态

更新日期：2026-10-09。公开发布为 `v0.1.0`（研究预览版）；当前分支为 `0.2.0.dev1`，增量尚未发布，不能用旧发布包调用新接口。

基础教学示例与当前开发接口分开：先运行下面的离线示例；限定原文适配、真实样本和未完成项见[开发路线](ROADMAP.md)。原始报告不随源码分发。

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

后续优先增加真实基金报告适配与发行人关系证据核验，不承诺完整实时持仓。可与 [research-workbench](https://github.com/KILING-TASI/research-workbench) 的取数与报告流程配合，也可独立使用。两者接口不同；主包支持显式JSON桥，开发版另有限定PDF桥，不自动互换输入。

原创部分采用MIT，见 [LICENSE](LICENSE)。数据与公告使用权属于各自提供方；本仓库不附第三方报告、账户资料或作者行情缓存，不构成投资建议。

## 免责声明

本项目仅供学习与研究，不构成投资建议或交易指令，不保证收益或结果准确性。请在使用前阅读[免责声明与使用边界](DISCLAIMER.md)，并结合本次数据来源、假设与缺口独立判断。代码许可不包含第三方数据使用授权。


## 后续与项目关系

已有能力、限定适配、转换契约和验收缺口见[开发路线](ROADMAP.md)。适配和定位代码已实现，限定真实样本结果见路线链接；版本关系与其他管理人等缺口仍保留，不代表全部已完成。

开发分支版本为`0.2.0.dev1`，此前公开发布仍是`v0.1.0`；本批功能待PR审阅，不将本地完成写成已发布。

## 许可范围

[MIT原创许可](LICENSE)（KILING-TASI及原有贡献者版权） · [第三方、示例与数据范围](THIRD_PARTY_NOTICES.md)。第三方保留原许可；代码许可不包含原文、数据或品牌的再分发授权。

## 结果表筛选与排序（待审）

当前HTML可筛选表内文字、按首列名称排序，保存输入及方法摘要。只改变显示，不重新计算或改动未知余额/口径状态；仍需新输出路径，分享前检查保存的输入。原教学预览保持冻结，本次交互未截图、未做浏览器视觉验收。

[本次实际生成的筛选排序HTML](examples/filter-sort-preview.html)沿用[教学输入](examples/demo.json)，保存输入和方法摘要；只做文本与结构检查，未截图/视觉验收。旧readme-preview.html保持冻结。

截图重试记录（2026-10-09）：用户恢复权限后，本地HTML仍被浏览器file协议策略拒绝，且禁止绕过。实际HTML生成与代码验证已完成，三个报告尚未取得浏览器截图或视觉验收；不是合成图替代，也不是许可证或原件核验通过证明。

[方法卡与教学反例](METHODS.md)说明哪些声明被校验、哪些仍需原文；本轮验证规则升级到v2，无schema旧输入仍受理，不自动迁移未知版本。


新增限定实测：[第二管理人华夏成长样本](SECOND_MANAGER.md)，132条股票与原文分母/权益合计；仅选定证券单日发行人映射，其他未知。


当前待审增量的实现、真实样本、版本与未完成项见[详细交付状态](SECOND_MANAGER.md)；CI不代表原件认证或投资有效，不自动更新已安装版。

## 单仓隔离安装验收（当前待审版）

[披露穿透情景实例](SCENARIOS.md)：复用教学正例，新增FOF共享ETF、缺证据及拒绝实例；可用一条命令生成输入/手算预期/实际CLI报告与版本回执。仅教学验证，不扩大真实基金覆盖。

2026-10-10：仅本仓git源码归档构建wheel，在新目录、新venv且清除作者路径/缓存环境后，用已安装包生成教学HTML与JSON；未安装主工作台或其他自家库。模块origin位于新venv，报告教学标记、数值/未知状态与版本核对通过；重复输出拒绝，缺PDF组件不作为原页通过。CI新增同仓导出安装检查。宿主仍有其他仓库，此为目录/进程隔离，不是全新操作系统；已发布v0.1.0未另验，视觉/自然语言发现未验。
