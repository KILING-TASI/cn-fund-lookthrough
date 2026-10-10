"""Throttled CLI stage feedback; never changes numeric output."""
import sys,time
class Progress:
    def __init__(self,stream=None,clock=time.monotonic,interval=2, force=False, delay=10):
        self.stream=stream or sys.stderr;self.clock=clock;self.interval=interval;self.last=None;self.started=clock();self.force=force;self.delay=delay
    def __call__(self,phase,count=None):
        now=self.clock()
        if not self.force and now-self.started<self.delay:return
        if self.last is not None and now-self.last<self.interval and phase!='complete':return
        labels={'input-check':'检查输入与声明字段','traverse':'展开已披露路径','aggregate':'汇总证券和公司敞口','complete':'计算完成，正在准备结果'}
        extra='' if count is None else f'；已检查{count}条持仓记录（不是总进度百分比）'
        print('进度：'+labels[phase]+extra,file=self.stream,flush=True);self.last=now
