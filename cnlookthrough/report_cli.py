"""Explicit bounded local PDF adapter entry, no acquisition or installation."""
import argparse,json,sys,html
from pathlib import Path
from .report_adapter import parse_ruiyuan,parse_chinaamc_growth,to_spec
from .engine import analyze

def main():
 for stream in (sys.stdout,sys.stderr):
  if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
 p=argparse.ArgumentParser(description='限定睿远成长价值年报/中报完整股票表；不自动取数')
 p.add_argument('--profile',choices=['ruiyuan','chinaamc-growth-2025'],default='ruiyuan')
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
 except ImportError:p.exit(2,'缺少可选PDF组件，请在可信项目环境安装pdf可选依赖；未生成适配结果。'+chr(10))
 except (ValueError,KeyError,TypeError,OSError,ArithmeticError) as error:p.exit(2,'未能完成限定适配：'+str(error)+'；旧输出未覆盖。'+chr(10))
if __name__=='__main__':main()
