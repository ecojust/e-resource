from pathlib import Path
import hashlib,json,os,time,errno
w=Path(__file__).parent;plan=json.loads((w/'cache-source-plan.json').read_bytes());base='ae55637ce1d7cbc4d21fd94934c8309aca1dcd09'
roots=[Path(f'/tmp/shanghai-additional-inputs-{n}/server-cache/{base}/objects')for n in [15138,17138]]
for r in plan:
 for cache in roots:
  dest=cache/r['rel'];peer=Path(r['verified_peer'])if r['verified_peer'] else w/'prior-objects'/r['git_blob']
  b=peer.read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_blob']
  if dest.is_file():
   assert dest.read_bytes()==b;continue
  while True:
   try:
    dest.parent.mkdir(exist_ok=True,parents=True)
    if dest.parent.stat().st_dev==peer.stat().st_dev:os.link(peer,dest)
    else:dest.symlink_to(peer)
    break
   except FileExistsError:assert dest.read_bytes()==b;break
   except OSError as e:
    if e.errno!=errno.ENOSPC:raise
    time.sleep(.35)
 print(r['rel'],flush=True)
