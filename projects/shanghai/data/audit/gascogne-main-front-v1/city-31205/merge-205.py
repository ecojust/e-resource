"""Join the completed physical public interactions and asset receipts."""
from pathlib import Path
import json,hashlib,os,shutil,subprocess,sys
w=Path(__file__).parent;h=w/'evidence/205';parts=h/'separate';dest=h/'after';root=Path('/workspace/e-resource/projects/shanghai/data/audit/gascogne-main-front-v1/city-31205')
read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():
  try:os.link(src,dst)
  except OSError:shutil.copyfile(src,dst)
 assert sha(src)==sha(dst)
def save(f,d):
 f.parent.mkdir(exist_ok=True,parents=True);f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
entry_closed=parts/'entry/closed.json'
if not entry_closed.exists():
 subprocess.run([sys.executable,'-Bu',w/'run-205-separated.py',w/'204-real-exits.json','entry'],check=True)
data={};receipts={}
for i in ['before','desktop','phone','details','touch','architecture','roof','closeups','bands','entry','distant']:
 control=i=='before';q=h/'before'if control else parts/i;f=q/('control-browser.json'if control else'main-browser.json');cl=q/'closed.json';d=read(f);c=read(cl)
 assert d['section']==i and d['completed'] and not d['errors'] and not d['failed'] and not d.get('failure')
 assert c['report_sha256']==sha(f) and c['driver_sha256']==d['scriptSha256']==sha(w/'driver-versions'/c['driver_sha256']/'check-205-separated.cjs') and c['exit']==0 and c['node_closed']and not c['remaining']
 copy(f,root/'sessions'/i/f.name);copy(cl,root/'sessions'/i/cl.name)
 if control:continue
 for v in d['screenshots']:
  assert v['sha256']==sha(q/v['file']);copy(q/v['file'],dest/v['file'])
 receipts[i]=c;data[i]=d
d=dict(data['details'])
d['executedDriverVersions']={name:entry['scriptSha256'] for name,entry in data.items()}
for name, entry in data.items():
 copy(w/'driver-versions'/entry['scriptSha256']/'check-205-separated.cjs',root/'driver-versions'/entry['scriptSha256']/'check-city.cjs')
for k in ['catalog','id','caseSha256','bindings','server']:
 assert all(x[k]==d[k]for x in data.values())
for field in ['views','screenshots']:d[field]=[v for row in data.values()for v in row[field]]
d['ground']=data['architecture']['ground']
assert len(d['ground'])==25 and len(d['views'])==len(d['screenshots'])==10
assert {'map-mobile','map-desktop','map-beacon-return','map-touch-beacon-return','map-street-facade','map-roof','map-distant','map-garden-doors-and-canopy','map-loggias-and-central-bands','map-twin-doorways-beneath-canopy'}=={a['view']for a in d['views']}
assert d['realBeacon']['landed']==data['touch']['realBeacon']['landed']==d['id']
assert data['touch']['realBeacon']['action']=='physical canvas touch'
d['physical_selections']=[d['realBeacon'],data['touch']['realBeacon']]
telemetry=parts/'distant/second-public-zoom.json'
if telemetry.exists():
 second=read(telemetry);zoom=data['distant']['distantSelection']
 assert second['action']['trusted'] and second['action']['button']=='zoom-out' and second['before']['variant']=='full'
 assert abs(zoom['before']['zoom']-second['before']['zoom']-1)<.02 and abs(second['before']['zoom']-zoom['after']['zoom']-1)<.02 and zoom['after']['variant']=='distant'
 copy(telemetry,root/'sessions/distant/second-public-zoom.json')
 copy(Path('/dev/shm/shanghai-205-formal/one-further-zoom.py'),root/'sessions/distant/one-further-zoom.py')
 d['distant_zoom_actions']={'count':2,'first_and_final':zoom,'second_input':second,'second_receipt_sha256':sha(telemetry)}

d['files']=[]
for name in dict.fromkeys(v['file']for row in data.values()for v in row['files']):
 records=[r for row in data.values()for r in row['files']if r['file']==name]
 assert len({(r['sha256'],r['bytes'])for r in records})==1
 d['files'].append({**records[0],'loadedByScene':any(r['loadedByScene']for r in records)})
assert len([r for r in d['files']if '/models/candidates/'in r['file']])==4
d.pop('section',None);d['sessions']=receipts;d['started']=min(r['started']for r in data.values());d['finished']=max(r['finished']for r in data.values())
save(dest/'main-browser.json',d);save(dest/'exit.json',dict(code=0,phase='after',base=d['server'],case_sha256=d['caseSha256'],driver_sha256=d['scriptSha256'],production=sha(w/'205-production.json'),finished=d['finished'],sessions=receipts))
for name in ['check-205-separated.cjs','source-driver.sha256','run-205-separated.py','merge-205.py']:copy(w/name,root/name)
