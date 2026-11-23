from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import argparse,json,os,shutil
q=Path(__file__).parent;w=q/'final-map-31268';a=Path('/workspace/e-resource/projects/shanghai/data/audit/somekh-building-street-corner-v1');dst=a/'final-map-31268';pa=argparse.ArgumentParser();pa.add_argument('--notes',type=Path);args=pa.parse_args()
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
  try:os.link(f.resolve(),t)
  except OSError:shutil.copyfile(f,t)
 assert sha(t)==sha(f)
case=read(w/'map-case.json');inputs=read(w/'bound-inputs.json');manifest=read(a.parents[2]/'assets/models/candidates'/case['id']/'manifest.json');assert read(w/'all-real-processes-closed.json')['phases']==7
shots={};rows={};reports={};keep=[]
for phase in ('before','phone','desktop','architecture','mouse','touch','distant'):
 d=w/phase;f=d/('control-browser.json'if phase=='before'else'main-browser.json');c=d/'process.json';v=read(f);close=read(c);stage=inputs['267' if phase=='before'else'268']
 assert v['completed'] and v['id']==case['id']and close['exit_code']==0 and close['node_closed']and close['chromium_pids']and not close['remaining_children']and not close['remaining_chromium']and close['report_sha256']==sha(f)
 assert v['server']==stage['origin']and v['catalog']['sha256']==stage['catalog_sha256']and v['catalog']['count']==stage['count']and v['caseSha256']==sha(w/'map-case.json')and v['source_code_sha256']==v['scriptSha256']==close['driver_sha256']==sha(d/'actual-driver.cjs')and not(v.get('errors')or v['failed'])
 if phase in ['mouse','touch']:assert len(v['physicalSelections'])==1 and v['physicalSelections'][0]['input']==phase and v['physicalSelections'][0]['selected']==case['id']
 if phase=='architecture':assert len(v['ground'])==len(case['ground'])==79 and all(z['expected']==z['found'] for z in v['ground'])and len(v['architecturalPixels'])==3
 if phase=='distant':
  for role,z in manifest['assets'].items():
   match=[k for k in v['files']if k['file'].endswith('/'+z['file'])];assert len(match)==1 and match[0]['sha256']==z['sha256']and(role not in('full','lod')or match[0]['loadedByScene'])
 rows[phase]=dict(closed=str(c),sha256=sha(c),report=str(f),report_sha256=sha(f),exit=0,node_pids=close['node_pids'],chromium_pids=close['chromium_pids'],finished=close['finished']);reports[phase]=str(f)
 import runpy
 verified=runpy.run_path(str(w/'verify-map-frames.py'))['verify'](d,f)
 write(dst/phase/'frame-comparison.json',verified)
 keep.extend([(c,phase+'/closed.json'),(f,phase+'/'+f.name),(d/'actual-driver.cjs',phase+'/actual-driver.cjs')])
 for name in [v['viewportCalibration']['image'],*[t['file'] for t in v['webglCaptures']],*[t['displayImage'] for t in v['displayCaptures']]]:
  keep.append((d/name,phase+'/'+name))
 for z in v['screenshots']:
  img=d/z['file'];key=phase+'/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
closed=w/'standalone-closed.json';v=read(closed);f=w/'standalone-31268/viewer.json';viewer=read(f)
assert v['exit']==0 and not v['chromium_remaining']and v['report_sha256']==sha(f)and viewer['passed']and len(viewer['downloads'])==4 and len(viewer['views'])==6 and v['chromium_pids'] and not v['remaining_observed']
assert all(z['sha256']==viewer['downloads'][k]['sha256'] for k,z in manifest['assets'].items())
rows['standalone']=dict(closed=str(closed),sha256=sha(closed),report=str(f),report_sha256=sha(f),exit=0,node_pids=[v['pid']],chromium_pids=v['chromium_pids'],finished=v['finished']);reports['standalone']=str(f);keep.extend([(f,'standalone/viewer.json'),(closed,'standalone/closed.json')])
for z in viewer['views']:
 img=f.parent/z['filename'];key='standalone/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
assert len(shots)>=18,len(shots)
for item in viewer['downloads'].values():
 saved=f.parent/item['saved'];assert item['saveAsVerified'] and sha(saved)==item['sha256'] and saved.stat().st_size==item['bytes']
if not args.notes:print(json.dumps({'images':shots},indent=2));raise SystemExit
notes=read(args.notes)['images'];assert set(notes)==set(shots) and all(z['sha256']==notes[k]['sha256'] and notes[k]['observation'].strip()for k,z in shots.items())
for f,path in keep:link(f,path)
for f in [q/'wait-267.py',q/'offer-333.py',q/'finish-reviewed.py',w/'check-map-stages.cjs',w/'run.py',w/'sequence.py',w/'standalone.py',w/'bind.py',w/'prewarm.py',w/'bound-inputs.json',w/'prewarm-bound-files.json',w/'checker-inputs.json']:link(f,f.name)
full=Path('/workspace/e-resource/projects/shanghai/data/audit/somekh-building-street-corner-v1/31268-all-http.json');doc=read(full);assert doc['passed']and doc['count']==inputs['268']['signed_inputs']and doc['production_receipt_sha256']==inputs['268']['signature_sha256'];link(full,'all-http.json')
for file in [q/'offer-333-recovered.py',q/'finish-reviewed-recovered.py',q/'after-267-recovered.py',w/'sequence-recovered.py',w/'standalone-recovered.py',w/'somekh-four-saveas.cjs']:
 link(file,'recovered-'+file.name)
link(args.notes,'visual-review.json');record=dict(order=268,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,after_real_screenshot_review=True,real_browser_process_exits=rows,reports=reports,finished=max(z['finished']for z in rows.values()),manual_sha256=sha(args.notes),ports=[31267,31268],screenshots=len(shots),downloads=viewer['downloads'],actual_saved_downloads=viewer['downloads'],views_reviewed=True,count=[302,303],all_http_sha256=sha(full))
write(dst/'slot-released.json',record);write(q/'268-map-slot-released.json',record)
import subprocess,sys
development=Path('/workspace/.e-resource-recovery/root/hongkou-664-study/development-native/complete-268.py')
assert sha(development)=='c9f13ea68c638cd33ee10ea6d9eaf021a3862c44ea4bfcbbc2b9757e9623cec1'
subprocess.run([sys.executable,'-Bu',development,q/'268-map-slot-released.json'],check=True)
