from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import argparse,json,os,shutil
q=Path(__file__).parent;w=q/'final-map-31237';a=Path('/workspace/e-resource/projects/shanghai/data/audit/gibb-livingston-corner-v1');dst=a/'final-map-31237';pa=argparse.ArgumentParser();pa.add_argument('--notes',type=Path);args=pa.parse_args()
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
 d=w/phase;f=d/('control-browser.json'if phase=='before'else'main-browser.json');c=d/'process.json';v=read(f);close=read(c);stage=inputs['236' if phase=='before'else'237']
 assert v['completed'] and v['id']==case['id']and close['exit_code']==0 and close['node_closed']and close['chromium_pids']and not close['remaining_children']and not close['remaining_chromium']and close['report_sha256']==sha(f)
 assert v['server']==stage['origin']and v['catalog']['sha256']==stage['catalog_sha256']and v['catalog']['count']==stage['count']and v['caseSha256']==sha(a/'map-case.json')and v['scriptSha256']==('c6cb1166a413d1515c84b6018de9d58541169117df3936329702d1392256b7c4' if phase in ['before','phone','desktop','architecture'] else sha(w/('check-distant-groups.cjs' if phase=='distant' else 'check-map-stages.cjs')))and not(v.get('errors')or v['failed'])
 if phase in ['mouse','touch']:assert len(v['physicalSelections'])==1 and v['physicalSelections'][0]['input']==phase and v['physicalSelections'][0]['selected']==case['id']
 if phase=='architecture':assert len(v['ground'])==len(case['ground'])+len(case['neighbors'])==35 and all(z['expected']==z['found'] for z in v['ground'])and len(v['architecturalPixels'])==2
 if phase=='distant':
  for role,z in manifest['assets'].items():
   match=[k for k in v['files']if k['file'].endswith('/'+z['file'])];assert len(match)==1 and match[0]['sha256']==z['sha256']and(role not in('full','lod')or match[0]['loadedByScene'])
 rows[phase]=dict(closed=str(c),sha256=sha(c),report=str(f),report_sha256=sha(f),exit=0,node_pids=close['node_pids'],chromium_pids=close['chromium_pids'],finished=close['finished']);reports[phase]=str(f)
 keep.extend([(c,phase+'/closed.json'),(f,phase+'/'+f.name)])
 for z in v['screenshots']:
  img=d/z['file'];key=phase+'/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
for z in read(w/'mouse/main-browser.json').get('supplementary',[]):
 img=w/'mouse'/z['file'];key='supplementary/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
ind=w/'actual-standalone';closed=ind/'closed.json';v=read(closed);f=ind/'viewer.json';viewer=read(f)
assert v['passed'] and v['exit_code']==0 and v['node_closed'] and not v['remaining_chromium'] and v['report_sha256']==sha(f) and viewer['passed'] and len(viewer['downloads'])==4 and len(viewer['views'])==6 and v['chromium_pids'] and not v['remaining_children']
assert all(z['sha256']==viewer['downloads'][k]['sha256']==sha(ind/viewer['downloads'][k]['saved']) and viewer['downloads'][k]['saveAsVerified'] for k,z in manifest['assets'].items())
rows['standalone']=dict(closed=str(closed),sha256=sha(closed),report=str(f),report_sha256=sha(f),exit=0,node_pids=[v['node_pid']],chromium_pids=v['chromium_pids'],finished=v['finished']);reports['standalone']=str(f);keep.extend([(f,'standalone/viewer.json'),(closed,'standalone/closed.json')])
for z in viewer['views']:
 img=ind/z['file'];key='standalone/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
assert len(shots)>=18,len(shots)
if not args.notes:print(json.dumps({'images':shots},indent=2));raise SystemExit
notes=read(args.notes)['images'];assert set(notes)==set(shots) and all(z['sha256']==notes[k]['sha256'] and notes[k]['observation'].strip()for k,z in shots.items())
for f,path in keep:link(f,path)
for f in [q/'watch.py',q/'finish-reviewed.py',w/'check-map-stages.cjs',w/'run.py',w/'sequence.py',w/'bind.py',w/'prewarm.py',w/'bound-inputs.json',w/'prewarm-bound-files.json',w/'checker-inputs.json']:link(f,f.name)
link(Path('/workspace/.e-resource-recovery/grace/reboot237/original-city-driver.cjs'),'original-city-driver.cjs')
link(Path('/workspace/.e-resource-recovery/grace/reboot237/visibility.py'),'visibility.py')
for name in ('after-412.py','verify-page.cjs'):
 link(Path('/workspace/.e-resource-recovery/browser/237-ordinary')/name,'standalone/'+name)
full=Path('/tmp/shanghai-yongjia-porch/scenes/237-all-http.json');doc=read(full);assert doc['passed']and doc['count']==inputs['237']['signed_inputs']and doc['production_receipt_sha256']==inputs['237']['signature_sha256'];link(full,'all-http-catalog.json')
link(w/'check-distant-groups.cjs','check-distant-groups.cjs')
for name in ('process.json','main-browser.json','distant.log','distant.exit'):
 link(Path('/workspace/.e-resource-recovery/grace/reboot237/first-distant-grouped-marker')/name,'attempts/first-distant-grouped-marker/'+name)
link(Path('/tmp/shanghai-fourth-302/237-viewer-deferred.json'),'guests/302-first-deferred.json')
link(Path('/tmp/shanghai-fourth-302/architecture-302-supplement.json'),'guests/302-later-viewer.json')
link(Path('/tmp/shanghai-fourth-302/viewer-closed.json'),'guests/302-viewer-closed.json')
link(Path('/tmp/shanghai-fourth-302/native-closed.json'),'guests/302-native-closed.json')
link(Path('/tmp/chekiang-bank518/237-native-returned.json'),'guests/518-reverified.json')
link(Path('/tmp/hongkou-412-study/development-native/237-development-returned.json'),'guests/412-returned.json')
late=Path('/workspace/.e-resource-recovery/root/huangpu-536-study/development-native/early-development-returned.json')
guest=read(late)
assert guest['order']==536 and guest['host']==237 and guest['all_children_exited'] and guest['remaining_children']==[]
assert guest['physical_sha256']==sha(late.parent/'physical.json')
link(late,'guests/536-returned.json')
link(args.notes,'visual-review.json');record=dict(order=237,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,after_real_screenshot_review=True,real_browser_process_exits=rows,reports=reports,finished=max(z['finished']for z in rows.values()),manual_sha256=sha(args.notes),ports=[31236,31237],screenshots=len(shots),downloads=viewer['downloads'],count=[273,274],all_http_sha256=sha(full))
record.update(final_guest_536_sha256=sha(late),sessions=rows,actual_report_sha256=sha(dst/'results.json'),actual_saved_downloads=viewer['downloads']);write(dst/'slot-released.json',record);write(q/'237-map-slot-released.json',record)
