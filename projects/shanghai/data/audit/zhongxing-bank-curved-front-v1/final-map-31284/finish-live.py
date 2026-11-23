from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import argparse,json,os,shutil
q=Path(__file__).parent;w=q/'final-map-31284';a=Path('/workspace/e-resource/projects/shanghai/data/audit/zhongxing-bank-curved-front-v1');dst=Path('/dev/shm/zhongxing284-live/verified-audit/final-map-31284');pa=argparse.ArgumentParser();pa.add_argument('--notes',type=Path);args=pa.parse_args()
def sha(f):
 with f.open('rb')as s:return file_digest(s,'sha256').hexdigest()
def read(f):return json.loads(f.read_bytes())
def write(f,v):
 data=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();f.parent.mkdir(exist_ok=True,parents=True)
 if f.is_file():
  assert f.read_bytes()==data,f;return
 tmp=f.with_suffix('.new');tmp.write_bytes(data);os.replace(tmp,f)
def link(f,rel):
 t=dst/rel;t.parent.mkdir(exist_ok=True,parents=True)
 if not t.exists():
  try:os.link(f,t)
  except OSError:shutil.copyfile(f,t)
 assert sha(t)==sha(f)
case=read(a/'map-case.json');inputs=read(w/'bound-inputs.json');manifest=read(a.parents[2]/'assets/models/candidates'/case['id']/'manifest.json');assert read(w/'all-real-processes-closed.json')['phases']==7
shots={};rows={};reports={};keep=[]
for phase in ('before','phone','desktop','architecture','mouse','touch','distant'):
 d=w/phase;f=d/('control-browser.json'if phase=='before'else'main-browser.json');c=d/'process.json';v=read(f);close=read(c);stage=inputs['283' if phase=='before'else'284']
 assert v['completed'] and v['id']==case['id']and close['exit_code']==0 and close['node_closed']and close['chromium_pids']and not close['remaining_children']and not close['remaining_chromium']and close['report_sha256']==sha(f)
 assert v['server']==stage['origin']and v['catalog']['sha256']==stage['catalog_sha256']and v['catalog']['count']==stage['count']and v['caseSha256']==sha(a/'map-case.json')and v['scriptSha256']==close['driver_sha256']==sha(d/'actual-driver.cjs')and not(v.get('errors')or v['failed'])
 if phase in ['mouse','touch']:assert len(v['physicalSelections'])==1 and v['physicalSelections'][0]['input']==phase and v['physicalSelections'][0]['selected']==case['id']
 if phase=='architecture':assert len(v['ground'])==len(case['ground'])+len(case['neighbors'])==30 and all(z['expected']==z['found'] for z in v['ground'])and len(v['architecturalPixels'])==2
 if phase=='distant':
  for role,z in manifest['assets'].items():
   match=[k for k in v['files']if k['file'].endswith('/'+z['file'])];assert len(match)==1 and match[0]['sha256']==z['sha256']and(role not in('full','lod')or match[0]['loadedByScene'])
 rows[phase]=dict(closed=str(c),sha256=sha(c),report=str(f),report_sha256=sha(f),exit=0,node_pids=close['node_pids'],chromium_pids=close['chromium_pids'],finished=close['finished']);reports[phase]=str(f)
 keep.extend([(c,phase+'/closed.json'),(f,phase+'/'+f.name)])
 for z in v['screenshots']:
  img=d/z['file'];key=phase+'/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
closed=w/'standalone-closed.json';v=read(closed);f=w/'standalone-31284/viewer.json';viewer=read(f)
assert v['exit']==0 and not v['chromium_remaining']and v['report_sha256']==sha(f)and viewer['passed']and len(viewer['downloads'])==4 and len(viewer['views'])==6 and v['chromium_pids'] and not v['remaining_observed']
assert all(z['sha256']==viewer['downloads'][k]['sha256'] for k,z in manifest['assets'].items())
for role,entry in viewer['downloads'].items():
 saved=f.parent/'saved'/entry['file'];assert entry['saveAsVerified'] and saved.stat().st_size==entry['bytes'] and sha(saved)==entry['sha256']
rows['standalone']=dict(closed=str(closed),sha256=sha(closed),report=str(f),report_sha256=sha(f),exit=0,node_pids=v.get('node_pids',[v['pid']]),chromium_pids=v['chromium_pids'],finished=v['finished']);reports['standalone']=str(f);keep.extend([(f,'standalone/viewer.json'),(closed,'standalone/closed.json')])
for z in viewer['views']:
 img=f.parent/z.get('filename',z.get('file'));key='standalone/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
assert len(shots)>=18,len(shots)
if not args.notes:print(json.dumps({'images':shots},indent=2));raise SystemExit
notes=read(args.notes)['images'];assert set(notes)==set(shots) and all(z['sha256']==notes[k]['sha256'] and notes[k]['observation'].strip()for k,z in shots.items())
for f,path in keep:link(f,path)
for f in (q/'controller-recovery.json',q/'guest-349-recovered.json',q/'offer-349-recovered.py',w/'sequence-recovered.py',w/'standalone-retained.py',w/'check-rounded-front-retained.cjs',q/'after-283-retained.py'):link(f,f.name)
for f in [q/'wait-283.py',q/'offer-349.py',q/'finish-reviewed.py',w/'check-map-stages.cjs',w/'run.py',w/'sequence.py',w/'standalone.py',w/'bind.py',w/'prewarm.py',w/'bound-inputs.json',w/'prewarm-bound-files.json',w/'checker-inputs.json']:link(f,f.name)
full=a/'31284-all-http.json';doc=read(full);assert doc['passed']and doc['count']==inputs['284']['signed_inputs']and doc['production_receipt_sha256']==inputs['284']['signature_sha256'];link(full,'all-http.json')
guests={}
for kind in ['native','viewer']:
 g=q/f'349-{kind}-result.json';entry=read(g);receipt=Path(entry['result'])
 assert receipt.name==kind+'-closed.json' and read(receipt)['passed'] and sha(receipt)==entry['result_sha256']
 guests[kind]={'path':str(g),'sha256':sha(g),'result_sha256':sha(receipt)}
 link(g,g.name)
for extra in [q/'after-283-live.py',q/'offer-349-live.py',q/'guest-349-live.json',w/'run-live.py',w/'sequence-live.py',w/'bind-live.py',w/'standalone-live.py',w/'ordinary-284-devices.py',w/'chromium-284-ordinary',w/'standalone-devtools.cjs',w/'check-zhongxing-live.cjs',w/'system-chromium-cdp-284.cjs',q/'finish-live.py']:
 link(extra,extra.name)
link(args.notes,'visual-review.json');record=dict(order=284,guest_349=guests,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,after_real_screenshot_review=True,real_browser_process_exits=rows,reports=rows,finished=max(z['finished']for z in rows.values()),manual_sha256=sha(args.notes),ports=[31283,31284],screenshots=len(shots),downloads=viewer['downloads'],actual_saved_downloads=viewer['downloads'],views_reviewed=True,count=[318,319],all_http_sha256=sha(full))
write(dst/'slot-released.json',record);write(q/'284-map-slot-released.json',record)
