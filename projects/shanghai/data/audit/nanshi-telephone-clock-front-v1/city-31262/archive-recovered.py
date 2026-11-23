"""Archive the genuine Nanshi Telephone Exchange map sessions and the exact historical viewer bytes; issue the physical handoff only after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path('/tmp/shanghai-main-262/formal-31262');a=Path('/workspace/e-resource/projects/shanghai/data/audit/nanshi-telephone-clock-front-v1');e=w/'isolated-evidence';dest=a/'city-31262'
ap=argparse.ArgumentParser();ap.add_argument('--reviewed',action='store_true');ap.add_argument('--submit',action='store_true');args=ap.parse_args()
r=lambda f:json.loads(f.read_bytes());h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,rel=None):
 t=dest/(rel or f.name);t.parent.mkdir(exist_ok=True,parents=True)
 if not t.exists():
  if f.is_symlink():
   shutil.copyfile(f,t)
  else:
   try:os.link(f,t)
   except OSError:shutil.copyfile(f,t)
 assert h(t)==h(f);return t
def put(f,q):
 if f.exists():assert r(f)==q;return
 z=f.with_suffix('.temp');z.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');z.replace(f)
pins=r(w/'isolated-inputs.json');intake=r(w/'signed-comparison.json');assert all(h(w/k)==v for k,v in pins['frozen_program_and_inputs'].items())
for f in ['check-nanshi-telephone.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','standalone-visual-review.json','isolated-inputs.json','archive.py','x11-scanlines.c','archive-recovered.py','sequence-recovered.py','capture-measured.py','nanshi_runtime.py','check-nanshi-telephone-measured.cjs','verify-map-frames.py']:save(w/f)
pr261=Path('/tmp/shanghai-yongjia-porch/scenes/261-all-http.json')
for n in [261,262]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=(pr261 if n==261 else a/'31262-all-http.json');assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-261/261-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=261 if name=='control'else 262
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==h(folder/'actual-driver.cjs')==actual['scriptSha256']
 assert c['predecessor']['sha256']==h(old);old=folder/'closed.json'
 assert actual['realDirectoryEntry']['pointer']['trusted'];assert actual['completed'] and not (actual['failed'] or actual['errors'] or actual['warnings']) and actual['phase']==name and actual['server']==f'http://127.0.0.1:{31000+n}/'
 assert all(sig[k]==z['sha256']for k,z in actual['servedRuntime'].items()) and sig['data/candidate-city-integrations.json']==actual['catalog']['sha256']
 assert bool(actual['inputDevice']['touchPoints'])==name.startswith('mobile-');v=actual['views'][0]
 assert not v['contextLost'] and v['glError']==0
 if name=='control':assert v['clip'] is None
 else:assert v['asset']['status']=='loaded' and v['asset']['visible'] and v['asset']['verifiedAsset']['modelId']==pins['id']
 if name in ['mobile-pin','desktop-pin']:
  ev,=actual['realBeaconInputs'];assert ev['pointer']['trusted'] and ev['pointer']['on_canvas'] and ev['landed']==pins['id'];actions.append(ev)
 if name=='street':
  floor=actual['ground'];assert len(floor)==len(cases['ground'])+len(cases['neighbors']) and all(v['found']==v['expected'] for v in floor)
 if name=='distant':assert v['asset']['variant']=='distant'
 im,=actual['screenshots'];impath=folder/im['file'];assert h(impath)==im['sha256'] and impath.stat().st_size==im['bytes'];save(impath);images.append(im)
 for rec in actual['files']:
  f=rec['file'];assert rec['sha256']==sig.get(f,native.get(f,{}).get('sha256'));files[f]=rec
 frame_check=folder/'frame-check.json'
 assert h(frame_check)==c['frame_check_sha256'] and r(frame_check)['report_sha256']==h(path)
 from runpy import run_path
 verify=run_path(str(w/'verify-map-frames.py'))['verify']
 assert verify(folder,path)==r(frame_check)
 save(frame_check,'actual-browser-phases/'+name+'/frame-check.json')
 save(folder/'actual-driver.cjs','actual-browser-phases/'+name+'/actual-driver.cjs')
 for picture in (actual['viewportCalibration']['image'],actual['displayCaptures'][0]['displayImage'],actual['webglCaptures'][0]['file']):
  save(folder/picture,'actual-browser-phases/'+name+'/'+picture)
 save(path,'actual-browser-phases/'+name+'.json');save(old,'actual-browser-phases/'+name+'-closed.json')
 rows.append({'phase':name,'exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':h(path),'closed_sha256':h(old)})
# Require both separate guest outcomes even when a caller invokes the archiver directly.
guest=Path('/tmp/sino-german-hospital327')
for kind,phase in [('native','control'),('viewer','mobile-pin')]:
 receipt=guest/f'{kind}-closed.json';item=r(receipt);source=e/phase/'closed.json'
 assert item['order']==327 and item['passed'] and item['all_processes_closed'] and item['wrapper_closed']
 assert item['host_receipt_sha256']==h(source) and item['host_report_sha256']==r(source)['report_sha256']
 assert not item.get('remaining_chromium') and not item.get('remaining_blender')
 if kind=='native':assert len(item['assets'])==4 and len(item['blender_pids'])>=2
 else:assert item['views']==6 and item['downloads']==4 and h(Path(item['report']))==item['receipt_sha256']
assets={k:y for k,y in files.items() if '/huangpu-nanshi-telephone-exchange/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==52
for phase in pins['stage_order']:
 c=r(e/phase/'closed.json')
 assert c['cdp_closed'] and c['debug_port']>0
 with socket.socket()as connection:
  connection.settimeout(1)
  assert connection.connect_ex(('127.0.0.1',c['debug_port']))!=0,phase
def checked_viewer():
 closure=w/'current-standalone/closed.json';c=r(closure);report=Path(c['report']);v=r(report)
 assert c['passed'] and c['exit_code']==0 and c['chromium'] and c['remaining']==[] and c['report_sha256']==h(report)
 expected=r(w/'standalone-originals.json')['downloads'];assert set(v['downloads'])==set(expected) and len(v['views'])==6
 for k,row in v['downloads'].items():
  assert row['saveAsVerified'] and {f:row[f] for f in ('file','bytes','sha256')}==expected[k] and h(report.parent/'saved'/row['file'])==row['sha256']
 for row in v['views']:assert h(dest/'current-standalone'/row['filename'])==row['sha256']
 return v
fresh=checked_viewer()
record=dest/'process-exits.json';put(record,dict(order=262,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor))
if args.reviewed:
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 receipt=w.parent/'262-map-slot-released.json'
 observations=r(w/'manual-current-standalone.json');assert set(observations)=={v['filename'] for v in fresh['views']}
 for frame in fresh['views']:
  row=observations[frame['filename']];assert row['observation'].strip() and row['sha256']==frame['sha256']
 save(w/'manual-current-standalone.json','current-standalone/manual-visual-review.json')
 if not receipt.exists():put(receipt,dict(order=262,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,views_reviewed=True,real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),review_sha256=h(note),screenshots=images,reports=rows,actual_saved_downloads=fresh['downloads'],current_standalone_sha256=h(w/'current-standalone/closed.json'),manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 print(receipt,h(receipt))
if args.submit:
 assert args.reviewed and (w.parent/'262-map-slot-released.json').is_file()
 doc=a/'README.md';base=doc.read_text().rstrip();section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31262/process-exits.json) · [旧城对照](city-31262/map-before.png) · [中华路钟楼正立面](city-31262/map-zhonghua-clock-street.png) · [钟面与角柱](city-31262/map-clock-face-and-columns.png) · [远档](city-31262/map-distant.png)'
 if '## 正式城市地图复核' not in base:
  tmp=doc.with_name('.README.262-new.md');tmp.write_text(base+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
 else:assert section in base
 names=[v['filename']for v in r(w/'standalone-originals.json')['views']]
 subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','262','README.md','viewer.json','city-31262',*names],check=True)
