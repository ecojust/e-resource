"""Inventory original-city screenshots and, after visual review, sign the city release for the next operator."""
from pathlib import Path
from shutil import copyfile
import argparse,datetime,hashlib,json,os
w=Path(__file__).resolve().parent;n=int(w.name.rsplit('-',1)[1]);assert n==230
model='zhapu-road-bridge-v1';audit=Path('/workspace/e-resource/projects/shanghai/data/audit')/model;public=audit/f'city-{31000+n}'
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
  for role,item in result['downloads'].items():
   file=folder/item['saved'];assert item['saveAsVerified'] and sha(file)==item['sha256'] and file.stat().st_size==item['bytes']
  downloads=result['downloads'];assert len(downloads)==4 and len(result['views'])==len(result['orientationViews'])==4 and not result['pageErrors']
 elif walk:
  mesh=folder/'real-city-mesh.json';proof=read(mesh);assert proof['passed'] and proof['max_error_m']<.003
  assert all(c['state']['mode']=='walk'for c in result['cases'][:2])
  assert result['departure'] and result['returned'] and result['closed'] and not result['failedRequests']
  to_archive.append((mesh,'sessions/'+stage+'/'+mesh.name))
  parts=result['componentProcesses']
  assert [item['section'] for item in parts]==['walk','side','far','departure-return']
  for item in parts:
   c=folder/('component-'+item['section']);receipt=c/'process.json';observation=c/'real-city.json'
   assert read(receipt)==item and item['exit']==0 and item['node']>1 and item['driver_sha256']==cl['driver_sha256'] and item['report_sha256']==sha(observation)
   actual=read(observation);assert actual['passed'] and actual['closed']
   for img in actual['cases']:assert img['sha256']==sha(c/img['file'])==sha(folder/img['file'])
   for f in c.iterdir():
    if f.is_file():to_archive.append((f,'sessions/'+stage+'/'+c.name+'/'+f.name))
 else:
  assert result['closed']and result['production']==bound['rows'][str(n-1 if stage=='before'else n)]['production_sha256']
 for shot in [*result['views'],*result['orientationViews']] if solo else result['cases']if walk else result['screenshots']:
  f=folder/shot['filename'if solo else'file'];k=stage+'/'+f.name;assert shot['sha256']==sha(f);photos[k]=shot['sha256']
  to_archive.append((f,k))
 receipts[stage]={'report':str(report),'report_sha256':sha(report),'closed':str(closed),'closed_sha256':sha(closed),'exit':0,'node':cl['node'],'chromium_pids':cl['chromium_pids'],'remaining_chromium':[]}
 to_archive.extend([(report,'sessions/'+stage+'/'+report.name),(closed,'sessions/'+stage+'/closed.json')])
wide=w/'sessions/before-wide';wc=read(wide/'closed.json');wr=read(wide/'report.json')
assert wr['passed'] and wr['closed'] and wc['exit']==0 and wc['node_closed'] and wc['chromium_pids'] and not wc['remaining']
assert wc['report_sha256']==sha(wide/'report.json') and wr['base'].endswith(':31229/') and wr['directory']['containsNewBridge'] is False
assert wr['deviceProfile']['viewport']=={'width':960,'height':680} and wr['observed']['water']>0 and len(wr['observed']['bridgeSources'])==2
wf=wide/'old-water-and-road.png';assert wr['screenshots'][0]['sha256']==sha(wf);photos['before-wide/'+wf.name]=sha(wf)
to_archive.extend([(wf,'before-wide/'+wf.name),(wide/'report.json','sessions/before-wide/report.json'),(wide/'closed.json','sessions/before-wide/closed.json'),(w/'before-overview-wide.cjs','before-overview-wide.cjs')])
assert len(photos)==22

if not args.notes:
 print(json.dumps({'images':{k:{'sha256':v,'observation':''}for k,v in photos.items()}},indent=2));raise SystemExit
notes=read(args.notes);assert set(notes['images'])==set(photos)
for k,v in photos.items():
 note=notes['images'][k];assert note['sha256']==v and note['observation'].strip(),k
for p,key in to_archive:copy(p,public/key)
for name in ['bind.py','presentation-inputs.json','overview.cjs','walk.cjs','run-when-released.py','finish-reviewed.py','offer-295.py','official-standalone.cjs']:
 copy(w/name,public/name)
for name in ['ordinary-cameras.py','ordinary-cameras.json','replay.py']:
 copy(w/name,public/name)
import runpy
attempts=runpy.run_path(str(w/'verify-attempts.py'))['history'](w,public)
copy(w/'verify-attempts.py',public/'verify-attempts.py')
copy(w/'verify-public-attempts.py',public/'verify-public-attempts.py')
for label in sorted(f.name for f in w.glob('*-handback.json')):
 if (w/label).is_file():copy(w/label,public/'guest-returns'/label)
full=w/'all-http.json';formal=read(full);assert formal['passed']and formal['production_receipt_sha256']==bound['rows'][str(n)]['production_sha256']
copy(full,public/'all-http.json');copy(w/'replayed-signed-navigation.json',public/'replayed-signed-navigation.json');save(public/'visual-review.json',notes)
handoff={'order':n,'passed':True,'exit':0,'exit_code':0,'remaining':[],'remaining_chromium':[],'final_closed_at':final,'finished':final,'after_real_screenshot_review':True,'all_captures_visually_reviewed':True,'screenshots':{k:v for k,v in photos.items() if not k.startswith('before-wide/')},'supplementary_screenshots':{'before-wide/'+wf.name:{'file':str(wf),'bytes':wf.stat().st_size,'sha256':sha(wf),'phase':'before-wide'}},'receipts':receipts,'downloads':downloads,'review_sha256':sha(public/'visual-review.json'),'actual_public_inputs_sha256':sha(w/'presentation-inputs.json'),'full_http_sha256':sha(full)}
handoff['failed_attempts_sha256']=sha(public/'attempts/index.json')
handoff['actual_saved_downloads']=downloads
handoff['reports']={k:dict(report=v['report'],report_sha256=v['report_sha256'],exit=v['closed'],exit_sha256=v['closed_sha256'])for k,v in receipts.items()}
handoff['real_browser_process_exits']={k:read(Path(v['closed']))for k,v in receipts.items()}
handoff['supplementary_receipts']={'before-wide':{'report':str(wide/'report.json'),'report_sha256':sha(wide/'report.json'),'closed':str(wide/'closed.json'),'closed_sha256':sha(wide/'closed.json')}};handoff['signed_navigation_sha256']=sha(w/'replayed-signed-navigation.json');save(public/'slot-released.json',handoff);save(w/f'{n}-map-slot-released.json',handoff);print(w/f'{n}-map-slot-released.json',sha(w/f'{n}-map-slot-released.json'))
