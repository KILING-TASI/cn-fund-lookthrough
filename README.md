# 中国基金持仓穿透

按披露持仓与明确映射计算底层资产、公司重叠和未知部分。

[原创代码 MIT](LICENSE) · [发行说明](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/tag/v0.3.6) · [运行检查](https://github.com/KILING-TASI/cn-fund-lookthrough/actions) · [English](README.en.md)

当前发布：**v0.3.6 · 普通发行版**。Python **3.10+**；基础功能只需 Python，无第三方运行依赖。

[快速开始](#快速开始) · [使用自己的资料](#使用自己的资料) · [能力与边界](#能力与边界) · [文档与维护](#文档与维护)

## 能解决什么问题

**几只基金是否重复持有同一批公司？还有多少资产未能穿透？**

独立维护持仓路径和敞口计算；综合基金评价与整体配置风险分别由工作台和组合工具负责。

| 需要准备 | 会得到什么 |
|---|---|
| 披露持仓、披露日期、权重或金额、基金层级及证券与公司映射。 | 已知底层敞口、公司重叠、集中度和未披露或未映射比例。 |

## 快速开始

1. 安装 Python 3.10 或以上版本。
2. 下载[完整源码 ZIP](https://github.com/KILING-TASI/cn-fund-lookthrough/releases/download/v0.3.6/cn-fund-lookthrough-v0.3.6-source.zip)并解压，进入包含 `try_demo.py` 的目录。
3. 在该目录打开终端，运行：

```console
python try_demo.py --no-open --out-dir reports/first-demo
```

按终端给出的路径打开 HTML。也可以在源码目录双击 `Start-Demo.cmd`（Windows），或运行 `sh Start-Demo.sh`（Linux/macOS）。教学使用原创模拟资料，不自动取得真实数据。

使用 Git 时，先运行 `git clone https://github.com/KILING-TASI/cn-fund-lookthrough.git`，再运行 `cd cn-fund-lookthrough`，随后执行上面的教学命令。重复运行请指定新目录，历史结果会保留。

[报告示例源码](examples/readme-preview.html)：GitHub 会展示 HTML 源码，请下载完整源码后在浏览器中打开。

## 使用自己的资料

先按[资料准备与排错](BEGINNER.md)整理来源、日期、单位和必要字段，再按[使用说明](USAGE.md)选择对应入口。以下两种使用方式分别配置。

**命令行（CLI）**：在源码目录安装本仓，然后查看可用命令：

```console
python -m pip install .
cn-fund-lookthrough --help
```

可选组件按需要安装：`pdf`。例如 `python -m pip install ".[pdf]"`；依赖范围见 [使用说明](USAGE.md)。安装时下载构建工具或可选依赖可能需要联网。

**助手 Skill**：按 [SKILL.md](SKILL.md) 配置，保留完整目录及其引用资源。安装 CLI 不会自动注册 Skill，也不表示已在第三方技能市场上架。

| 身份 | 名称 |
|---|---|
| GitHub 仓库 / Python 发行包 | `cn-fund-lookthrough` |
| 主要命令 | `cn-fund-lookthrough` |
| SKILL.md 中的名称 | `cn-fund-lookthrough` |

本仓可单独使用。需要跨工具功能时，再按说明安装并明确配置对应工具的位置。

## 能力与边界

披露不等于实时完整持仓；未披露或未映射资产保留未知，覆盖率不是准确率。

报告中的来源、日期、假设和未知事项需一起阅读。程序运行成功不等于来源已经认证、资料完整或投资判断有效。原创代码采用MIT，第三方代码、公告、研报和数据仍按各自权利范围处理。

## 文档与维护

- [详细命令与方法](USAGE.md)
- [资料准备与排错](BEGINNER.md)
- [Skill 调用指引](SKILL.md)
- [版本记录](CHANGELOG.md)
- [许可与第三方范围](THIRD_PARTY_NOTICES.md)
- [审计范围](AUDIT_SCOPE.md)
- [计算方法](METHODS.md)
- [扩展专题](EXPANSION.md)

[贡献说明](CONTRIBUTING.md) · [安全反馈](SECURITY.md) · [更新与清理](LIFECYCLE.md)

[按问题选择其他工具](https://github.com/KILING-TASI/research-workbench/blob/main/references/tool-navigation.md)；资料契约校验已并入[数据仓](https://github.com/KILING-TASI/cn-data-adapters/blob/main/CONTRACT_MIGRATION.md)。默认分支的文档整理不改写已发布的源码包和历史结果；版本变化见 [CHANGELOG.md](CHANGELOG.md)。
