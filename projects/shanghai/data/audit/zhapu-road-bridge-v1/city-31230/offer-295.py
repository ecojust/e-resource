"""Give the completed 230 control or phone interval to 295 after verifying its signed 294 inputs."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json,os,subprocess,sys,time
w=Path(__file__).parent;model=Path('/tmp/kiangsu-inn295');parent=Path('/tmp/guangdong306-294')
kind={'before':'native','phone':'viewer'}[sys.argv[1]]
read=lambda p:json.loads(p.read_bytes())
def digest(f):return sha256(f.read_bytes()).hexdigest()
def write(path,fields):
 if path.is_file():assert read(path)==fields;return
 tmp=path.with_suffix('.pending');tmp.write_text(json.dumps(fields,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,path)
stop=w/'sessions'/sys.argv[1]/'closed.json';rec=read(stop);report=stop.parent/'report.json'
assert rec['exit']==0 and rec['node_closed'] and rec['chromium_pids'] and not rec['remaining']
assert rec['report_sha256']==digest(report) and read(report)['passed']
proof=model/('native-closed.json' if kind=='native'else 'viewer-closed.json')
def verify_proof():
 data=read(proof);assert data['order']==295 and data['passed'] and data.get('exit',data.get('exit_code'))==0
 if kind=='native':
  assert data['remaining_blender']==[] and not data.get('remaining_oidn') and len(data['files'])==4
 else:
  assert data.get('remaining', data.get('remaining_chromium'))==[]
  count=lambda d:len(d)if isinstance(d,(list,dict))else d
  assert count(data['views'])==6 and count(data['downloads'])==4
 return data
if proof.is_file():verify_proof();raise SystemExit
raw=parent/'raw-294-confirmed.json';base_native=parent/'native-closed.json';admit=model/'handoff/admit-window.py'
required=[base_native,raw,admit]
if kind=='viewer':required.extend([parent/'viewer-closed.json',model/'native-closed.json',model/'raw-295-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/295-comparison.json')])
missing=[str(f)for f in required if not f.is_file()]
info=dict(order=295,host=230,phase=kind,previous_session=str(stop),previous_session_sha256=digest(stop),previous_browser_report_sha256=digest(report),remaining_chromium=[])
defer=w/f'295-{kind}-deferred.json'
if defer.is_file():
 d=read(defer)
 assert all(d.get(k)==v for k,v in info.items()) and d.get('deferred') and not d['blender_started'] and not d['chromium_started'] and d['missing']
 raise SystemExit

if missing:
 write(defer,{**info,'deferred':True,'blender_started':False,'chromium_started':False,'missing':missing});raise SystemExit
for f in [base_native]+([parent/'viewer-closed.json',model/'native-closed.json'] if kind=='viewer'else []):
 a=read(f);assert a['passed'] and a.get('exit',a.get('exit_code'))==0
for f,n in [(raw,294)]+([(model/'raw-295-confirmed.json',295)]if kind=='viewer'else []):
 a=read(f);assert a['order']==n and digest(Path(a['snapshot']))==a['sha256']
if kind=='viewer':
 formal=read(required[-1]);assert formal['passed'] and formal['order']==295
subprocess.run([sys.executable,'-B',admit,kind,stop],check=True)
accepted=model/'handoff'/(kind+'-window.json');assert accepted.is_file()
text=accepted.read_text();assert digest(stop) in text
write(w/f'295-{kind}-window.json',{**info,'authorized':True,'admission':str(accepted),'admission_sha256':digest(accepted)})
while not proof.is_file():
 if defer.is_file():
  d=read(defer);assert d['deferred']and not d.get('blender_started',False)and not d.get('chromium_started',False);raise SystemExit
 time.sleep(3)
verify_proof()
