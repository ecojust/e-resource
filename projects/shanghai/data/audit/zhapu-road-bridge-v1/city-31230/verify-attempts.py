"""Bind each unsuccessful browser run to its original files and its later successful phase."""
from hashlib import file_digest
from pathlib import Path
import json,os,shutil

def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream,'sha256').hexdigest()
def document(path):
    return json.loads(path.read_bytes())
def history(run,public=None):
    run=Path(run);out=[];images=[]
    for phase in sorted((run/'attempts').iterdir()):
        for archived in sorted(phase.iterdir()):
            closed=archived/'closed.json'; rec=document(closed)
            assert rec['phase']==phase.name and rec['node_closed'] and rec['remaining']==[] and rec['node']>1
            assert rec['finished']>=rec['started'] and rec['driver_sha256']==digest(archived/'executed-driver.cjs')
            report=archived/('real-city.json' if phase.name.startswith('walk')else 'viewer.json'if phase.name=='standalone'else'report.json')
            if rec['report_sha256']:
                assert digest(report)==rec['report_sha256']
                observed=document(report)
            else:
                assert not report.exists()
                observed={}
            assert rec['exit']!=0 or not observed.get('passed')
            retry=run/'sessions'/phase.name;actual=document(retry/'closed.json')
            assert actual['exit']==0 and actual['node_closed']and actual['remaining']==[] and actual['chromium_pids']and actual['node']!=rec['node']
            assert actual['started']>=rec['finished'] and actual['prior_sha256']==rec['prior_sha256']
            assert actual['report_sha256']==digest(retry/report.name) and document(retry/report.name)['passed']
            for shot in [*observed.get('cases',[]),*observed.get('screenshots',[]),*observed.get('views',[])]:
                name=shot.get('filename',shot.get('file'));assert digest(archived/name)==shot['sha256']
            files={}
            for nested in sorted(archived.glob('component-*/process.json')):
                child=document(nested);assert child['node']>1 and child['driver_sha256']==rec['driver_sha256']
                if child['report_sha256']:
                    sub=nested.parent/'real-city.json';assert digest(sub)==child['report_sha256']
                    for shot in document(sub).get('cases',[]):assert digest(sub.parent/shot['file'])==shot['sha256']
            for f in sorted(archived.rglob('*')):
                if not f.is_file():continue
                rel=Path('attempts')/phase.name/archived.name/f.relative_to(archived);value=digest(f)
                if public is not None:
                    dest=Path(public)/rel;dest.parent.mkdir(exist_ok=True,parents=True)
                    if not dest.exists():
                        try:os.link(f,dest)
                        except OSError:shutil.copyfile(f,dest)
                    assert digest(dest)==value
                files[str(rel)]={'bytes':f.stat().st_size,'sha256':value}
                if f.suffix.lower() in ('.png','.jpg','.jpeg'):images.append(str(rel))
            out.append({'phase':phase.name,'attempt':archived.name,'exit_code':rec['exit'],'node':rec['node'],'chromium_pids':rec['chromium_pids'],'remaining':rec['remaining'],'exit_sha256':digest(closed),'report_sha256':rec['report_sha256'],'successful_retry_exit_sha256':digest(retry/'closed.json'),'successful_retry_report_sha256':actual['report_sha256'],'files':files})
    result={'order':230,'passed':True,'attempts':out,'images':images}
    if public is not None:
        index=Path(public)/'attempts/index.json';index.write_text(json.dumps(result,indent=2)+'\n')
    return result
if __name__=='__main__':
    import sys
    result=history(Path(__file__).resolve().parent,*sys.argv[1:])
    print(len(result['attempts']),len(result['images']))
