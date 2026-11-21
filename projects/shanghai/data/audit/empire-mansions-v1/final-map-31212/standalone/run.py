"""Run the 31212 independent page after its last completed physical city phase."""
from pathlib import Path
from datetime import datetime, timezone
import fcntl, hashlib, json, os, shutil, subprocess, sys, tempfile, time, psutil
W=Path(__file__).resolve().parent
DIST=Path('/tmp/shanghai-main-212/final-map-31212/distant')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def main(gate):
    assert gate==DIST/'process.json'
    g=read(gate);report=DIST/'main-browser.json';data=read(report)
    assert g['phase']=='distant' and g['exit_code']==0 and g['node_closed'] and g['node_pids'] and g['chromium_pids']
    assert g['remaining_children']==g['remaining_chromium']==[] and g['report_sha256']==sha(report)
    assert data['completed'] and data['id']=='xuhui-empire-mansions-street-front'
    config=read(W/'inputs.json')
    for p,h in config['files'].items():assert sha(Path(p))==h,p
    with (W/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        closed=W/'closed.json'
        if closed.exists():
            prior=read(closed);assert prior['passed'] and prior['host_sha256']==sha(gate) and prior['report_sha256']==sha(Path(prior['report']));return
        disks=list(dict.fromkeys([Path('/tmp'),Path('/dev/shm'),Path('/run/lock')]))
        largest=max(disks,key=lambda p:shutil.disk_usage(p).free)
        with tempfile.TemporaryDirectory(prefix='empire212-browser-',dir=largest) as temp:
            target=largest/('empire212-standalone-'+str(time.time_ns()));target.mkdir()
            out=W/'observed'
            if out.exists() or out.is_symlink():out.rename(W/('prior-'+str(time.time_ns())))
            out.symlink_to(target)
            env=dict(os.environ,TMPDIR=temp,PLAYWRIGHT_DOWNLOAD_DIR=temp,MODEL_BASE_URL=config['origin'],NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
            started=now();seen={}
            with (target/'run.log').open('w')as log:
                proc=subprocess.Popen(['node',str(W/'viewer.cjs'),config['id'],str(target)],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                parent=psutil.Process(proc.pid)
                while proc.poll() is None:
                    try:children=parent.children(recursive=True)
                    except psutil.NoSuchProcess:children=[]
                    for child in children:
                        try:
                            if 'chrom' in child.name().lower():seen[(child.pid,child.create_time())]=child.name()
                        except psutil.NoSuchProcess:pass
                    time.sleep(.06)
            rc=proc.returncode
            def live():
                survivors=[]
                for pid,birth in seen:
                    try:
                        child=psutil.Process(pid)
                        if child.create_time()==birth and child.status()!=psutil.STATUS_ZOMBIE:survivors.append(pid)
                    except psutil.NoSuchProcess:pass
                return survivors
            for _ in range(100):
                if not live():break
                time.sleep(.05)
            rp=target/'viewer.json'
            ck=dict(order=212,exit=rc,exit_code=rc,passed=False,host=str(gate),host_sha256=sha(gate),host_report_sha256=sha(report),node_pid=proc.pid,node_closed=proc.poll() is not None,chromium_pids=sorted({pid for pid,_ in seen}),remaining_chromium=live(),started=started,finished=now(),log_sha256=sha(target/'run.log'),input_sha256=sha(W/'inputs.json'))
            save(target/'process.json',ck)
            assert rc==0 and seen and not ck['remaining_chromium'] and rp.is_file(),ck
            actual=read(rp);assert actual['passed'] and actual['base']==config['origin'] and actual['id']==config['id'] and len(actual['views'])==6
            for v in actual['views']: assert sha(target/v['filename'])==v['sha256']
            assert set(actual['downloads'])==set(config['downloads'])
            for k,v in actual['downloads'].items():
                assert v['saved_file_released'] and v['clicked'] and v['sha256']==config['downloads'][k]['sha256'] and v['bytes']==config['downloads'][k]['bytes']
            ck.update(passed=True,report=str(rp),report_sha256=sha(rp),views=actual['views'],downloads=actual['downloads'])
            save(target/'process.json',ck);save(closed,ck)
if __name__=='__main__':main(Path(sys.argv[1]))
