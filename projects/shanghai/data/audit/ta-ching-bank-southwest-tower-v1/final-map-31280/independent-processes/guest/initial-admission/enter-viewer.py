"""Resume the same actual phone authoring window after both city receipts exist."""
from pathlib import Path
import fcntl, hashlib, json, os, shutil, subprocess, sys, time
w=Path('/tmp/anhe345');h=Path('/tmp/shanghai-main-280');g=w/'mapping/handoff'
phone=h/'final-map-31280/phone/process.json';last=Path('/tmp/shanghai-yongjia-porch/scenes/345-comparison.json')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
with (w/'second-viewer-offer.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if (w/'viewer-closed.json').is_file():sys.exit(0)
 while not (last.is_file() and (w/'raw-345-confirmed.json').is_file()):time.sleep(5)
 raw=read(w/'raw-345-confirmed.json');final=read(last);assert raw['catalog_sha256']==final['catalog_sha256'] and final['passed'] and final['port']==31345
 assert read(phone)['exit_code']==0
 saved=h/'345-attempts'/'initial-viewer';saved.mkdir(parents=True,exist_ok=True)
 old=w/'280-viewer-deferred.json';res=h/'345-viewer-result.json'
 if old.is_file():
  assert read(old)['deferred'] and not read(old)['attempted'] and read(old)['host_receipt_sha256']==sha(phone)
  assert res.is_file() and read(res)['result_sha256']==sha(old)
  for f in [res,old]:
   dest=saved/f.name
   if dest.is_file():assert sha(dest)==sha(f)
   else:shutil.copyfile(f,dest)
  for f in [res,old]:f.unlink()
 subprocess.run([sys.executable,'-Bu',h/'offer-345-live.py','viewer',phone],check=True)
 result=read(h/'345-viewer-result.json');print(result,flush=True)
 assert Path(result['result']).name=='viewer-closed.json'
