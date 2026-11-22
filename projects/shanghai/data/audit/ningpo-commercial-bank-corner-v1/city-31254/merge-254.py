"""Join the completed physical public interactions and asset receipts."""
from pathlib import Path
import json,hashlib,os,shutil
w=Path(__file__).parent;h=w/'evidence/254';parts=h/'separate';dest=h/'after';root=Path('/workspace/e-resource/projects/shanghai/data/audit/ningpo-commercial-bank-corner-v1/city-31254')
read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():
  try:os.link(src,dst)
  except OSError:shutil.copyfile(src,dst)
 assert sha(src)==sha(dst)
def save(f,d):
 f.parent.mkdir(exist_ok=True,parents=True);f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
data={};receipts={};phase_drivers={}
source_drivers={sha(f):f for f in w.glob('check-254-*.cjs')}
for i in ['before','desktop','phone','details','touch','architecture','closeups','distant']:
 control=i=='before';q=h/'before'if control else parts/i;f=q/('control-browser.json'if control else'main-browser.json');cl=q/'closed.json';d=read(f);c=read(cl)
 assert d['section']==i and d['completed'] and not d['errors'] and not d['failed'] and not d.get('failure')
 assert c['report_sha256']==sha(f) and c['driver_sha256']==d['scriptSha256'] and c['driver_sha256'] in source_drivers and c['exit']==0 and c['node_closed']and not c['remaining']
 copy(f,root/'sessions'/i/f.name);copy(cl,root/'sessions'/i/cl.name)
 source=source_drivers[c['driver_sha256']];phase_drivers[i]=dict(name=source.name,sha256=c['driver_sha256'])
 copy(source,root/'drivers'/source.name)
 from PIL import Image,ImageChops
 import re
 for capture in d.get('displayCaptures',[]):
  screen=q/capture['displayImage']
  assert sha(screen)==capture['displayImageSha256']
  shot=next(k for k in d['screenshots'] if k['file'][:-4]+'-x11-root.png'==screen.name);assert sha(q/shot['file'])==shot['sha256']
  width,height,left,top=map(int,re.fullmatch(r'(\d+)x(\d+)\+(\d+)\+(\d+)',capture['rectangle']).groups())
  with Image.open(screen) as df,Image.open(q/shot['file']) as stored:
   assert stored.size==(width,height) and not ImageChops.difference(df.crop((left,top,left+width,top+height)).convert('RGB'),stored.convert('RGB')).getbbox()
  copy(screen,root/'display-frames'/i/screen.name)
  calibration=d.get('viewportCalibration')
  if calibration:
   assert [calibration[key] for key in ('width','height','x','y')]==[width,height,left,top]
   cf=q/calibration['image'];assert sha(cf)==calibration['sha256']
   with Image.open(cf) as im:
    rgb=im.convert('RGB');assert rgb.getpixel((left,top))==(207,43,171) and rgb.getpixel((left+width-1,top+height-1))==(31,211,93)
   copy(cf,root/'display-frames'/i/cf.name)
 if control:continue
 for v in d['screenshots']:
  assert v['sha256']==sha(q/v['file']);copy(q/v['file'],dest/v['file'])
 receipts[i]=c;data[i]=d
d=dict(data['details'])
for k in ['catalog','id','caseSha256','bindings','server']:
 assert all(x[k]==d[k]for x in data.values())
for field in ['views','screenshots']:d[field]=[v for row in data.values()for v in row[field]]
d['phaseDrivers']=phase_drivers
d['ground']=data['architecture']['ground']
assert len(d['ground'])==45 and len(d['views'])==len(d['screenshots'])==9
assert {'map-mobile','map-desktop','map-beacon-return','map-touch-beacon-return','map-street-facade','map-roof','map-distant','map-arched-entrance-and-columns','map-oval-window-and-railings'}=={a['view']for a in d['views']}
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
save(dest/'main-browser.json',d);save(dest/'exit.json',dict(code=0,phase='after',base=d['server'],case_sha256=d['caseSha256'],driver_sha256=d['scriptSha256'],production=sha(w/'254-production.json'),finished=d['finished'],sessions=receipts))
for name in ['check-254-separated.cjs','source-driver.sha256','run-254-separated.py','merge-254.py']:copy(w/name,root/name)
