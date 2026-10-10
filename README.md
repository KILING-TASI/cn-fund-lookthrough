# 中国基金持仓穿透

看基金是否买了同一批公司，并保留联接基金、FOF的投资路径和暂时看不清的部分。

[![原创代码 MIT](https://img.shields.io/badge/原创代码-MIT-green)](LICENSE) [![测试](https://github.com/KILING-TASI/cn-fund-lookthrough/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/KILING-TASI/cn-fund-lookthrough/actions/workflows/tests.yml)

## 安装和首次试用

本轮对应[发布页](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/tag/v0.2.2)；下载时以实际上传的完整源码、wheel、sdist 与校验清单为准。源码按下面步骤安装；下载 wheel 后，将安装命令末尾的 `.` 换成该 wheel 文件路径。pip 安装不会自动注册 AI 工具中的 Skill。

本轮源码版本为 `0.2.2`。统一安装入口需要 Python 3.10 或以上。在完整源码目录新建自己的 Python 环境，下面的 Windows 命令不需要激活脚本：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\cn-fund-lookthrough.exe --help
.\.venv\Scripts\cn-fund-lookthrough.exe demo --out-dir reports/demo --auto-name
```

工具名与仓库名相同；在已激活的环境中可以直接输入工具名。Linux/macOS 使用 `.venv/bin/python` 和 `.venv/bin/cn-fund-lookthrough`。教学结果写入当前工作目录；`--auto-name` 自动另选新名字，旧结果保留。不加该参数时，教学入口拒绝已有目录。`cn-fund-lookthrough run --help` 查看原生参数，原来的命令继续兼容。pip 安装提供 CLI；作为 Skill 使用仍须保留完整源码及许可资源，不能只复制 SKILL.md。安装可能需要联网获取普通构建依赖；教学离线。下面保留原生入口及此前发行记录，本轮安装和版本以本节为准。

导入自己的资料前，可先运行 `python -m cnlookthrough input.json --validate-only`；[输入契约索引](examples/INPUT_CONTRACTS.md)列出字段、入口与预检限制。

## 先试一次

下载或克隆本仓库后，在仓库根目录运行。需要 **Python 3.10+**；这个教学例子只用标准库，不安装依赖、不联网。

```powershell
python -m cnlookthrough examples/demo.json --format html --out "local-data/第一次教学报告.html"
```

打开生成的 `local-data/第一次教学报告.html`。终端会提示结果位置，并标明输入声明为教学样本。再次运行时换一个新文件名，旧报告不会被覆盖；父目录可以复用。

## 结果是什么样

教学组合中，**84%的权重能解释，16%仍未知**；公司A占组合52.4%。这些数字说明已知部分的结构，不代表实际账户，也不是实时持仓。已映射股票约相当于2.13个等权公司，不能据此说整个组合只有这些风险来源。

[打开实际生成的教学HTML（下载后查看）](examples/readme-preview.html) · [查看教学输入](examples/demo.json) · [查看生成记录](examples/readme-preview-manifest.json)

想看筛选、排序和保存输入的效果，可打开[另一份实际教学报告](examples/filter-sort-preview.html)。只改变表格显示，不重新计算。以上报告保持原样，尚未完成浏览器视觉验收。

## 能做什么，哪些还不能判断

| 要看什么 | 当前能给出的结果 |
|---|---|
| 联接基金、FOF是否绕了几层买到同一证券 | 按每条投资路径乘权重，再汇总；重复路径分别保留 |
| 子基金缺报告，或只取得部分持仓 | 把缺失、循环和未披露余额列为未知，不填零，不把已知部分放大到100% |
| 多只基金是否重复买了同一家公司 | 分别展示证券和有依据的公司敞口；没有公司映射就保留缺口 |
| A/C份额、A/H证券是否应该合并 | 依据明确关系处理，不仅凭名称合并；A/H证券与公司层分别记录 |
| 本地基金报告中的完整股票表 | 限定睿远成长价值年报/中报及华夏成长2025年报，核对净资产分母和股票金额，保留原表位置 |

本工具读取你已取得的资料，不自动下载报告或采集全市场。它不能还原逐日交易、确认当前真实仓位，或仅凭持仓重叠判断基金该不该卖。不同报告期不当作同时持仓；季报前十大不能当成完整股票表。

外币换算、杠杆、衍生品Delta、发行人自动识别和收益回测暂不支持。限定PDF解析不能套用到任意管理人或扫描件，QDII格式尚未迁移。具体支持条件见[报告适配与转换说明](ROADMAP.md)、[华夏选定样本及未核项](SECOND_MANAGER.md)。

## 独立使用，也可以通过Skill调用

本仓有[Skill入口](SKILL.md)，其 `name` 是 **`cn-fund-lookthrough`**；同时提供可独立运行的Python引擎。仓库和安装包叫 `cn-fund-lookthrough`，命令模块叫 `cnlookthrough`。

使用Skill时保留整个项目目录，包括 `SKILL.md`、`README.md`、`examples/`、`cnlookthrough/` 等资源，不要只复制一个说明文件。CLI和Skill都不依赖其他自家仓库、作者缓存或行情账户，也不会自动改动已安装Skill。

[research-workbench](https://github.com/KILING-TASI/research-workbench)可以显式调用本引擎来组织研究与报告，但不是运行本工具的前提。本仓负责披露持仓穿透，不替代基金综合评价或交易决策。

### 安装后使用

如果希望在其他目录调用，在仓库根目录安装到单独的虚拟环境。下面是Windows示例，不需要激活脚本：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m cnlookthrough examples/demo.json --out "local-data/第一次教学底稿.json" --human
```

这里仍从仓库目录读取示例；换到其他目录运行时，传入自己输入文件的完整路径。安装构建需要普通第三方 `setuptools>=68`，pip可能联网下载；分析核心没有第三方运行依赖。

限定PDF入口另需 `pdfplumber>=0.11,<0.12` 及其第三方依赖。在同一源码版本和环境中安装：

```powershell
.\.venv\Scripts\python.exe -m pip install ".[pdf]"
.\.venv\Scripts\python.exe -m cnlookthrough.report_cli --help
```

安装可能联网，程序不会自动安装。依赖就绪后，解析你提供的本地PDF不需要程序自动取数；参数示例见[睿远入口](ROADMAP.md)和[华夏入口](SECOND_MANAGER.md)。

主引擎的默认JSON stdout保持可解析格式；`--human`只向stderr补使用提示。保存HTML或Markdown时自动提示打开位置。目标文件已存在就换新名字；缺PDF组件按上面的命令安装；输入无效时核对提示指出的字段。PDF入口的JSON写入指定文件，原有终端回执保留。详细输入示例与边界见下方。

### 准备自己的输入

参考[完整教学输入](examples/demo.json)：根持仓权重按同一估值日的人民币市值换算，合计为1，不能直接用份额数量代替市值。每条基金持仓权重相对于父节点净资产；前十大不能重新归一。

`asOf`记录资料截止日，`currency`记录统一币种；`positions`列根持仓，`nodes`保存来源、报告期、实际公开日及持仓，`securities`保存证券分类和有依据的公司映射。缺公司身份不猜名称关系。日期、分母和未知处理见[方法说明](METHODS.md)及[中国公募情景](CN_SCENARIOS.md)。

下面是教学输入中完整的证券映射部分，证券代码必须与持仓行的`security`一致。这些名称和依据都是教学声明，不能复制到真实基金充当证据：

```json
{
"securities": {
  "CN-SSE:DEMO-A": {"kind": "stock", "issuer": "教学公司A", "source": "教学证券身份映射"},
  "CN-SSE:DEMO-B": {"kind": "stock", "issuer": "教学公司B", "source": "教学证券身份映射"},
  "CN-SSE:DEMO-C": {"kind": "stock", "issuer": "教学公司C", "source": "教学证券身份映射"}
}
}
```

不要将`securities`改成`issuerMap`，也不要将每项对象简写为公司名称，或把`issuer`写成`issuerName`。字段误写会提示未被使用，不自动转换。每项`kind`是证券分类，`issuer`可为有依据的公司名称或`null`，`source`必须注明依据；本次用到的映射缺来源会报错，不自动补上。

没有`securities`或某项证券分类时，相应敞口列入未知；已有分类和来源、只缺`issuer`时，证券金额仍保留，公司未映射敞口单列，不计算虚构的公司数。金额权重能算出来不代表身份已经认证。

输入诊断采用`declared-input-fields-1`：仅有告警时在JSON旁加`inputDiagnostics`，包含`version`和`warnings`（每项为`code`、`fieldPath`、`message`），同时向stderr提示；正常教学输入原结果字段和数值不变。未知字段继续受理但提示未用于计算；既有适配版本、转换版本、教学账户、节点范围/名称和证券`issuerEvidence`保留兼容。附加资料可放在任一已检查对象的`metadata`、`extensions`或`notes`中，其内容不参与计算或自动认证。未知的显式`inputSchema`仍拒绝。例子和反例见[情景说明](SCENARIOS.md#输入字段诊断)；核心规则仍为`disclosed-paths-2`。

## 当前源码与旧发布包

此前v0.2.0发行时的功能如下；当前源码与本轮版本以上方安装节为准。披露穿透、限定报告适配、公司映射与情景验证已集成默认分支；**`v0.2.0`已发布**，安装包与完整源码可从下方链接下载；旧 **`v0.1.0`研究预览版**保留历史，不包含全部新增接口。克隆当前源码与安装旧发布包不是同一版本，旧安装不会自动更新。

[下载v0.2.0 Release](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/tag/v0.2.0) · [发布说明与安装方式](RELEASE_NOTES.md) · [旧v0.1.0 Release](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/tag/v0.1.0) · [查看源码版本与可选依赖](pyproject.toml)

[完整Skill与源码ZIP](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.2.0/cn-fund-lookthrough-v0.2.0-source.zip) · [Python wheel安装包](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.2.0/cn_fund_lookthrough-0.2.0-py3-none-any.whl) · [sdist源码包](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.2.0/cn_fund_lookthrough-0.2.0.tar.gz) · [SHA256摘要](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.2.0/SHA256SUMS.txt)

发布资产固定于提交`7afd2b5`；本页更新发布状态和下载链接，标签内的准备记录、历史输入和结果保持原样。

## 验证、来源与许可

CI在Windows/Linux、Python 3.10/3.12检查测试、单仓安装及教学报告。隔离安装不依赖主工作台；这不是全新操作系统验收，也不证明真实基金全覆盖。自然语言发现、浏览器视觉及旧Release的重新安装验收尚未完成。

- [披露穿透情景与实际结果](SCENARIOS.md)：嵌套、未知、缺证据和失败实例。
- [中国公募情景与官方口径](CN_SCENARIOS.md)：季报范围、A/C市值、A/H身份与转换反例。
- [华夏选定原文样本](SECOND_MANAGER.md)与[睿远样本记录](validation/limited-real-samples.json)：限定版式、金额核对及证据缺口。
- [历史截图尝试记录（2026-10-09）](https://github.com/KILING-TASI/cn-fund-lookthrough/blob/4b4a4c86d12cb5afb7f19ac87b8325edf0bde036/README.md#结果表筛选与排序待审)：原HTML未取得截图，未绕过浏览器策略。

原创代码采用[MIT许可](LICENSE)，原贡献者版权保留。[第三方与资料权利](THIRD_PARTY_NOTICES.md)单独说明；代码许可不授权再分发报告原件、公告或数据，本仓不打包原始PDF、私人账户或作者缓存。

本项目用于学习与研究，不构成投资建议或交易指令。使用时结合本次来源、假设和缺口判断；完整边界见[免责声明](DISCLAIMER.md)。

## 导入前先预检

`python -m cnlookthrough input.json --validate-only`（或`--dry-run`）只检查本地声明字段，不联网、不读PDF、不写报告，也不执行专业计算。问题按fieldPath列出；通过不证明来源或完整性。`python -m cnlookthrough.preflight --contract`查看契约索引。完整入口与边界见[输入契约说明](examples/INPUT_CONTRACTS.md)。
