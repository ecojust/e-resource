from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import argparse,json,os,shutil
q=Path(__file__).parent;w=q/'final-map-31264';a=Path('/workspace/e-resource/projects/shanghai/data/audit/shanghai-waterworks-484-corner-v1');dst=a/'final-map-31264';pa=argparse.ArgumentParser();pa.add_argument('--notes',type=Path);args=pa.parse_args()
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
  tmp=t.with_name(t.name+'.part')
  with f.open('rb') as source,tmp.open('wb') as copy:
   shutil.copyfileobj(source,copy,131072);copy.flush();os.fsync(copy.fileno())
  assert sha(tmp)==sha(f)
  os.replace(tmp,t)
 assert sha(t)==sha(f) and t.resolve().is_relative_to(dst.resolve())
case=read(a/'map-case.json');inputs=read(w/'bound-inputs.json');manifest=read(a.parents[2]/'assets/models/candidates'/case['id']/'manifest.json');assert read(w/'all-real-processes-closed.json')['phases']==7
shots={};rows={};reports={};keep=[]
for phase in ('before','phone','desktop','architecture','mouse','touch','distant'):
 d=w/phase;f=d/('control-browser.json'if phase=='before'else'main-browser.json');c=d/'process.json';v=read(f);close=read(c);stage=inputs['263' if phase=='before'else'264']
 assert v['completed'] and v['id']==case['id']and close['exit_code']==0 and close['node_closed']and close['chromium_pids']and not close['remaining_children']and not close['remaining_chromium']and close['report_sha256']==sha(f)
 assert v['server']==stage['origin']and v['catalog']['sha256']==stage['catalog_sha256']and v['catalog']['count']==stage['count']and v['caseSha256']==sha(a/'map-case.json')and v['scriptSha256']==close['source_code_sha256']==sha(d/'actual-driver.cjs')and not(v.get('errors')or v['failed'])
 if phase in ['mouse','touch']:assert len(v['physicalSelections'])==1 and v['physicalSelections'][0]['input']==phase and v['physicalSelections'][0]['selected']==case['id']
 if phase=='architecture':assert len(v['ground'])==len(case['ground'])+len(case['neighbors'])==59 and all(z['expected']==z['found'] for z in v['ground'])and len(v['architecturalPixels'])==2
 if phase=='distant':
  for role,z in manifest['assets'].items():
   match=[k for k in v['files']if k['file'].endswith('/'+z['file'])];assert len(match)==1 and match[0]['sha256']==z['sha256']and(role not in('full','lod')or match[0]['loadedByScene'])
 rows[phase]=dict(closed=str(c),sha256=sha(c),report=str(f),report_sha256=sha(f),exit=0,node_pids=close['node_pids'],chromium_pids=close['chromium_pids'],finished=close['finished']);reports[phase]=str(f)
 keep.extend([(c,phase+'/closed.json'),(f,phase+'/'+f.name)])
 frames=d/'real-frames.json';assert read(frames)['report_sha256']==sha(f) and len(read(frames)['frames'])==len(v['screenshots'])
 keep.append((frames,phase+'/real-frames.json'))
 keep.extend([(d/'actual-driver.cjs',phase+'/actual-driver.cjs'),(d/'actual-debug-port.json',phase+'/actual-debug-port.json')])
 assert len(v['webglCaptures'])==len(v['displayCaptures'])==len(v['screenshots'])
 calibration=v['viewportCalibration'];cal=d/calibration['image'];assert sha(cal)==calibration['sha256']
 keep.append((cal,phase+'/'+cal.name))
 for shot,frame in zip(v['displayCaptures'],v['webglCaptures']):
  full=d/shot['displayImage'];render=d/frame['file']
  assert sha(full)==shot['displayImageSha256'] and sha(render)==frame['sha256']
  keep.extend([(full,phase+'/'+full.name),(render,phase+'/'+render.name)])
 for z in v['screenshots']:
  img=d/z['file'];key=phase+'/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
closed=w/'standalone-closed.json';v=read(closed);f=w/'standalone-31264/viewer.json';viewer=read(f)
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
for f in [q/'wait-263.py',q/'offer-329.py',q/'finish-reviewed.py',w/'check-map-stages.cjs',w/'run.py',w/'sequence.py',w/'standalone.py',w/'bind.py',w/'prewarm.py',w/'bound-inputs.json',w/'prewarm-bound-files.json',w/'checker-inputs.json']:link(f,f.name)
full=Path('/tmp/shanghai-yongjia-porch/scenes/264-all-http.json');doc=read(full);assert doc['passed']and doc['count']==inputs['264']['signed_inputs']and doc['production_receipt_sha256']==inputs['264']['signature_sha256'];link(full,'all-http.json')
for file in [q/'offer-329-recovered.py',q/'finish-reviewed-recovered.py',q/'after-263-recovered.py',w/'sequence-recovered.py',w/'standalone-recovered.py',w/'waterworks-four-saveas.cjs']:
 link(file,'recovered-'+file.name)
for source in (w/'check-waterworks-measured.cjs',w/'run-waterworks-measured.py',w/'verify-map-frames.py',Path('/workspace/shanghai-publisher-preservation/city-264/x11-scanlines.c')):link(source,source.name)
link(args.notes,'visual-review.json');record=dict(order=264,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,after_real_screenshot_review=True,real_browser_process_exits=rows,reports=reports,finished=max(z['finished']for z in rows.values()),manual_sha256=sha(args.notes),ports=[31263,31264],screenshots=len(shots),downloads=viewer['downloads'],actual_saved_downloads=viewer['downloads'],views_reviewed=True,count=[298,299],all_http_sha256=sha(full))
develop=Path('/workspace/.e-resource-recovery/root/hongkou-648-study/development-native')
returned=develop/'early-development-returned.json';actual=read(returned);origin=read(develop/'physical.json')
assert actual['order']==648 and actual['host']==264 and actual['passed'] and actual['exit_code']==0 and actual['all_children_exited'] and actual['remaining_children']==[]
assert actual['physical_sha256']==sha(develop/'physical.json') and origin['passed']
record['development_648_sha256']=sha(returned);record['development_648_physical_sha256']=actual['physical_sha256']
record['finished']=max(record['finished'],actual['finished'])
write(dst/'slot-released.json',record);write(q/'264-map-slot-released.json',record)
