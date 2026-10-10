"""Explicit bounded local PDF adapter entry, no acquisition or installation."""
import argparse,json,sys,html
from pathlib import Path
from .report_adapter import parse_ruiyuan,parse_chinaamc_growth,to_spec
from .engine import analyze

def main():
 for stream in (sys.stdout,sys.stderr):
  if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
 p=argparse.ArgumentParser(description='cn-fund-lookthrough 独立CLI引擎的限定PDF适配入口；支持范围见 --profile，不自动取数')
 p.add_argument('--profile',choices=['ruiyuan','chinaamc-growth-2025'],default='ruiyuan')
 p.add_argument('--human',action='store_true',help='在stderr显示结果位置和下一步；原stdout回执保持兼容')
 p.add_argument('pdf',type=Path);p.add_argument('--report-date',required=True);p.add_argument('--published-at',required=True);p.add_argument('--source-url',required=True);p.add_argument('--net-assets',required=True);p.add_argument('--equity-value',required=True);p.add_argument('--as-of');p.add_argument('--format',choices=['parsed','engine','analysis','markdown','html'],default='parsed');p.add_argument('--out',required=True,type=Path);a=p.parse_args()
 try:
  if a.out.exists():raise FileExistsError('输出已存在')
  if a.format!='parsed' and not a.as_of:raise ValueError('转换或穿透需明确资料截止日as-of')
  adapter=parse_ruiyuan if a.profile=='ruiyuan' else parse_chinaamc_growth
  parsed=adapter(a.pdf,a.report_date,a.published_at,a.source_url,a.net_assets,a.equity_value)
  result=parsed if a.format=='parsed' else to_spec(parsed,a.as_of)
  if a.format in ('analysis','markdown','html'):result=analyze(result)
  if a.format in ('markdown','html'):
   from .report import markdown
   text=markdown(result)
   if a.format=='html':text='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>限定披露持仓穿透</title><body><pre>'+html.escape(text)+'</pre></body></html>'
  else:text=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
  a.out.parent.mkdir(parents=True,exist_ok=True)
  with a.out.open('x',encoding='utf-8') as f:f.write(text)
  print('已按限定版式生成'+a.format+'结果；非股票余额仍为未知，不代表当前账户。')
  if a.human or a.format in ('html','markdown'):
   from .cli_feedback import saved
   saved(a.out,a.format)
 except ImportError:
  from .cli_feedback import PDF_DEPENDENCY_HINT
  p.exit(2,PDF_DEPENDENCY_HINT+chr(10))
 except (ValueError,KeyError,TypeError,OSError,ArithmeticError) as error:
  from .cli_feedback import failure
  p.exit(2,'未能完成限定适配：'+failure(error,pdf=True)+'；旧输出未覆盖。'+chr(10))
if __name__=='__main__':main()
