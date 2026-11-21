import hashlib,json,sys,subprocess,os
from pathlib import Path
w=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=lambda p:json.loads(p.read_bytes())
def save(f,x):
 tmp=f.with_suffix('.pending');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(f)
def active(pid):
 fs=Path('/proc')/str(pid)/'stat'
 if not fs.exists():return False
 return fs.read_text().rsplit(')',1)[1].split()[0] not in ('Z','X')
src=w/'sessions/desktop/failed-exit.json';q=r(src)
assert q['exit_code'] and q['node_closed'] and q['cdp_closed'] and not q['remaining_chromium'] and not any(map(active,[q['node_pid'],*q['chromium_pids']])) and q['report_sha256']==sha(Path(q['report']))
e=w/'independent-author-window-218.json'
save(e,dict(order=218,all_children_exited=True,remaining_children=[],map_passed=False,previous=src.as_posix(),previous_sha256=sha(src),report_sha256=q['report_sha256'],end=q['end'],node_pid=q['node_pid'],chromium_pids=q['chromium_pids']))
p=Path('/tmp/hujiang352-research/run-packed.py')
assert sha(p)=='db9dcfb4fdfd45233f48ee803d396581166d1d64ae1cc7be7f4b8c6f9b12dc43'
x=subprocess.run([sys.executable,'-B',p,e]);ret=p.parent/'packed-exit.json';z=r(ret)
assert z['prior_sha256']==sha(e) and x.returncode==z['exit_code'] and z['all_children_exited'] and not z['remaining_children']
save(w/'352-cpu-return.json',dict(program_sha256=sha(p),actual_return=str(ret),sha256=sha(ret),exit_code=x.returncode,remaining=[],independent_map_exit=str(e),independent_map_exit_sha256=sha(e)))
subprocess.run([sys.executable,'-B',w/'after-352-physical.py'],check=True)
