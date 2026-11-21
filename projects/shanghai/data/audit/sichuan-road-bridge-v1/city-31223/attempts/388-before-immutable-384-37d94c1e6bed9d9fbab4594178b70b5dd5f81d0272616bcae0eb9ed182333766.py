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
    assert h['physical_sha256']==sha(physical) and v['node_closed'] and v['remaining']==[] and (not h['passed'] or v['exit']==h['wrapper_exit']==0)
    entry=Path('/tmp/gao-an-63-study/first-geometry/start.py');assert sha(entry)=='c41d6a0f6395e34bb6230c1bb1e28b4239fd2ed8de2b9fe32da705cfd80d85e7'
    p=entry.with_name('returned.json')
    reused=p.exists()
    if not reused:
        cp=subprocess.run([sys.executable,'-Bu',entry,physical]);r=read(p)
        assert r['prior_sha256']==sha(physical) and r['exit_code']==cp.returncode
    else:
        r=read(p);old=Path(r['prior']).resolve(strict=True)
        anchor=Path('/tmp/jianguo-602-study/packed-exit.json')
        assert old==anchor and sha(old)==r['prior_sha256']
        old_exit=read(old);assert old_exit['all_children_exited'] and old_exit['remaining_children']==[]
    assert r['all_children_exited'] and r['remaining_children']==[]
    if r['passed']:
        proof=p.with_name('physical.json');data=read(proof)
        assert r['exit_code']==0 and sha(proof)==r['geometry_report_sha256'] and data['passed'] and data['all_children_exited'] and not data['remaining_children']
        assert set(data['mesh'])=={'full','lod'}
    dest=w/'388-checked-handback.json';dest.write_text(json.dumps(dict(source=str(physical),source_sha256=sha(physical),previous_sha256=sha(returned),actual_geometry_predecessor=r['prior'],actual_geometry_predecessor_sha256=r['prior_sha256'],reused_actual_result=reused,returned=str(p),returned_sha256=sha(p),passed=r['passed'],exit_code=r['exit_code']),indent=2)+'\n')
