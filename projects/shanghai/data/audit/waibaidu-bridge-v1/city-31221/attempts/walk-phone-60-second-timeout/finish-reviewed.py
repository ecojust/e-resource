"""Inventory original-city screenshots and, after visual review, sign the city release for the next operator."""
from pathlib import Path
from shutil import copyfile
import argparse,datetime,hashlib,json,os
w=Path(__file__).resolve().parent;n=int(w.name.rsplit('-',1)[1]);assert n in (221,223)
model={221:'waibaidu-bridge-v1',223:'sichuan-road-bridge-v1'}[n];audit=Path('/workspace/e-resource/projects/shanghai/data/audit')/model;public=audit/f'city-{31000+n}'
parser=argparse.ArgumentParser();parser.add_argument('--notes',type=Path);args=parser.parse_args()
def read(p):return json.loads(p.read_bytes())
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def copy(p,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():
  try:os.link(p,target)
  except OSError:copyfile(p,target)
 assert sha(p)==sha(target)
def save(p,obj):
 data=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
 if p.exists():assert p.read_bytes()==data,p;return
 p.parent.mkdir(exist_ok=True,parents=True);temp=p.with_suffix('.pending');temp.write_bytes(data);os.replace(temp,p)
bound=read(w/'presentation-inputs.json');assert bound['passed']
photos={};receipts={};downloads={};final=None;to_archive=[]
for stage in ['before','phone','desktop','mouse','touch','walk-phone','walk-desktop','standalone']:
 folder=w/'sessions'/stage;walk=stage.startswith('walk');solo=stage=='standalone'
 report=folder/('real-city.json'if walk else'viewer.json'if solo else'report.json');closed=folder/'closed.json'
 result=read(report);cl=read(closed);assert result['passed']and cl['node_closed']and cl['exit']==0 and cl['chromium_pids']and cl['remaining']==[]
 assert not result.get('errors')and not result.get('pageErrors')and cl['report_sha256']==sha(report)
 final=max(final or cl['finished'],cl['finished'])
 if solo:
  downloads=result['downloads'];assert len(downloads)==4 and len(result['views'])==4 and not result['pageErrors']
 elif walk:
  mesh=folder/'real-city-mesh.json';proof=read(mesh);assert proof['passed'] and proof['max_error_m']<.003
  assert all(c['state']['mode']=='walk'for c in result['cases'][:2])
  assert result['departure'] and result['returned'] and result['closed'] and not result['failedRequests']
  to_archive.append((mesh,'sessions/'+stage+'/'+mesh.name))
 else:
  assert result['closed']and result['production']==bound['rows'][str(n-1 if stage=='before'else n)]['production_sha256']
 for shot in result['views'] if solo else result['cases']if walk else result['screenshots']:
  f=folder/shot['filename'if solo else'file'];k=stage+'/'+f.name;assert shot['sha256']==sha(f);photos[k]=shot['sha256']
  to_archive.append((f,k))
 receipts[stage]={'report':str(report),'report_sha256':sha(report),'closed':str(closed),'closed_sha256':sha(closed),'exit':0,'node':cl['node'],'chromium_pids':cl['chromium_pids'],'remaining_chromium':[]}
 to_archive.extend([(report,'sessions/'+stage+'/'+report.name),(closed,'sessions/'+stage+'/closed.json')])
assert len(photos)==17
import runpy
index=runpy.run_path(str(w/'build-attempt-index.py'))['build']()
to_archive.extend([(index,'archived-browser-attempts.json'),(w/'build-attempt-index.py','build-attempt-index.py')])
for file in (w/'attempts').rglob('*'):
 if file.is_file():to_archive.append((file,str(file.relative_to(w))))
for receipt in (Path('/tmp/wanyi343/vector/221-before-retry-returned.json'),Path('/tmp/elisabeth360/door-revision/packed-exit.json'),Path('/tmp/remi-jinling285/mapping/handoff/221-retry-returned.json')):
 assert read(receipt).get('exit_code')==0
 to_archive.append((receipt,'supplemental/'+receipt.parent.name+'-'+receipt.name))
if not args.notes:
 print(json.dumps({'images':{k:{'sha256':v,'observation':''}for k,v in photos.items()}},indent=2));raise SystemExit
notes=read(args.notes);assert set(notes['images'])==set(photos)
for k,v in photos.items():
 note=notes['images'][k];assert note['sha256']==v and note['observation'].strip(),k
for p,key in to_archive:copy(p,public/key)
for name in ['bind.py','presentation-inputs.json','overview.cjs','walk.cjs','run-when-released.py','finish-reviewed.py',f'offer-{286 if n==221 else 288}.py']:
 copy(w/name,public/name)
full=w/'all-http.json';formal=read(full);assert formal['passed']and formal['production_receipt_sha256']==bound['rows'][str(n)]['production_sha256']
copy(full,public/'all-http.json');save(public/'visual-review.json',notes)
handoff={'archived_attempts_sha256':sha(index),'order':n,'passed':True,'exit':0,'exit_code':0,'remaining':[],'remaining_chromium':[],'final_closed_at':final,'after_real_screenshot_review':True,'all_captures_visually_reviewed':True,'screenshots':photos,'receipts':receipts,'downloads':downloads,'review_sha256':sha(public/'visual-review.json'),'actual_public_inputs_sha256':sha(w/'presentation-inputs.json'),'full_http_sha256':sha(full)}
save(public/'slot-released.json',handoff);save(w/f'{n}-map-slot-released.json',handoff);print(w/f'{n}-map-slot-released.json',sha(w/f'{n}-map-slot-released.json'))
