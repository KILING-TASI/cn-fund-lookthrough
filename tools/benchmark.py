"""Deterministic synthetic benchmarks in fresh processes; no trading data or extrapolation."""
import argparse,hashlib,json,os,platform,subprocess,sys,time,tracemalloc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cnlookthrough import analyze

def fixture(count,shape):
    per=min(count,1000);nodes={};master={};roots=[]
    if shape=='shared':
        for i in range(per):master[f'S{i}']=dict(kind='stock',issuer=f'教学公司{i}',source='原创合成身份')
        rows=[dict(kind='stock',security=f'S{i}',weight=.9/per) for i in range(per)]
        nodes['leaf']=dict(currency='CNY',source='原创合成',reportDate='2025-12-31',publishedAt='2026-03-31',holdings=rows)
        paths=max(1,count//per)
        for i in range(paths):nodes[f'N{i}']=dict(currency='CNY',source='原创合成',reportDate='2025-12-31',publishedAt='2026-03-31',holdings=[dict(kind='fund',node='leaf',weight=1/paths)])
        nodes['root']=dict(currency='CNY',source='原创合成',reportDate='2025-12-31',publishedAt='2026-03-31',holdings=[dict(kind='fund',node=f'N{i}',weight=1) for i in range(paths)]) if paths==1 else dict(currency='CNY',source='原创合成',reportDate='2025-12-31',publishedAt='2026-03-31',holdings=[dict(kind='fund',node=f'N{i}',weight=1/paths) for i in range(paths)])
        # Intermediate weights remain 1 so repeated shared-leaf paths conserve root weights.
        for i in range(paths):nodes[f'N{i}']['holdings'][0]['weight']=1
    else:
        for k,start in enumerate(range(0,count,per)):
            n=min(per,count-start);rows=[]
            for i in range(n):
                sid=f'S{start+i}';master[sid]=dict(kind='stock',issuer=f'教学公司{start+i}',source='原创合成身份');rows.append(dict(kind='stock',security=sid,weight=.9/n))
            nodes[f'L{k}']=dict(currency='CNY',source='原创合成',reportDate='2025-12-31',publishedAt='2026-03-31',holdings=rows)
        nodes['root']=dict(currency='CNY',source='原创合成',reportDate='2025-12-31',publishedAt='2026-03-31',holdings=[dict(kind='fund',node=k,weight=1/len(nodes)) for k in nodes])
    return dict(asOf='2026-10-09',currency='CNY',positions=[dict(id='原创合成组合',node='root',weight=1)],nodes=nodes,securities=master)

def peak_process_bytes():
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
        c=Counters();c.cb=ctypes.sizeof(c)
        kernel=ctypes.WinDLL('kernel32');kernel.GetCurrentProcess.restype=wintypes.HANDLE
        api=ctypes.WinDLL('psapi').GetProcessMemoryInfo;api.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD];api.restype=wintypes.BOOL
        if not api(kernel.GetCurrentProcess(),ctypes.byref(c),c.cb):return None
        return c.PeakWorkingSetSize
    import resource
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform=='darwin' else value*1024

def child(count,shape):
    spec=fixture(count,shape);raw=json.dumps(spec,sort_keys=True,ensure_ascii=False).encode();tracemalloc.start();start=time.perf_counter();r=analyze(spec);elapsed=time.perf_counter()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert abs(r['knownExposure']+r['unknownExposure']-1)<1e-8
    return dict(requestedCount=count,shape=shape,inputHoldingRows=sum(len(n['holdings']) for n in spec['nodes'].values()),expandedLeafPaths=len(r['paths']),
        wallSeconds=elapsed,tracemallocPeakBytes=peak,processLifetimePeakResidentBytes=peak_process_bytes(),inputUtf8Bytes=len(raw),inputSha256=hashlib.sha256(raw).hexdigest(),cli16MiBWouldAccept=len(raw)<=16*1024*1024)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--counts',default='1000,10000,50000');p.add_argument('--out',type=Path);p.add_argument('--child',type=int);p.add_argument('--shape',choices=['flat','shared'],default='flat');a=p.parse_args()
    if a.child is not None and not 1<=a.child<=500000:p.error('child count outside bounded range')
    if a.child is not None:print(json.dumps(child(a.child,a.shape)));raise SystemExit()
    counts=[int(v) for v in a.counts.split(',')]
    if not counts or any(v<1 or v>500000 for v in counts):p.error('本复现工具限定1至500000条，避免把结构上限当推荐负载')
    if not a.out or a.out.exists():p.error('--out须为新文件，拒绝覆盖')
    records=[]
    for shape in ['flat','shared']:
        for n in counts:
            result=subprocess.run([sys.executable,__file__,'--child',str(n),'--shape',shape],capture_output=True,text=True,encoding='utf-8',timeout=180,env=dict(os.environ,PYTHONIOENCODING='utf-8'))
            if result.returncode:raise RuntimeError(result.stderr)
            records.append(json.loads(result.stdout))
    engine=Path(__file__).resolve().parents[1]/'cnlookthrough/engine.py'
    report=dict(python=sys.version,platform=platform.platform(),cpuCount=os.cpu_count(),engineSha256=hashlib.sha256(engine.read_bytes()).hexdigest(),methodSha256={name:hashlib.sha256((engine.parents[1]/name).read_bytes()).hexdigest() for name in ['cnlookthrough/engine.py','cnlookthrough/input_diagnostics.py','tools/benchmark.py']},measurement='fresh subprocess; input built before tracemalloc; process peak includes fixture and runtime; timed region analyze only',records=records,limitations=['仅原创合成样本，不是全市场或真实完整持仓','tracemalloc仅Python跟踪分配；进程峰值单列，均不是部署内存保证','不从有限点证明O(n)，共享节点按展开路径计量；未涵盖所有深度和循环形状','未计JSON解析、报告渲染与写盘；文件大小与API结构限制分开'])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
