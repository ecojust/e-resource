"""Join the completed physical public interactions and asset receipts."""
from pathlib import Path
import json,hashlib,os,shutil
w=Path(__file__).parent;h=w/'evidence/193';parts=h/'separate';dest=h/'after';root=Path('/workspace/e-resource/projects/shanghai/data/audit/embankment-riverfront-v1/city-31193')
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
for i in ['before','phone','desktop','beacon','beacon-return','architecture','distant','downloads']:
 control=i=='before';q=h/'before'if control else parts/i;f=q/('control-browser.json'if control else'main-browser.json');cl=q/'closed.json';d=read(f);c=read(cl)
 assert d['section']==i and d['completed'] and not d['errors'] and not d['failed'] and not d.get('failure')
 assert c['report_sha256']==sha(f) and c['driver_sha256']==sha(w/('check-193-separated.cjs' if control else 'check-193-default-camera.cjs' if i in ('desktop','phone') else 'check-193-marker.cjs' if i in ('beacon','beacon-return') else 'check-193-near-views.cjs')) and c['exit']==0 and c['node_closed']and not c['remaining']
 copy(f,root/'sessions'/i/f.name);copy(cl,root/'sessions'/i/cl.name)
 if control:continue
 for v in d['screenshots']:
  assert v['sha256']==sha(q/v['file']);copy(q/v['file'],dest/v['file'])
 receipts[i]=c;data[i]=d
d=dict(data['architecture'])
for k in ['catalog','id','caseSha256','bindings','server']:
 assert all(x[k]==d[k]for x in data.values())
d['executedDriverBySession']={k:v['scriptSha256'] for k,v in data.items()}
assert all(v['scriptSha256']==receipts[k]['driver_sha256'] for k,v in data.items())
for field in ['views','screenshots']:d[field]=[v for row in data.values()for v in row[field]]
assert len(d['ground'])==22 and len(d['views'])==len(d['screenshots'])==7
assert {'map-mobile','map-desktop','map-beacon-return','map-street-facade','map-roof','map-distant','map-terrace-and-pavilion'}=={a['view']for a in d['views']}
assert len(data['downloads']['savedDownloads'])==4 and {r['role'] for r in data['downloads']['savedDownloads']}=={'raw','full','lod','native'}
assert not data['downloads']['views'] and not data['downloads']['screenshots']
d['savedDownloads']=data['downloads']['savedDownloads']
d['realBeacon']=data['beacon']['realBeacon']
assert d['realBeacon']['landed']==d['id'] and d['realBeacon']['realPointer']['trusted']
assert all(data[k]['directoryPointer']=={'id':d['id'],'type':t,'trusted':True} for k,t in [('phone','touch'),('desktop','mouse')])
d['directoryInputs']=[data[k]['directoryPointer'] for k in ['phone','desktop']]
assert all(v['glError']==0 and not v['contextLost'] for v in d['views'])
assert all(r['found']==r['expected'] for r in d['ground'])
d['files']=[]
for name in dict.fromkeys(v['file']for row in data.values()for v in row['files']):
 records=[r for row in data.values()for r in row['files']if r['file']==name]
 assert len({(r['sha256'],r['bytes'])for r in records})==1
 d['files'].append({**records[0],'loadedByScene':any(r['loadedByScene']for r in records)})
verified_assets=[r for r in d['files'] if '/models/candidates/'in r['file']]
assert len(verified_assets)==4
assert {(v['bytes'],v['sha256']) for v in verified_assets}=={(v['bytes'],v['sha256']) for v in d['savedDownloads']}
d.pop('section',None);d['sessions']=receipts;d['started']=min(r['started']for r in data.values());d['finished']=max(r['finished']for r in data.values())
save(dest/'main-browser.json',d);save(dest/'exit.json',dict(code=0,phase='after',base=d['server'],case_sha256=d['caseSha256'],driver_sha256=d['scriptSha256'],production=sha(w/'193-production.json'),finished=d['finished'],sessions=receipts))
for name in ['check-193-marker.cjs','check-193-near-views.cjs','check-193-default-camera.cjs','check-193-separated.cjs','source-driver.sha256','run-193-separated.py','merge-193.py']:copy(w/name,root/name)

for f in (h/'first-phone-overview').iterdir():
 if f.is_file():copy(f,root/'first-phone-overview'/f.name)
copy(w/'overview-streaming-correction.json',root/'overview-streaming-correction.json')

for f in (h/'first-desktop-renderer').iterdir():
 if f.is_file():copy(f,root/'first-desktop-renderer'/f.name)

for f in (h/'first-beacon-renderer').iterdir():
 if f.is_file():copy(f,root/'first-beacon-renderer'/f.name)

assert data['beacon-return']['reopenedFromMarker']['clickReportSha256']==sha(parts/'beacon/main-browser.json')
for f in (h/'first-beacon-transition').iterdir():
 if f.is_file():copy(f,root/'first-beacon-transition'/f.name)

for folder in h.glob('retained-*'):
 for f in folder.iterdir():
  if f.is_file():copy(f,root/folder.name/f.name)

zoom=read(h/'real-distance-zoom.json');assert zoom['confirmed_after_button']['variant']=='distant' and zoom['before']['variant']=='full' and len(zoom['steps'])>=1
copy(h/'real-distance-zoom.json',root/'real-distance-zoom.json');copy(w/'zoom-beyond-lod.cjs',root/'zoom-beyond-lod.cjs')
