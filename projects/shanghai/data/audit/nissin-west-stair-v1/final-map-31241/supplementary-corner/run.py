"""Physically revisit both Bund 5 corner views after a real city or model session has closed."""
import fcntl,hashlib,json,os,subprocess,sys,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
city=Path('/tmp/shanghai-main-241');sys.path.insert(0,str(city))
import sequence as control
app=Path(__file__).resolve().parent
out=Path('/dev/shm/grace241-city/corner-street-level')
out.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_bytes())
def digest(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def put(p,record):
    tmp=p.with_suffix('.new');tmp.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
if __name__=='__main__':
    gate=Path(sys.argv[1]);g=read(gate)
    assert g['exit_code']==0 and (g.get('remaining_children')==[] or g.get('remaining_chromium')==[]),gate
    with (out/'run.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for phase in ('old-corner','corner'):
            old=control.verify_closed(phase)
            d=out/phase;d.mkdir(exist_ok=True)
            if (d/'closed.json').is_file():
                prior=read(d/'closed.json')
                assert prior['exit_code']==0 and prior['report_sha256']==digest(d/'browser.json')
                continue
            assert not(d/'browser.json').exists()
            with (d/'stdout.log').open('wb')as stream,tempfile.TemporaryDirectory(prefix='b5c-',dir='/dev/shm')as tmp:
                env=dict(os.environ,TMPDIR=tmp,CORNER_SUPPLEMENT=str(out),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
                start=now()
                proc=subprocess.Popen(['node',app/'corner.cjs',phase],env=env,cwd=app,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                seen={}
                while proc.poll()is None:
                    seen.update(control.process_group(proc.pid));time.sleep(.28)
                for i in range(45):
                    if not control.alive(seen):break
                    time.sleep(.24)
                remaining=control.alive(seen);chrome={pid for pid,state in seen.items() if state[1]in('chrome','chromium')}
                rr=d/'browser.json'
                record=dict(order=241,phase=phase,source=str(gate),source_sha256=digest(gate),original_report_sha256=old['report_sha256'],original_exit_sha256=digest(city/'evidence'/phase/'closed.json'),pid=proc.pid,exit_code=proc.returncode,node_closed=not control.alive({proc.pid:seen[proc.pid]}),chromium_pids=sorted(chrome),remaining_children=remaining,remaining_chromium=sorted(chrome&set(remaining)),all_children_exited=not remaining,started=start,finished=now(),driver_sha256=digest(app/'corner.cjs'),report=str(rr),report_sha256=digest(rr)if rr.is_file()else None)
                put(d/'closed.json',record)
                assert proc.returncode==0 and chrome and not remaining and read(rr)['completed']
            print(phase,record['report_sha256'],flush=True)
