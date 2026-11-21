from pathlib import Path
import time,json,hashlib,sys,fcntl,subprocess
w=Path(__file__).parent;stage=w/'sessions/walk-desktop';returned=w/'288-supplemental-handback.json'
def read(f):return json.loads(f.read_bytes())
def sha(f):
    with f.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
while not (stage/'run.log').exists():time.sleep(.25)
time.sleep(2.5)
with (w/'render.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    c=read(stage/'closed.json');assert c['node_closed'] and c['remaining']==[]
    if c['exit'] or not read(stage/'real-city.json')['passed']:sys.exit('Desktop walk needs a real successful replay')
    if not returned.is_file():sys.exit('The 288 independent page was not handed back')
    h=read(returned);physical=Path(h['physical']);v=read(physical)
    assert h['physical_sha256']==sha(physical) and v['node_closed'] and v['remaining']==[] and v['exit']==h['wrapper_exit']
    entry=Path('/tmp/gao-an-63-study/first-geometry/start.py');assert sha(entry)=='c41d6a0f6395e34bb6230c1bb1e28b4239fd2ed8de2b9fe32da705cfd80d85e7'
    cp=subprocess.run([sys.executable,'-Bu',entry,physical]);p=entry.with_name('returned.json');r=read(p)
    assert r['prior_sha256']==sha(physical) and r['all_children_exited'] and r['remaining_children']==[] and r['exit_code']==cp.returncode
    dest=w/'388-checked-handback.json';dest.write_text(json.dumps(dict(source=str(physical),source_sha256=sha(physical),previous_sha256=sha(returned),returned=str(p),returned_sha256=sha(p),passed=r['passed'],exit_code=cp.returncode),indent=2)+'\n')
