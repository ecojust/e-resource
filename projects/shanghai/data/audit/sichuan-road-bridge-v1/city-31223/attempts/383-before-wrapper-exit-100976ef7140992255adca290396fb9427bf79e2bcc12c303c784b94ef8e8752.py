from pathlib import Path
import hashlib,json,time,subprocess,sys,fcntl
w=Path(__file__).parent;p=Path('/tmp/jianguo598-383/author/after-223.py');src=w/'sessions/standalone/closed.json';prev=Path('/tmp/anfu201-366/223-model-closed.json')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def rd(f):return json.loads(f.read_bytes())
while not (w/'366-checked-handback.json').exists():time.sleep(2)
assert sha(p)=='b3502d1c58a8de5520041233c590318f58ee514512953b9110daf0dc34682be7'
with (w/'render.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX);q=subprocess.run([sys.executable,'-Bu',p,src,prev])
    ret=Path('/tmp/jianguo598-383/223-first-study-closed.json');r=rd(ret)
    assert (r['order'],r['host'])==(383,223) and r['all_children_exited'] and r['remaining']==[]
    assert r['host_sha256']==sha(src) and r['host_report_sha256']==rd(src)['report_sha256'] and r['previous_sha256']==sha(prev)
    assert r['exit_code']==q.returncode and (not r['passed'] or sha(Path(r['result']))==r['result_sha256'])
    dst=w/'383-checked-handback.json';dst.write_text(json.dumps(dict(previous_sha256=sha(prev),returned=str(ret),returned_sha256=sha(ret),passed=r['passed'],exit_code=q.returncode),indent=2)+'\n')
