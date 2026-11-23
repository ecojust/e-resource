"""Join the completed physical public interactions and asset receipts."""
from pathlib import Path
import json,hashlib,os,shutil
w=Path(__file__).parent;h=w/'evidence/279';parts=h/'separate';dest=h/'after';root=Path('/dev/shm/arnhold279-live/verified-audit/city-31279')
read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():
  try:os.link(src,dst)
  except OSError:shutil.copyfile(src,dst)
 assert sha(src)==sha(dst)
def save(f,d):
 f.parent.mkdir(exist_ok=True,parents=True);f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
data={};receipts={}
for i in ['before','desktop','phone','details','touch','architecture','closeups','distant']:
 control=i=='before';q=h/'before'if control else parts/i;f=q/('control-browser.json'if control else'main-browser.json');cl=q/'closed.json';d=read(f);c=read(cl)
 assert d['section']==i and d['completed'] and not d['errors'] and not d['failed'] and not d.get('failure')
 assert c['report_sha256']==sha(f) and c['driver_sha256']==sha(q/'actual-driver.cjs')==d['scriptSha256'] and c['exit']==0 and c['node_closed']and not c['remaining']
 copy(f,root/'sessions'/i/f.name);copy(cl,root/'sessions'/i/cl.name)
 if control:continue
 for v in d['screenshots']:
  assert v['sha256']==sha(q/v['file']);copy(q/v['file'],dest/v['file'])
 receipts[i]=c;data[i]=d
d=dict(data['details'])
for k in ['catalog','id','caseSha256','bindings','server']:
 assert all(x[k]==d[k]for x in data.values())
d['phase_driver_sha256']={i:v['scriptSha256'] for i,v in data.items()}
for field in ['views','screenshots']:d[field]=[v for row in data.values()for v in row[field]]
d['ground']=data['architecture']['ground']
assert len(d['ground'])==66 and len(d['views'])==len(d['screenshots'])==9
assert {'map-mobile','map-desktop','map-beacon-return','map-touch-beacon-return','map-street-facade','map-roof','map-distant','map-sichuan-road-320-and-stone-arch','map-jiujiang-road-red-brick-bays-and-cornice'}=={a['view']for a in d['views']}
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
save(dest/'main-browser.json',d);save(dest/'exit.json',dict(code=0,phase='after',base=d['server'],case_sha256=d['caseSha256'],driver_sha256=d['scriptSha256'],production=sha(w/'279-production.json'),finished=d['finished'],sessions=receipts))
for name in ['check-279-separated.cjs','check-279-live.cjs','check-279-field.cjs','check-directory-279.cjs','check-street-279.cjs','check-beacon-279.cjs','check-touch-279.cjs','check-touch-reload-279.cjs','check-feature-pair-279.cjs','check-building-closeups-279.cjs','run-279-live.py','offer-344-live.py','source-driver.sha256','run-279-separated.py','merge-279.py','run-279-recovered.py','merge-279-recovered.py','offer-344-recovered.py']:copy(w/name,root/name)
