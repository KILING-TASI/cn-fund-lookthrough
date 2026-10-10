"""Human guidance on stderr; result schemas and stdout remain unchanged."""
import sys


def saved(output, format_name, teaching=False):
    identity = '输入声明为教学样本，非真实基金或账户。' if teaching else '仅分析声明的披露快照，不代表实时持仓或账户认证。'
    print('cn-fund-lookthrough 独立CLI引擎：已生成' + format_name + '结果。' + identity, file=sys.stderr)
    if output is not None:
        print('结果目录：' + str(output.resolve().parent), file=sys.stderr)
        verb = '打开报告：' if format_name in ('html', 'markdown') else '查看底稿：'
        print(verb + str(output.resolve()), file=sys.stderr)
    else:
        print('结果已写到stdout；使用 --out 新文件路径 可保存。', file=sys.stderr)


def failure(error, pdf=False):
    if isinstance(error, FileExistsError):
        return '输出文件已存在；请把 --out 换成新的文件名，旧文件保持不变。'
    if isinstance(error, FileNotFoundError):
        return '输入文件或目录不存在；请核对本地文件路径，有空格时用双引号包住。'
    if isinstance(error, PermissionError):
        return '无法读写指定路径；请检查文件权限并选择可写的新输出路径。'
    if isinstance(error, OSError):
        return '文件读写失败；请检查本地输入、路径与磁盘空间，再使用新的输出文件名。'
    fields = '--profile、报告期、公开日、来源和净资产分母；确认本地PDF属于已支持版式' if pdf else 'asOf、currency、positions、nodes、securities与权重分母'
    return str(error) + '；请核对输入的' + fields + '，参照仓库示例，不要把缺值填零。'


PDF_DEPENDENCY_HINT = '缺少可选PDF组件pdfplumber；在当前源码仓/版本的虚拟环境运行 python -m pip install ".[pdf]"。此安装可能联网；JSON教学入口无需PDF组件。未生成适配结果。'
