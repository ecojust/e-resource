"""Exercise Asia Realty's registered page after the genuine distant stage."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib, json, tempfile, shutil, sys, time, subprocess, os, fcntl
from psutil import Process, NoSuchProcess

case=Path('/tmp/shanghai-main-242/formal-31242')
project=Path('/workspace/e-resource/projects/shanghai')
out=case/'isolated-evidence/independent'
source=Path(__file__).resolve().parent
node_script=source/'verify-normal-page.cjs'
id_='huangpu-asia-realty-sichuan-front'
sha=lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
def now():return datetime.now(timezone.utc).isoformat()
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def valid_viewer(folder):
    rpt=read(folder/'viewer.json')
    assert rpt['passed'] and rpt['id']==id_ and rpt['base']=='http://127.0.0.1:31242/' and not rpt['errors']
    assert rpt['script_sha256']==sha(node_script)
    assert {(v['device'],v['role'],v['pose'])for v in rpt['views']}=={(d,r,k) for d in ['desktop','mobile']for r,k in [('full','front'),('full','oblique'),('lod','above')]}
    for v in rpt['views']:
        f=folder/v['file'];assert f.stat().st_size==v['bytes'] and sha(f)==v['sha256']
    assert set(rpt['downloads'])=={'raw','full','lod','native'}
    for role,item in rpt['downloads'].items():
        expected=manifest['assets'][role];f=folder/item['saved']
        assert item['saveAsVerified'] and sha(f)==expected['sha256']==item['sha256'] and f.stat().st_size==item['bytes']==expected['bytes']
    return rpt
distant=Path(sys.argv[1])
assert distant.resolve()==(case/'isolated-evidence/distant/closed.json').resolve()
d=read(distant);host_report=distant.parent/'main-browser.json'
assert d['exit_code']==0 and d['node_closed'] and d['node_pid'] and d['chromium_pids'] and d['remaining']==d['remaining_chromium']==[]
assert d['report_sha256']==sha(host_report) and read(host_report)['completed']
inputs=case/'242-production.json';bounds=read(inputs)['files']
manifestpath='assets/models/candidates/'+id_+'/manifest.json'
manifest=read(project/manifestpath)
assert sha(project/manifestpath)==bounds[manifestpath]
assert sha(project/manifest['viewer_page'])==bounds[manifest['viewer_page']]
out.mkdir(exist_ok=True)
with (out/'viewer.lock').open('a')as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    core=out/'closed.json'
    if core.is_file():
        c=read(core);assert c['passed'] and c['host_sha256']==sha(distant)
        assert c['report_sha256']==sha(out/'viewer.json')
        valid_viewer(out);sys.exit(0)
    attempts=out/'attempts';attempts.mkdir(exist_ok=True)
    folder=attempts/str(len(list(attempts.iterdir()))+1);folder.mkdir()
    started=now();observed={};left=[]
    with tempfile.TemporaryDirectory(prefix='asia-realty-242-',dir='/dev/shm')as temp:
        env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=temp,SHANGHAI_PROJECT_ROOT=str(project),SIGNED_INPUTS=str(inputs))
        with(folder/'node.log').open('wb')as log:
            child=subprocess.Popen(['node','-r',project/'data/audit/brunner-mond-v1/viewer-timeout.cjs',node_script,folder],cwd=project,env=env,stdout=log,stderr=log,start_new_session=True)
            while child.poll() is None:
                try:
                    for c in Process(child.pid).children(recursive=True):
                        try:
                            if c.name() in ('chromium','chrome'):observed[c.pid]=c.create_time()
                        except NoSuchProcess:pass
                except NoSuchProcess:pass
                time.sleep(.14)
        for pid,birth in observed.items():
            try:
                c=Process(pid)
                if c.create_time()==birth and c.status() not in ('dead','zombie'):left.append(pid)
            except NoSuchProcess:pass
        for f in Path('/proc').glob('[0-9]*/cmdline'):
            try:text=f.read_bytes()
            except OSError:continue
            if os.fsencode(temp) in text and b'chromium' in text:left.append(int(f.parent.name))
    report=folder/'viewer.json'
    rec=dict(order=242,stage='actual standalone',started=started,finished=now(),exit=child.returncode,exit_code=child.returncode,node_pid=child.pid,node_closed=child.poll() is not None,cdp_closed=not left,remaining=sorted(set(left)),chromium_pids=sorted(observed),chromium_birthtimes=observed,remaining_children=sorted(set(left)),remaining_chromium=sorted(set(left)),all_children_exited=not left,host_sha256=sha(distant),host_report_sha256=sha(host_report),script_sha256=sha(node_script),report=str(report),report_sha256=sha(report)if report.exists()else None,passed=False)
    write(folder/'closed.json',rec)
    assert child.returncode==0 and observed and not left, str(folder)
    rpt=valid_viewer(folder);rec['passed']=True
    for f in [report]+[folder/v['file'] for v in rpt['views']]+[folder/v['saved']for v in rpt['downloads'].values()]:
        alias=out/f.relative_to(folder);alias.parent.mkdir(exist_ok=True)
        if not alias.exists():os.link(f,alias)
        assert sha(alias)==sha(f)
    rec['report']=str(out/'viewer.json')
    rec['downloads']=rpt['downloads'];rec['views']=rpt['views']
    write(folder/'closed.json',rec);write(core,rec)
    print(sha(core),flush=True)
