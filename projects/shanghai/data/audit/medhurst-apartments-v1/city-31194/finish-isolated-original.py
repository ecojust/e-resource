"""Archive each recovered public browser receipt separately, with all ten successful real process exits."""
import argparse,datetime,hashlib,json,os,shutil,socket
from pathlib import Path
opt=argparse.ArgumentParser();opt.add_argument('--visually-reviewed',action='store_true');arg=opt.parse_args()
w=Path(__file__).resolve().parent;proj=Path('/workspace/e-resource/projects/shanghai');audit=proj/'data/audit/medhurst-apartments-v1';store=audit/'city-31194';store.mkdir(exist_ok=True);raw=w/'isolated-evidence';read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,to=None):
 dest=store/(to or f.name);dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert sha(f)==sha(dest);return dest
 try:os.link(f,dest)
 except OSError:shutil.copyfile(f,dest)
 assert sha(f)==sha(dest);return dest
def write(p,d):
 txt=json.dumps(d,ensure_ascii=False,indent=2)+'\n'
 if p.is_file():assert read(p)==d
 else:p.write_text(txt)
 return p
pins=read(w/'isolated-inputs.json');assert all(sha(w/f)==h for f,h in pins['frozen_program_and_inputs'].items())
for fn in ['isolated-inputs.json','check-medhurst-isolated.cjs','isolated-phases.py','finish-isolated.py','31k-live-inputs.json','viewer-byte-continuity.json','original-reference-recheck.json','ordinary-startup-reads.json']:save(w/fn)
save(Path('/tmp/grace194-pixels/194-pixels.json'),'projected-pixels.json')
signed={}
for n in [193,194]:
 path=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';d=read(path);assert sha(w/f'{n}-production.json')==d['production_receipt_sha256'];signed[n]=read(w/f'{n}-production.json')['files'];save(path,f'{n}-31k-comparison.json')
rows=[];all_views=[];all_images=[];all_fetched={};action=[];ground_seen=[]
for index,name in enumerate(pins['stage_order']):
 folder=raw/name;c=read(folder/'closed.json');rfile=Path(c['report']);r=read(rfile);catalog=signed[193 if name=='control'else 194]
 assert c['exit_code']==0 and c['cdp_closed']and not c['remaining_chromium'] and c['observed_chromium_pid_and_starttime']and sha(rfile)==c['report_sha256'] and c['phase']==name
 assert r['completed']and not(r['failed']or r['errors']or r['warnings']);assert r['catalog']['sha256']==catalog['data/candidate-city-integrations.json']and r['scriptSha256']==sha(w/'check-medhurst-isolated.cjs')
 assert 'src/candidate-overview-camera.js'in r['servedRuntime']and all(v['sha256']==catalog[k]for k,v in r['servedRuntime'].items())
 assert bool(r['inputDevice']['touchPoints'])==name.startswith('mobile-');assert len(r['screenshots'])==1
 if index:assert c['predecessor']['sha256']==sha(raw/pins['stage_order'][index-1]/'closed.json')
 im,=r['screenshots'];f=folder/im['file'];assert sha(f)==im['sha256'] and f.stat().st_size==im['bytes'];save(f);all_images.append(im);all_views+=r['views']
 for d in r['files']:
  assert catalog[d['file']]==d['sha256'];all_fetched[d['file']]=d
 if name.endswith('-pin'):
  b,=r['realBeaconInputs'];e=b['pointer'];assert e['trusted']and e['on_canvas'] and e['picked']==b['hit']['id'] and b['landed']=='jingan-medhurst-apartments';action.append(b)
 if name=='street':
  ground_seen=r['ground'];assert len(ground_seen)==22 and all(g['found']==g['expected']for g in ground_seen)
 save(rfile,'actual-browser-phases/'+name+'.json');save(folder/'closed.json','actual-browser-phases/'+name+'-closed.json')
 rows.append(dict(phase=name,exit_code=0,finished=c['finished'],node_pid=c['node_pid'],chromium=c['observed_chromium_pid_and_starttime'],report_sha256=c['report_sha256'],closure_sha256=sha(folder/'closed.json')))
assets={k:v for k,v in all_fetched.items()if '/jingan-medhurst-apartments/' in k};assert len(assets)==4 and len(action)==2 and len(all_images)==10 and ground_seen
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19394))!=0
report=dict(order=194,id='jingan-medhurst-apartments',before_port=31193,after_port=31194,phases=rows,closed_remote_debugging_port=19394,real_pointer_events=action,ground_points=ground_seen,downloaded_model_files=assets,screenshots=all_images)
write(store/'process-exits.json',report)
if arg.visually_reviewed:
 close={'order':194,'before_port':31193,'new_port':31194,'confirmed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_captures_visually_reviewed':True,'process_and_view_receipt':str(store/'process-exits.json'),'reports':{str(f):sha(f)for f in [store/'process-exits.json',*(store/'actual-browser-phases').glob('*.json')]},'real_browser_process_exits':rows}
 receipt=w.parent/'194-map-slot-released.json'
 if receipt.exists():assert read(receipt)['reports']==close['reports']
 else:write(receipt,close)
 print(receipt,sha(receipt))
