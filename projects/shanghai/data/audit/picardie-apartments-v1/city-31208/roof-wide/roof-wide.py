"""Inspect the stepped roof with a wider view that leaves space for the public map controls."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,tempfile,time
from process_family import chrome_descendants,still_alive
q=Path(__file__).resolve().parent
root=Path((q/'evidence-root.txt').read_text().strip())
independent=root/'independent/closed.json'
assert json.loads(independent.read_bytes())['passed']
p=Path('/workspace/e-resource/projects/shanghai')
out=root/'roof-wide';out.mkdir(exist_ok=True)
def sha(path):return hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
read=lambda path:json.loads(path.read_bytes())
if (out/'physical.json').exists():
 prior=read(out/'physical.json');assert prior['exit_code']==0 and prior['sha256']==sha(out/'main-browser.json');raise SystemExit(0)
assert not (out/'main-browser.json').exists()
now=lambda:datetime.now(timezone.utc).isoformat()
base=max(map(Path,['/run/codex-docker/user','/dev/shm','/tmp']),key=lambda path:shutil.disk_usage(path).free)
with tempfile.TemporaryDirectory(prefix='p208-wide-',dir=base)as prof:
 env={**os.environ,'TMPDIR':prof,'MODEL_BASE_URL':'http://127.0.0.1:31208/','SHANGHAI_PROJECT_ROOT':str(q/'208'),'QA_OUTPUT_DIR':str(out)}
 with (out/'run.log').open('wb')as log:
  start=now();proc=subprocess.Popen(['node',q/'check-roof-wide.cjs',p/'data/audit/picardie-apartments-v1/map-case.json','--roof'],env=env,stdout=log,stderr=log,start_new_session=True);seen={}
  while proc.poll() is None:
   seen.update(chrome_descendants(proc.pid));time.sleep(.22)
 still=still_alive(seen)
 result=dict(name='roof-wide',pid=proc.pid,started_utc=start,finished_utc=now(),exit_code=proc.returncode,observed_chromium_pids_and_starttime=seen,remaining_chromium=still,report='main-browser.json',sha256=sha(out/'main-browser.json') if (out/'main-browser.json').exists()else None,driver_sha256=sha(q/'check-roof-wide.cjs'))
 (out/'physical.json').write_text(json.dumps(result,indent=2)+'\n')
 assert proc.returncode==0 and seen and not still,result
j=read(out/'main-browser.json');assert j['completed'] and not j['errors'] and not j['failed']
v,=j['views'];im,=j['screenshots'];assert v['viewport']==[910,750] and v['view']=='map-roof-wide' and v['glError']==0 and not v['contextLost']
assert sha(out/im['file'])==im['sha256']
