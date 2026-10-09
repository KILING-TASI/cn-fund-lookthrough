# 许可范围与第三方说明

核对日期：2026-10-09。根LICENSE既有版权署名research-workbench contributors保持不变。本项目有权授权的原创代码/原创说明采用MIT；不能据此替第三方或来源不明内容授权。

## 本批代码来源

`cnlookthrough/report_adapter.py`复用并修改同作者research-workbench的持仓解析函数（清理、排序与完整股票表勾稽），不是来自未注明第三方项目。固定来源：[fund_report_holdings.py，a00ace5](https://github.com/KILING-TASI/research-workbench/blob/a00ace5/scripts/fund_report_holdings.py)。原MIT与版权保留，修改点为限定管理人版式、显式净资产/权益总额、行表定位与独立nodes转换。

来源文件SHA256：`71d05ac93364821152452255cef7fc82443be69ecfd6a00baa0bc51a1fa70a85`。根LICENSE保留原MIT全文；适配器头部保留来源与版权。该固定来源记录不是整个主包所有第三方代码的许可替代。

## 依赖、示例与未确认范围

Python标准库随使用者Python发行版；可选[pdfplumber](https://github.com/jsvine/pdfplumber/blob/stable/LICENSE.txt)采用MIT，读取链的传递依赖须按实际安装版本保留许可。这些库未捆绑；本清单不是完整递归软件物料清单，不自动认证未来版本。

examples/demo.json是虚构教学输入；readme-preview.html由其实际计算生成，不是真实基金或公司数据，只追加教学/日期标识，未取得截图或浏览器视觉验收。页面未捆绑字体，只使用系统后备字体。validation仅保留有限事实、来源URL和摘要，不附公告全文、PDF、机构图表、行情缓存或账户输入。

原文的访问或公开披露不等于已获再分发权；管理人、巨潮等原件和数据的商业再分发授权未确认，用户须按实际用途核对。MIT仅覆盖有权授权的项目内容，不授予外部行情、研报、公告、品牌或运行依赖的权利。
