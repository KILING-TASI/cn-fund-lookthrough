# 从自己的问题开始

教学入口只验证软件能运行，不代表已经分析你的标的。先用已有资料回答能确定的部分：金额表说明钱放在哪里；披露持仓说明已知重合；公告和报表字段需区分期间、单位及版本。

## 首次试用

完整源码解压后，需要 Python。Windows 可运行 Start-Demo.cmd；也可在源码目录执行 `python try_demo.py`。Linux/macOS 可执行 `sh Start-Demo.sh`，自动打开浏览器依系统能力而定。运行前可用 `python try_demo.py --check`。不联网、不自动安装组件，新输出目录保留旧报告。不能把教学数值替代真实资料。

## 准备资料确认卡

先确认：你问什么；标的身份；研究截止日；来源及资料日期；金额还是份额；币种与单位；权重相对什么。已有会话信息无需重复追问。日期和单位无法确定时只做不依赖它们的解释，不补造。

## 看懂结果与失败

报告生成、输入通过、计算完成和来源核验分别判断。未知比例不是错误率，也不代表未知部分没有风险；说明它可能影响哪个问题。缺来源时提供原表或原文，缺组件时按README按需安装，输出已存在时换新目录。完整技术错误和原始警告留底稿，正文解释影响与下一步。

## 更新与追问

先明确沿用资料还是取得新资料。保存输入、参数和结果，另存新情景；不覆盖历史冻结结果。只有明确登记的资料才能复用，不能默选最新文件。受控取数和专题能力按各自README提供，不把本指南当作任意数据的自动采集器。

中文持仓准备：`python -m cnlookthrough.guide wizard --csv 自己的持仓.csv --out-dir reports/my-fund`。只接受明确整理的股票CSV；助手或用户确认来源、持仓日期、公开日期和净资产百分数。配置模板可用 `python -m cnlookthrough.guide init-config --out reports/config.json`，空白项不代表已通过。

| CSV | JSON | 含义 |
|---|---|---|
| weightPercent=3.18 | weight=0.0318 | 占父基金净资产3.18%，不是已披露股票部分的归一比例 |

交易所代码需来自有来源的证券目录或原文；不能只凭数字开头认证。公司未知留空，holdings内的issuer不作为顶层securities映射。

## 已有两份披露后回答重合并追问

用 question compare 输入清单声明相同截止日的2至10份单基金研究输入及配置百分数；每份保留原文来源与未知，不自动下载。示例见 examples/overlap-question.json。命令：python -m cnlookthrough.question compare --input examples/overlap-question.json --out-dir reports/overlap-first。

改变比例：python -m cnlookthrough.question follow --continue-from reports/overlap-first --weights 50 50 --out-dir reports/overlap-second。复用的是用户已选的快照，不是更新行情；旧输入变动会拒绝复用，方法变化会提示。

中文表格也可用：证券代码,交易所,权重百分数,公司,身份依据。交易所须在原表明确填写上交所、深交所或北交所；不会按数字开头推断。百分数列的3.18或3.18%均表示3.18%，不能填份额或股票部分归一比例。原表、转换表、原值与两份SHA256都会保留；公司未知留空。见 examples/holdings-chinese.csv（纯教学）。
