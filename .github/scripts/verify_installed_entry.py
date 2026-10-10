"""Check the installed command away from its source tree and user cache."""
import hashlib,json,os,subprocess,sys,tempfile,sysconfig
from pathlib import Path

REPO='cn-fund-lookthrough'

def check():
    binary=Path(sysconfig.get_path('scripts'))/(REPO+'.exe' if os.name=='nt' else REPO)
    with tempfile.TemporaryDirectory(prefix='installed-entry-') as tmp:
        root=Path(tmp);home=root/'empty-home';home.mkdir()
        env={k:v for k,v in os.environ.items() if not k.startswith(('PYTHON','RESEARCH_WORKBENCH_','CODEX','PORTFOLIO_'))}
        env.update(HOME=str(home),USERPROFILE=str(home),PYTHONIOENCODING='utf-8')
        def run(args,expected=0):
            result=subprocess.run([str(binary),*args],cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',timeout=300)
            assert result.returncode==expected,(args,result.stdout,result.stderr)
            return result
        assert '--auto-name' in run(['--help']).stdout
        assert '需要一个明确' in run(['run','--out-dir=a','--out-dir=b','--auto-name'],2).stderr
        first=run(['demo','--out-dir','reports/demo'])
        def hashes():
            return {str(p.relative_to(root/'reports/demo')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'reports/demo').rglob('*') if p.is_file()}
        frozen=hashes();assert frozen
        assert '--auto-name' in run(['demo','--out-dir','reports/demo'],2).stderr
        assert hashes()==frozen
        run(['demo','--out-dir','reports/demo','--auto-name'])
        assert len(list((root/'reports').iterdir()))==2 and hashes()==frozen
        if REPO=='portfolio-decision-engine':
            assert '请打开' in first.stderr and '教学' in first.stderr
        examples=Path(sys.prefix)/'share'/REPO/'examples'
        sample=examples/'demo.json'
        assert (examples/'INPUT_CONTRACTS.md').is_file()
        preflight=json.loads(run(['run',str(sample),'--validate-only']).stdout)
        assert preflight['status']=='declared-fields-valid' and not preflight['calculationPerformed']
        assert not preflight['networkAccess'] and not preflight['originalVerified']
        def module(args,expected=0):
            result=subprocess.run([sys.executable,'-I','-m',*args],cwd=root,env=env,capture_output=True,text=True,encoding='utf-8')
            assert result.returncode==expected,(args,result.stdout,result.stderr)
            return result
        contract=json.loads(module(['cnlookthrough.preflight','--contract']).stdout)
        assert contract['contract']==preflight['contract']
        blocked=root/'blocked.json'
        run(['run',str(sample),'--validate-only','--out',str(blocked)],2)
        assert not blocked.exists()
        args=['cnlookthrough.csv_import',str(examples/'holdings-import.csv'),'--config',str(examples/'holdings-import-config.json')]
        assert json.loads(module(args+['--validate-only']).stdout)['status']=='declared-fields-valid'
        imported=root/'imported.json'
        module(args+['--out',str(imported)])
        raw_hash=hashlib.sha256(imported.read_bytes()).hexdigest()
        module(args+['--out',str(imported)],2)
        assert hashlib.sha256(imported.read_bytes()).hexdigest()==raw_hash
        result=json.loads(run(['run',str(imported)]).stdout)
        assert abs(result['knownExposure']-.35)<1e-12 and abs(result['unknownExposure']-.65)<1e-12
        assert abs(result['unmappedStockIssuerExposure']-.15)<1e-12
        print(json.dumps(dict(repo=REPO,installed_demo=True,automatic_new_name=True,old_outputs_unchanged=True,source_working_directory=False)))

if __name__=='__main__':check()
