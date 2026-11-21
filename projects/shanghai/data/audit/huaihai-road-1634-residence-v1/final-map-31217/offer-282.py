"""Offer the actual preceding 217 browser exit to the Nankin Road residence stair bay."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
w=Path(__file__).parent
child=Path('/tmp/hankou-garden-hotel282')
parent=Path('/tmp/palace219-281')
read=lambda p:json.loads(p.read_bytes())
def sha(p):
 with p.open('rb')as fp:return hashlib.file_digest(fp,'sha256').hexdigest()
def write(p,obj):
 if p.exists():assert read(p)==obj;return
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
phase=sys.argv[1];kind={'before':'native','phone':'viewer'}[phase]
closed=w/phase/'process.json';report=w/phase/('control-browser.json' if phase=='before'else'main-browser.json');c=read(closed)
assert c['phase']==phase and c['exit_code']==0 and c['node_closed'] and c['chromium_pids'] and not c['remaining_children'] and not c['remaining_chromium']
assert c['report_sha256']==sha(report) and read(report)['completed']
done=child/(kind+'-closed.json');base={'order':282,'city':217,'phase':kind,'closure':str(closed),'closure_sha256':sha(closed),'report_sha256':sha(report)}
def verify():
 d=read(done);assert d.get('order',282)==282 and d.get('exit',d.get('exit_code'))==0 and d.get('passed',True) and not any(d.get(k)for k in ('remaining','remaining_chromium','remaining_blender','remaining_children'))
 if kind=='native':assert len(d.get('files',d.get('assets',{})))==4
if done.exists():verify();write(w/f'282-{kind}-already-completed.json',{**base,'actual_sha256':sha(done)});raise SystemExit
needed=[parent/'native-closed.json',parent/'raw-281-confirmed.json']
if kind=='viewer':needed += [parent/'viewer-closed.json',child/'native-closed.json',child/'raw-282-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/282-comparison.json')]
missing=[str(x)for x in needed if not x.is_file()]
if missing:
 write(w/f'282-{kind}-deferred.json',{**base,'deferred':True,'missing':missing,'blender_started':False,'browser_started':False});raise SystemExit
for x in needed:
 d=read(x)
 if x.name.startswith('raw-'):assert d['passed'] and sha(Path(d['snapshot']))==d['sha256']
 elif x.name.endswith('-closed.json'):assert d.get('exit',d.get('exit_code'))==0 and not any(d.get(k) for k in ('remaining','remaining_chromium','remaining_blender'))
 else:assert d['passed']
subprocess.run([sys.executable,'-B',child/'handoff/admit-window.py',kind,closed],check=True)
grant=child/'handoff'/(kind+'-window.json');assert read(grant)['sha256']==sha(closed)
write(w/f'282-{kind}-admitted.json',{**base,'admission_sha256':sha(grant)})
while not done.is_file():time.sleep(3)
verify()
