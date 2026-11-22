"""Exercise the signed 31235 standalone page and observe its actual browser process tree."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,json,os,subprocess,time
import psutil
w=Path('/tmp/shanghai-main-235/formal-31235')
s=Path('/dev/shm/recovery235/formal-viewer')
driver=Path(__file__).with_name('actual-235-viewer.cjs')
assert hashlib.sha256(driver.read_bytes()).hexdigest()=='c156f823e20b9759bbd671b7d417433a97c52ad750a7f75253c3aa61bc8bcd69'
dest=w/'actual-31235-standalone'
dest.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def save(p,data):
    temp=p.with_suffix('.pending');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(p)
def validate(result):
    assert result['exit_code']==0 and result['all_children_exited'] and result['chromium_pids'] and not result['remaining_children']
    report=Path(result['report']);assert sha(report)==result['report_sha256']
    r=read(report);assert r['id']==ident and r['base']=='http://127.0.0.1:31235/' and r['passed'] and not r['pageErrors']
    assert r['manifestSHA256']==sha(s/'exact-inputs/assets/models/candidates'/ident/'manifest.json')
    assert r['scriptSHA256']==sha(driver) and len(r['views'])==6 and set(r['downloads'])=={'raw','full','lod','native'}
    for v in r['views']:assert sha(report.parent/v['filename'])==v['sha256']
    for value in r['downloads'].values():
        f=report.parent/value['saved'];assert value['saveAsVerified'] and sha(f)==value['sha256'] and f.stat().st_size==value['bytes']
    return r
ident='huangpu-mitsui-bussan-pediment-front'
close=w/'isolated-evidence/distant/closed.json';hc=read(close);assert hc['order']==235 and hc['exit_code']==0 and hc['cdp_closed'] and hc['remaining_chromium']==[] and sha(Path(hc['report']))==hc['report_sha256']
prior=Path('/tmp/blackstone361/development-native/235-development-returned.json');prev=read(prior)
assert prev['order']==361 and prev['host_sha256']==sha(close) and prev['all_children_exited'] and prev['remaining_children']==[] and sha(Path(prev['physical']))==prev['physical_sha256']
with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    end=dest/'closed.json'
    if end.exists():
        validate(read(end));raise SystemExit(0)
    folder=dest/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder.mkdir()
    temp=s/'profile';temp.mkdir(exist_ok=True)
    env={**os.environ,'TMPDIR':str(temp),'MODEL_BASE_URL':'http://127.0.0.1:31235/','SHANGHAI_PROJECT_ROOT':str(s/'exact-inputs'),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
    begin=now();children={};report=folder/'viewer.json'
    with (folder/'run.log').open('xb') as log:
        p=subprocess.Popen(['node',driver,ident,folder],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        while p.poll() is None:
            try:
                for x in psutil.Process(p.pid).children(recursive=True):
                    try:children[x.pid]={'name':x.name(),'birth':x.create_time()}
                    except psutil.Error:pass
            except psutil.Error:pass
            time.sleep(.12)
    def live(pid,v):
        try:
            c=psutil.Process(pid);return c.create_time()==v['birth'] and c.status()!=psutil.STATUS_ZOMBIE
        except psutil.Error:return False
    for _ in range(30):
        left=[pid for pid,x in children.items() if live(pid,x)]
        if not left:break
        time.sleep(.12)
    result=dict(order=235,phase='standalone',started=begin,finished=now(),exit_code=p.returncode,node_pid=p.pid,node_closed=p.poll() is not None,chromium_pids=[pid for pid,x in children.items() if x['name'] in ('chrome','chromium')],process_births=children,remaining_children=left,remaining_chromium=left,all_children_exited=not left,host_sha256=sha(close),host_report_sha256=hc['report_sha256'],previous_sha256=sha(prior),driver_sha256=sha(driver),report=str(report),report_sha256=sha(report) if report.exists() else None)
    save(folder/'process-exit.json',result);r=validate(result)
    result.update(passed=True,views=6,downloads=4,actual_saved_downloads=r['downloads']);save(end,result)
