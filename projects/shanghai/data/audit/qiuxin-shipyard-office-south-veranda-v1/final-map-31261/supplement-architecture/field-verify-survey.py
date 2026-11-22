"""Recover the first saved field photograph and verify both viewports against their raw X11 and WebGL captures."""
from pathlib import Path
from hashlib import file_digest
import json,subprocess,sys,datetime,runpy
s=Path(__file__).absolute().parent
v=Path('/dev/shm/field-688-scratch-governor/live/261')
f=s.parent/'final-map-31261'
def sha(p):
 with p.open('rb')as stream:return file_digest(stream,'sha256').hexdigest()
def rd(p):return json.loads(p.read_bytes())
verify=runpy.run_path(str(f/'verify-map-frames.py'))['verify']
files={};sources={};cameras={}
for category,area in [('iron',v/'attempt-03-first-detail-rendered'),('glass',s/'survey')]:
 r=area/'main-browser.json';x=area/'closed.json'
 doc=rd(r);end=rd(x)
 assert end['report_sha256']==sha(r) and end['node_pids'] and end['chromium_pids'] and not end['remaining_children']
 if category=='iron':
  assert not end['passed'] and end['exit_code']>0 and 'Target page, context or browser has been closed' in doc['failure']
 else:
  assert end['passed'] and end['exit_code']==0 and doc['completed'] and len(doc['ground'])==54
 name='map-iron-post-and-scrolls' if category=='iron' else 'map-recessed-sash-and-sill'
 record=verify(area,r);assert record==rd(area/'verified-frames.json') and len(record['frames'])==1 and record['frames'][0]['view']==name
 probe=next(t for t in doc['detailSurvey'] if t['name']==name)
 assert probe['selected']['hit']==(6 if category=='iron' else 3) and len(probe['samples'])==6 and probe['kind']==category
 cameras[category]=dict(view=name,center=probe['selected']['camera'],material_votes=probe['selected']['trace'],observed=probe['selected']['hit'],total=len(probe['samples']),browser_completed=doc['completed'],exit_code=end['exit_code'],node_pids=end['node_pids'],chromium_pids=end['chromium_pids'],frames=record['frames'],ground_points=len(doc.get('ground',[])))
 for p in [r,x,area/'verified-frames.json',area/'viewport-calibration-x11-root.png',area/'actual-driver.cjs',area/'run.log',*[area/(name+suffix+'.png') for suffix in ('','-webgl','-x11-root')]]:
  logical=category+'/'+p.name;files[logical]={'source':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
 sources[category]=sha(r)
out=s/'two-architectural-details.json'
out.write_text(json.dumps(dict(order=261,model=doc['id'],passed=True,predecessor_437_sha256=end['predecessor_sha256'],cameras=cameras,reports=sources,files=files),indent=2,ensure_ascii=False)+'\n')
print(sha(out))
