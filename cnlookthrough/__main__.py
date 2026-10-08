import argparse,json,html
from pathlib import Path
from .engine import analyze

def pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('JSON字段重复：'+k)
  d[k]=v
 return d

def main():
 p=argparse.ArgumentParser(description='中国基金持仓穿透；读取声明资料，不自动联网')
 p.add_argument('input',type=Path);p.add_argument('--format',choices=['json','markdown','html'],default='json');p.add_argument('--out',type=Path)
 a=p.parse_args()
 try:
  if a.input.stat().st_size>16*1024*1024:raise ValueError('输入过大')
  spec=json.loads(a.input.read_text('utf-8-sig'),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('JSON不能含NaN或Infinity')))
  r=analyze(spec)
  from .report import markdown
  text=json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False) if a.format=='json' else markdown(r)
  if a.format=='html':text='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>中国基金持仓穿透</title><style>body{max-width:900px;margin:40px auto;padding:0 24px;font:17px/1.8 system-ui,"Microsoft YaHei",sans-serif;color:#203047}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><body><pre>'+html.escape(text)+'</pre></body></html>'
  if a.out:
   a.out.parent.mkdir(parents=True,exist_ok=True)
   with a.out.open('x',encoding='utf-8') as f:f.write(text)
  else:print(text)
 except (ValueError,KeyError,TypeError,OSError,ArithmeticError) as e:p.exit(2,'未能完成：'+str(e)+'；未覆盖旧输出。\n')

if __name__=='__main__':main()
