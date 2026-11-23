"""Join the completed physical public interactions and asset receipts."""
from pathlib import Path
import json,hashlib,os,shutil
w=Path(__file__).parent;h=w/'evidence/263';parts=h/'separate';dest=h/'after';root=Path('/dev/shm/c263/live/city-31263')
read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
from retained_evidence import copy
def save(f,d):
 f.parent.mkdir(exist_ok=True,parents=True);f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
dest.mkdir(parents=True,exist_ok=True)
data={};receipts={}
for i in ['before','desktop','phone','details','touch','architecture','closeups','distant']:
 control=i=='before';q=h/'before'if control else parts/i;f=q/('control-browser.json'if control else'main-browser.json');cl=q/'closed.json';d=read(f);c=read(cl)
 assert d['section']==i and d['completed'] and not d['errors'] and not d['failed'] and not d.get('failure')
 assert c['report_sha256']==sha(f) and c['driver_sha256']==sha(q/'executed-driver.cjs')==d['scriptSha256'] and c['driver_sha256'] in ('6e98ab1ce4482603b0dde814cf408010a2306d864e6765377f3a5f8703d0d60b','edd2aa7310f374e91574957045e2cfd11f61809ae0ef26477b2a4271e4925c40',sha(w/'check-263-measured.cjs')) and c['exit']==0 and c['node_closed']and not c['remaining']
 copy(f,root/'sessions'/i/f.name);copy(cl,root/'sessions'/i/cl.name)
 from importlib import util
 spec=util.spec_from_file_location('frame_proofs',w/'verify-263-frames.py');mod=util.module_from_spec(spec);spec.loader.exec_module(mod)
 verified=read(q/'verified-frames.json');assert verified==mod.verify(q,f)
 session=root/'sessions'/i
 for name in [d['viewportCalibration']['image'],'executed-driver.cjs','verified-frames.json',*[r['displayImage']for r in d['displayCaptures']],*[r['file']for r in d['webglCaptures']]]:copy(q/name,session/name)
 if control:continue
 for v in d['screenshots']:
  assert v['sha256']==sha(q/v['file']);copy(q/v['file'],dest/v['file'])
 receipts[i]=c;data[i]=d
d=dict(data['details'])
for k in ['catalog','id','caseSha256','bindings','server']:
 assert all(x[k]==d[k]for x in data.values())
for field in ['views','screenshots']:d[field]=[v for row in data.values()for v in row[field]]
d['scriptSha256ByPhase']={k:v['scriptSha256'] for k,v in data.items()}
d['ground']=data['architecture']['ground']
assert len(d['ground'])==59 and len(d['views'])==len(d['screenshots'])==9
assert {'map-mobile','map-desktop','map-beacon-return','map-touch-beacon-return','map-street-facade','map-roof','map-distant','map-stone-entrance-and-clock','map-upper-windows-and-pediment'}=={a['view']for a in d['views']}
assert d['realBeacon']['landed']==data['touch']['realBeacon']['landed']==d['id']
assert data['touch']['realBeacon']['action']=='physical canvas touch'
d['physical_selections']=[d['realBeacon'],data['touch']['realBeacon']]
d['files']=[]
for name in dict.fromkeys(v['file']for row in data.values()for v in row['files']):
 records=[r for row in data.values()for r in row['files']if r['file']==name]
 assert len({(r['sha256'],r['bytes'])for r in records})==1
 d['files'].append({**records[0],'loadedByScene':any(r['loadedByScene']for r in records)})
assert len([r for r in d['files']if '/models/candidates/'in r['file']])==4
d.pop('section',None);d['sessions']=receipts;d['started']=min(r['started']for r in data.values());d['finished']=max(r['finished']for r in data.values())
save(dest/'main-browser.json',d);save(dest/'exit.json',dict(code=0,phase='after',base=d['server'],case_sha256=d['caseSha256'],driver_sha256=d['scriptSha256'],production=sha(w/'263-production.json'),finished=d['finished'],sessions=receipts))
for name in ['check-263-measured.cjs','verify-263-frames.py','retained_evidence.py','run-263-separated-recovered.py','merge-263-measured.py']:copy(w/name,root/name)
