import argparse,json,html,sys
from pathlib import Path
from .engine import analyze

def pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('JSON字段重复：'+k)
  d[k]=v
 return d

def main():
 for stream in (sys.stdout,sys.stderr):
  if hasattr(stream,"reconfigure"):stream.reconfigure(encoding="utf-8")
 p=argparse.ArgumentParser(description='cn-fund-lookthrough 独立CLI引擎；可配合本仓同名Skill使用，读取声明资料，不自动联网')
 p.add_argument('input',type=Path);p.add_argument('--format',choices=['json','markdown','html'],default='json');p.add_argument('--out',type=Path)
 p.add_argument('--human',action='store_true',help='在stderr显示结果位置和下一步，stdout结果格式不变')
 a=p.parse_args()
 try:
  if a.input.stat().st_size>16*1024*1024:raise ValueError('输入过大')
  spec=json.loads(a.input.read_text('utf-8-sig'),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('JSON不能含NaN或Infinity')))
  r=analyze(spec)
  from .report import markdown
  text=json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False) if a.format=='json' else markdown(r)
  if a.format=='html':
   from .report import html_report
   text=html_report(r,spec)
  if a.out:
   a.out.parent.mkdir(parents=True,exist_ok=True)
   with a.out.open('x',encoding='utf-8') as f:f.write(text)
  else:print(text)
  if a.human or a.out and a.format in ('html','markdown'):
   from .cli_feedback import saved
   sources=[node.get('source','') if isinstance(node,dict) else '' for node in spec['nodes'].values()]
   teaching=bool(sources) and all(isinstance(source,str) and ('教学' in source or '虚构' in source) for source in sources)
   saved(a.out,a.format,teaching)
 except (ValueError,KeyError,TypeError,OSError,ArithmeticError) as e:
  from .cli_feedback import failure
  p.exit(2,'未能完成：'+failure(e)+'；未覆盖旧输出。\n')

if __name__=='__main__':main()
