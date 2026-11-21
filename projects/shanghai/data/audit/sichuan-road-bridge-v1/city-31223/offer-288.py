from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
w=Path(__file__).parent;prior=Path('/tmp/swire287');model=Path('/tmp/huangpu-theater288')
r=lambda p:json.loads(p.read_bytes())
def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):
 if p.exists():assert r(p)==d;return
 temp=p.with_suffix('.pending');temp.write_text(json.dumps(d,indent=2)+'\n');temp.replace(p)
phase=sys.argv[1];kind={'before':'native','phone':'viewer'}[phase]
closed=w/'sessions'/phase/'closed.json';report=closed.parent/'report.json';c=r(closed)
assert c['exit']==0 and c['node_closed']and not c['remaining']and c['chromium_pids']and digest(report)==c['report_sha256']and r(report)['passed']
native=prior/'native-closed.json';raw=prior/'raw-287-confirmed.json';previous_viewer=prior/'independent-closed.json';new_raw=model/'raw-288-confirmed.json';new_native=model/'native-closed.json';new_viewer=model/'viewer-closed.json'
need=[native,raw]+([previous_viewer,new_native,new_raw,Path('/tmp/shanghai-yongjia-porch/scenes/288-comparison.json')]if kind=='viewer'else[])
proof=new_native if kind=='native'else new_viewer
def verify_proof():
 a=r(proof);assert a['passed']and a['exit']==0 and a['order']==288 and a['remaining']==[]
 if kind=='native':assert a['wrapper_closed']and a['blender_pids'] and len(a['assets'])==4
 else:assert a['chromium_pids']and a['node']and a['receipt_sha256']
info={'order':288,'phase':kind,'previous':str(closed),'previous_sha256':digest(closed),'report_sha256':digest(report),'remaining_chromium':[]}
if proof.exists():verify_proof();save(w/f'288-{kind}-complete-before-window.json',{**info,'proof_sha256':digest(proof)});raise SystemExit
missing=[str(p)for p in need if not p.is_file()]
if missing:save(w/f'288-{kind}-deferred.json',{**info,'missing':missing});raise SystemExit
parent=r(raw)
assert parent['order']==287 and digest(Path(parent['snapshot']))==parent['sha256']and Path(parent['root']).is_dir()
assert r(native)['exit']==0 and not r(native).get('remaining')
if kind=='viewer':
 assert r(previous_viewer)['exit']==0 and not r(previous_viewer).get('remaining')
 manifest=r(new_raw);assert manifest['order']==288 and digest(Path(manifest['snapshot']))==manifest['sha256']
 assert r(new_native)['exit']==0 and r(need[-1])['passed']
admit=model/'mapping/handoff/admit-window.py'
subprocess.run([sys.executable,'-B',admit,kind,closed],check=True)
entry=model/'mapping/handoff'/(kind+'-window.json');assert r(entry)['sha256']==digest(closed)
save(w/f'288-{kind}-window.json',{**info,'authorized':True,'admission_sha256':digest(entry)})
defer=w/f'288-{kind}-author-deferred.json'
while not proof.is_file():
 if defer.exists():assert r(defer)['deferred']and r(defer)['admission_sha256']==digest(entry)and r(defer)['reason'];raise SystemExit
 time.sleep(3)
verify_proof()
