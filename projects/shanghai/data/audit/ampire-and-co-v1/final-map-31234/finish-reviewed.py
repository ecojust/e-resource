from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import argparse,json,os,shutil
q=Path(__file__).parent;w=q/'final-map-31234';a=Path('/workspace/e-resource/projects/shanghai/data/audit/ampire-and-co-v1');dst=a/'final-map-31234';pa=argparse.ArgumentParser();pa.add_argument('--notes',type=Path);args=pa.parse_args()
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
# The independent 397 trip runs once the preceding city and 299 have both actually returned.
import subprocess,sys
program=q/'offer-397-development.py'
assert sha(program)=='91050ddbe04d867699774d962aed1484f31ea42abfc8cc3dc29dbe9324397a7b'
subprocess.run([sys.executable,'-Bu',program],check=True,stdout=sys.stderr)
case=read(a/'map-case.json');inputs=read(w/'bound-inputs.json');manifest=read(a.parents[2]/'assets/models/candidates'/case['id']/'manifest.json');assert read(w/'all-real-processes-closed.json')['phases']==7
shots={};rows={};reports={};keep=[]
for phase in ('before','phone','desktop','architecture','mouse','touch','distant'):
 d=w/phase;f=d/('control-browser.json'if phase=='before'else'main-browser.json');c=d/'process.json';v=read(f);close=read(c);stage=inputs['233' if phase=='before'else'234']
 assert v['completed'] and v['id']==case['id']and close['exit_code']==0 and close['node_closed']and close['chromium_pids']and not close['remaining_children']and not close['remaining_chromium']and close['report_sha256']==sha(f)
 assert v['server']==stage['origin']and v['catalog']['sha256']==stage['catalog_sha256']and v['catalog']['count']==stage['count']and v['caseSha256']==sha(a/'map-case.json')and v['scriptSha256']==sha(w/'verified-drivers'/(v['scriptSha256']+'.cjs'))and not(v.get('errors')or v['failed'])
 for field in ('scriptSha256','adapterSha256'):
  digest=v.get(field)
  if digest:
   program=w/'verified-drivers'/(digest+'.cjs')
   assert sha(program)==digest
   keep.append((program,'verified-drivers/'+program.name))
 if phase in ['mouse','touch']:assert len(v['physicalSelections'])==1 and v['physicalSelections'][0]['input']==phase and v['physicalSelections'][0]['selected']==case['id']
 if phase=='architecture':assert len(v['ground'])==len(case['ground'])+len(case['neighbors'])==13 and all(z['expected']==z['found'] for z in v['ground'])and len(v['architecturalPixels'])==2
 if phase=='distant':
  for role,z in manifest['assets'].items():
   match=[k for k in v['files']if k['file'].endswith('/'+z['file'])];assert len(match)==1 and match[0]['sha256']==z['sha256']and(role not in('full','lod')or match[0]['loadedByScene'])
 rows[phase]=dict(closed=str(c),sha256=sha(c),report=str(f),report_sha256=sha(f),exit=0,node_pids=close['node_pids'],chromium_pids=close['chromium_pids'],finished=close['finished']);reports[phase]=str(f)
 keep.extend([(c,phase+'/closed.json'),(f,phase+'/'+f.name)])
 for z in v['screenshots']:
  img=d/z['file'];key=phase+'/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
closed=w/'standalone-closed.json';v=read(closed);f=w/'standalone-31234/viewer.json';viewer=read(f)
assert v['exit']==0 and v['chromium_pids'] and not v['remaining_observed'] and not v['chromium_remaining']and v['report_sha256']==sha(f)and viewer['passed']and len(viewer['downloads'])==len(viewer['views'])==4
source=Path(v['source_inputs']);assert sha(source)==v['source_inputs_sha256'] and len(read(source))==3 and sha(q/'signed-four-downloads.cjs')==v['driver_sha256']
for k,z in manifest['assets'].items():
 item=viewer['downloads'][k];saved=f.parent/item['saved']
 assert item['saveAsVerified'] and saved.name==z['file'] and saved.stat().st_size==z['bytes'] and sha(saved)==item['sha256']==z['sha256']
keep.extend([(q/'signed-four-downloads.cjs','signed-four-downloads.cjs'),(source,'standalone/signed-inputs.json'),(w/'standalone-signed/signed-inputs.py','signed-inputs.py')])
rows['standalone']=dict(closed=str(closed),sha256=sha(closed),report=str(f),report_sha256=sha(f),exit=0,node_pids=[v['pid']],chromium_pids=v['chromium_pids'],finished=v['finished']);reports['standalone']=str(f);keep.extend([(f,'standalone/viewer.json'),(closed,'standalone/closed.json')])
for z in viewer['views']:
 img=f.parent/z['filename'];key='standalone/'+img.name;assert sha(img)==z['sha256'];shots[key]=dict(sha256=sha(img),observation='');keep.append((img,key))
assert len(shots)==16,len(shots)
if not args.notes:print(json.dumps({'images':shots},indent=2));raise SystemExit
notes=read(args.notes)['images'];assert set(notes)==set(shots) and all(z['sha256']==notes[k]['sha256'] and notes[k]['observation'].strip()for k,z in shots.items())
for f,path in keep:link(f,path)
for f in [q/'reconcile-signed-independent.py',w/'independent-filename-review/standalone-closed.json',w/'independent-filename-review/standalone.py']:
 link(f,('independent-filename-review/'+f.name))
for f in [w/'cdp-city-page-234.cjs',q/'mouse-return.py',q/'desktop-299-resume.py',q/'offer-compact-studies.py',q/'offer-397-development.py',q/'check-233-tail.py',q/'wait-233.py',q/'offer-299.py',q/'finish-reviewed.py',w/'check-map-stages.cjs',w/'run.py',w/'sequence.py',w/'standalone.py',w/'bind.py',w/'prewarm.py',w/'bound-inputs.json',w/'prewarm-bound-files.json',w/'checker-inputs.json']:link(f,f.name)
full=Path('/tmp/shanghai-yongjia-porch/scenes/234-all-http.json');doc=read(full);assert doc['passed']and doc['count']==inputs['234']['signed_inputs']and doc['production_receipt_sha256']==inputs['234']['signature_sha256'];link(full,'all-http.json')
from runpy import run_path
failure_verifier=q/'verify-archived-physical.py'
assert sha(failure_verifier)=='e4778caef445ac3f50f19387abbcbd6e5af4fcefc672f877589e56dddb574f3b'
failed_attempts_sha256=run_path(str(failure_verifier))['materialize'](a)
link(failure_verifier,'verify-archived-physical.py')
link(args.notes,'visual-review.json');record=dict(order=234,failed_attempts_sha256=failed_attempts_sha256,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,after_real_screenshot_review=True,real_browser_process_exits=rows,reports=reports,finished=max(z['finished']for z in rows.values()),manual_sha256=sha(args.notes),ports=[31233,31234],screenshots=16,downloads=viewer['downloads'],count=[270,271],all_http_sha256=sha(full))
write(dst/'slot-released.json',record);write(q/'234-map-slot-released.json',record)
