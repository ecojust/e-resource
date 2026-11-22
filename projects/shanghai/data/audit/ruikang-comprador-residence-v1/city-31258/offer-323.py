"""Release the native or standalone slot after its own successful, verifiable city process exit."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
W=Path(__file__).parent;kind=sys.argv[1];assert kind in ('native','viewer')
host='before' if kind=='native' else 'phone'
exit_file=W/'evidence'/host/'closed.json'
P=Path('/tmp/changshu322')
def read(p):return json.loads(p.read_bytes())
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):
 data=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
 if p.exists():assert p.read_bytes()==data;return
 tmp=p.with_suffix('.new');tmp.write_bytes(data);tmp.replace(p)
r=read(exit_file);report=Path(r['report']);assert r['order']==258 and r['phase']==host and r['exit']==r['exit_code']==0 and r['node_closed'] and r['chromium_pids'] and r['remaining']==r['remaining_chromium']==[]
assert sha(report)==r['report_sha256'] and read(report)['completed'] and read(report)['section']==host
from window_ticket import existing_result
if existing_result(W,kind,exit_file,report) is not None:sys.exit(0)
bind=W/'guest-323.json'
G=Path(read(bind)['admit']).resolve().parents[2] if bind.is_file() else None
needed=[bind,P/'native-closed.json',P/'raw-322-confirmed.json']
if kind=='viewer' and G is not None:needed.extend([P/'viewer-closed.json',G/'native-closed.json',G/'raw-323-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/323-comparison.json')])
meta=dict(order=323,host=258,phase=kind,host_closed=str(exit_file),host_closed_sha256=sha(exit_file),host_report_sha256=sha(report))
missing=[str(f)for f in needed if not f.is_file()]
if missing:
 write(W/f'323-{kind}-deferred.json',dict(**meta,deferred=True,missing=missing,remaining=[],native_started=False,viewer_started=False));sys.exit(0)
b=read(bind);assert b['order']==323 and b['host']==258
for key in ['admit','dispatch','author']:assert sha(Path(b[key]))==b[key+'_sha256']
def count(v):return len(v) if isinstance(v,(list,dict))else v
def closed(p,n,mode):
 v=read(p);assert v['order']==n and v['passed'] and v.get('exit',v.get('exit_code'))==0
 k='remaining_blender'if mode=='native'else'remaining_chromium'
 assert k in v or 'remaining' in v
 assert not v.get('remaining') and not v.get(k)
 if mode=='native':
  assert len(v.get('assets',v.get('files',[])))==4 and (v.get('blender_pids')or v.get('native_stages')or v.get('wrapper_closed')or v.get('all_processes_closed'))
 else:assert (v.get('chromium_pids')or v.get('processes')) and count(v['views'])==6 and count(v['downloads'])==4
closed(needed[1],322,'native')
for n,p in [(322,needed[2])]+([(323,G/'raw-323-confirmed.json')]if kind=='viewer'else []):
 v=read(p);assert v['order']==n and sha(Path(v['snapshot']))==v['sha256']
if kind=='viewer':
 closed(P/'viewer-closed.json',322,'viewer');closed(G/'native-closed.json',323,'native')
 assert read(needed[-1])['passed']
from guest_result import verify
out=G/(kind+'-closed.json')
deferred=G/f'258-{kind}-deferred.json'
failed=G/f'258-{kind}-failed.json'
if not out.exists() and not (failed.is_file() and read(failed).get('host_receipt_sha256')==sha(exit_file)):
 matches_previous=deferred.is_file() and read(deferred).get('source_sha256')==sha(exit_file)
 if not matches_previous:
  admitted=subprocess.run([sys.executable,'-Bu',b['admit'],kind,str(exit_file)])
  if admitted.returncode:
   matching_failure=failed.is_file() and read(failed).get('host_receipt_sha256')==sha(exit_file)
   if not matching_failure:raise RuntimeError(f'323 {kind} admission exited {admitted.returncode} without a closed failure receipt')
if out.exists():
 closed(out,323,kind)
 assert verify(kind,exit_file,out)=='complete'
 write(W/f'323-{kind}-returned.json',dict(**meta,passed=True,actual_receipt=str(out),sha256=sha(out),dispatch_sha256=b['dispatch_sha256']))
else:
 if failed.is_file() and read(failed).get('host_receipt_sha256')==sha(exit_file):deferred=failed
 result=verify(kind,exit_file,deferred)
 assert result in ('deferred-before-launch','deferred-after-physical-exit')
 v=read(deferred)
 attempt={k:v[k] for k in ('launch_process','launch_process_sha256','launch_log','launch_log_sha256','child_exit','exit') if k in v}
 write(W/f'323-{kind}-deferred.json',dict(**meta,deferred=True,completed=False,started=v['started'],attempted=v['attempted'],guest_outcome=result,actual_receipt=str(deferred),sha256=sha(deferred),dispatch_sha256=b['dispatch_sha256'],remaining=[],**attempt))
