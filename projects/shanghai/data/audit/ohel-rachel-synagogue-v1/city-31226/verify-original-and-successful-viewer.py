"""Validate the real pre-launch failure and the two documented developmental guest failures."""
import hashlib,json
from pathlib import Path
from datetime import datetime
def h(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def j(p):return json.loads(Path(p).read_bytes())
def verify_guest(audit,n,names):
 assert n==226
 a=Path(audit);f=a/'final-map-31226';i=f/'independent';d=i/'attempt-01-before-browser'
 expected={d/'closed.json':h('/dev/shm/k226f/closed.json'),d/'official-page.cjs':'116c1db967676edc37c754e9390f706da6834a733bdd8137146a93b465f289ba',d/'run.log':'0616b7b7c4d4ae7374094c70b26698a5af8222f5c2994cade59330bb6f6e8dbd',i/'official-page.cjs':'cea30cee3cbfa59602ddee8a4ccb693610c60d0012a2e3d0b52eceb3b2ad2db6',i/'viewer.json':'c962ad4096acfbce9f866370beadf3f55617675aac892fc67f4e54879e99a06b',i/'run.log':hashlib.sha256(b'').hexdigest()}
 assert all(p.relative_to(a).as_posix() in names and h(p)==v for p,v in expected.items())
 err=j(d/'closed.json');good=j(i/'closed.json');viewer=j(i/'viewer.json')
 assert err['exit']==1 and err['node_closed'] and err['all_children_exited'] and err['remaining_children']==err['chromium_pids']==[] and err['report_sha256'] is None
 assert err['log_sha256']==h(d/'run.log') and err['driver_sha256']==h(d/'official-page.cjs') and 'ReferenceError: browser is not defined' in (d/'run.log').read_text()
 assert datetime.fromisoformat(err['finished']) < datetime.fromisoformat(good['started'])
 assert good['exit_code']==0 and good['all_children_exited'] and good['remaining_children']==[] and len(good['chromium_pids'])==2 and good['report_sha256']==h(i/'viewer.json') and good['log_sha256']==h(i/'run.log') and good['driver_sha256']==h(i/'official-page.cjs')
 assert viewer['passed'] and len(viewer['views'])==6 and len(viewer['downloads'])==4 and viewer['base']=='http://127.0.0.1:31226/' and all(h(i/v['filename'])==v['sha256'] for v in viewer['views'])
 assert all(v['file']==v['savedAs'] for v in viewer['downloads'].values())
 allow={d/'closed.json',i/'run.log'}
 for n,failed_hash,success_hash in ((380,'95fd46377382ad3cfb5b32a27718e7f2f2ebbac7137c3dcfd2c9eb54590ff878','3b6b321eec1196881571ac31755c0910a83c65e6aefac53a73dcb9ba2a7b5f71'),(396,'047a1c5de6bfba46ddfca77af2523d2b2c544060e4d81010938828793bd7b806','1ff6a1b7ae39ef8c580aa1036d47e05209b923cacf1d97ee083abde74d23d87a')):
  ret=f/(str(n)+'-development-returned.json');v=j(ret);assert v['order']==n and v['host']==226 and v['passed'] is False and v['exit_code']==1 and v['all_children_exited'] and v['remaining_children']==[]
  assert v['physical_sha256']==failed_hash==h(v['physical']);failed=j(v['physical']);assert failed['exit_code']==1 and not failed['passed'] and failed['all_children_exited'] and failed['remaining_children']==[]
  replacement=('/dev/shm/p38/development-native/physical.json' if n==380 else '/tmp/zikawei-396-architecture/development-native/recovered-226/physical.json')
  assert h(replacement)==success_hash;ok=j(replacement);assert ok['exit_code']==0 and ok['passed'] and ok['all_children_exited'] and ok['remaining_children']==[]
  assert ret.relative_to(a).as_posix() in names
  allow.add(ret)
 return allow
