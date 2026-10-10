# v0.2.0 发布说明

这次更新帮助你看清基金是否重复买了同一批公司，并把未披露、缺子基金和缺身份依据的部分单独留下。它读取已有披露资料，不代表实时仓位，也不提供交易指令。

v0.2.0已于2026年10月10日发布，资产固定于提交`7afd2b5f5acb082c5eafa91265a28ecc3d33d74d`。旧v0.1.0及构建时的准备记录保留；下列链接指向已上传的实际资产：

- [cn-fund-lookthrough-v0.2.0-source.zip](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.2.0/cn-fund-lookthrough-v0.2.0-source.zip)：完整Skill和源码资源，解压后运行README最短教学命令。
- [cn_fund_lookthrough-0.2.0-py3-none-any.whl](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.2.0/cn_fund_lookthrough-0.2.0-py3-none-any.whl)：Python安装包，分析核心不需额外运行依赖；附教学输入。
- [cn_fund_lookthrough-0.2.0.tar.gz](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.2.0/cn_fund_lookthrough-0.2.0.tar.gz)：含Skill、源码和示例的源代码分发包。
- [SHA256SUMS.txt](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.2.0/SHA256SUMS.txt)：资产摘要，下载后可与本地文件核对。

## 这次已有的改进

支持联接基金和FOF的显式路径穿透，重复路径与未知余额一起保留；证券和公司层分别统计，A/C及A/H不只凭名称合并。限定PDF适配覆盖已核睿远成长价值年报/中报与华夏成长2025年报，非股票余额仍未知。

输入误写为issuerMap时会说明字段未被读取，并指出securities的kind/issuer/source结构；合法扩展继续受理，未知显式schema仍拒绝。CLI提示结果位置、错误下一步和实际PDF可选依赖；正常JSON结果格式保持，仅有告警时旁加inputDiagnostics。

统一安装包、模块和Skill软件版本为0.2.0。核心disclosed-paths-2、nodes-v1、转换/解析/身份映射规则不变，历史输入和结果不改版本；新的toolVersion标明当前软件，不把旧结果冒充本次生成。

## 怎样安装

下载v0.2.0资产后使用以下命令，不会自动改动已安装Skill。Python3.10+，Windows示例：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --no-deps ".\cn_fund_lookthrough-0.2.0-py3-none-any.whl"
.\.venv\Scripts\python.exe -m cnlookthrough ".\.venv\share\cn-fund-lookthrough\examples\demo.json" --format html --out ".\第一次教学报告.html"
```

打开生成的HTML。再次运行请换新文件名，旧报告不覆盖。wheel附带的demo只需标准库；额外PDF组件仍按README安装pdf extra，pip可能联网，不随本包捆绑。

Skill入口name保持cn-fund-lookthrough；从完整源码ZIP使用，保留SKILL.md、README、examples和cnlookthrough等资源。wheel是独立CLI安装包，不代替完整Skill资源。

原创代码MIT及原贡献者版权保留。第三方/公告/数据权利单独说明；包内无PDF原件、私人账户、作者缓存或其他自家仓。教学和限定格式检查不算真实身份认证，浏览器视觉、自然语言发现、全市场/实时和新管理人版式仍未验。36项源码回归、最终main独立安装、教学运行及该提交CI均通过；下载文件以实际资产和SHA256SUMS为准。

[查看v0.2.0 Release](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/tag/v0.2.0) · [标签内保留的发布准备说明](https://github.com/KILING-TASI/cn-fund-lookthrough/blob/v0.2.0/RELEASE_NOTES.md)
