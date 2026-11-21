"""Archive the actual Yanqing Road 130 city and standalone views after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path('/tmp/shanghai-main-228/formal-31228');a=Path('/workspace/e-resource/projects/shanghai/data/audit/yanqing-road-130-v1');e=w/'isolated-evidence';dest=a/'city-31228'
ap=argparse.ArgumentParser();ap.add_argument('--reviewed',action='store_true');ap.add_argument('--submit',action='store_true');args=ap.parse_args()
r=lambda f:json.loads(f.read_bytes());h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,rel=None):
 t=dest/(rel or f.name);t.parent.mkdir(exist_ok=True,parents=True)
 if not t.exists():
  if f.is_symlink():shutil.copyfile(f,t)
  else:
   try:os.link(f,t)
   except OSError:shutil.copyfile(f,t)
 assert not t.is_symlink()
 assert h(t)==h(f);return t
def put(f,q):
 if f.exists():assert r(f)==q;return
 z=f.with_suffix('.temp');z.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');z.replace(f)
pins=r(w/'isolated-inputs.json');intake=r(w/'signed-comparison.json');assert all(h(w/k)==v for k,v in pins['frozen_program_and_inputs'].items())
for f in ['check-garden-front.cjs','check-garden-distant-760m.cjs','distant-budget.cjs','low-memory.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','isolated-inputs.json','archive.py','check-pixels.py','pixel-inspection.json']:save(w/f)
for n in [227,228]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-all-http.json';assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-227/227-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=227 if name=='control'else 228
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==h(w/('check-garden-distant-760m.cjs' if name=='distant' else 'check-garden-front.cjs'))==actual['scriptSha256']
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
 save(path,'actual-browser-phases/'+name+'.json');save(old,'actual-browser-phases/'+name+'-closed.json')
 rows.append({'phase':name,'exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':h(path),'closed_sha256':h(old)})
distant=r(e/'distant/main-browser.json');supplement=rows[-1]
assert distant['evidenceMode']=='separate-real-sessions' and not distant['single_session_passed']
source=distant['originalRendering'];failed=dest/source['physical'];partial=dest/source['report']
assert r(failed)['exit_code']==source['returned']==1 and h(failed)==source['physical_sha256']
original=r(partial);assert h(partial)==source['report_sha256'] and original['completed'] is False and original['views']==distant['views'] and original['screenshots']==distant['screenshots']
assert r(failed)['source_code_sha256']==source['driver_sha256']
driver=Path('/dev/shm/scene228-current/distant-formal-screenshot-before-reading-input-device/check-garden-distant-760m.cjs')
assert h(driver)==source['driver_sha256'];save(driver,'actual-browser-phases/distant-image-driver.cjs')
point=distant['supplemental']['realPointer'];assert point['trusted'] and point['type']=='mouse' and len(distant['downloads'])==4
supplement.update(evidence_mode=distant['evidenceMode'],single_session_passed=False,rendered_frame=source,verified_in_this_process=distant['supplemental'],saved_downloads=distant['downloads'])
i=e/'independent';ic=r(i/'closed.json');iv=r(i/'viewer.json')
assert ic['passed'] and ic['exit_code']==0 and not ic['remaining_chromium'] and ic['observed_chromium_pid_and_starttime'] and ic['report_sha256']==h(i/'viewer.json')
assert len(iv['views'])==4 and len(iv['downloads'])==4
for picture in iv['views']:assert h(i/picture['filename'])==picture['sha256'];save(i/picture['filename'],'standalone/'+picture['filename'])
for page in ['viewer.json','closed.json']:save(i/page,'standalone/'+page)
for evidence in ['check-special-camera-sightlines.py','actual-sightline-inputs.py','trace-actual-city.mjs','special-camera-sightlines.json','actual-city-ray-inputs.json','actual-camera-city-triangles.json','independent.py']:save(w/evidence)
rows.append({'phase':'independent','exit_code':0,'finished':ic['finished'],'node':ic['node_pid'],'chromium':ic['observed_chromium_pid_and_starttime'],'report_sha256':h(i/'viewer.json'),'closed_sha256':h(i/'closed.json')})
assets={k:y for k,y in files.items() if '/xuhui-yanqing-road-130-residence/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==16
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19528))!=0
record=dest/'process-exits.json';put(record,dict(order=228,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor))
if args.reviewed:
 assert r(w/'pixel-inspection.json')['passed']
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 receipt=w.parent/'228-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=228,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,sessions=rows,real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 print(receipt,h(receipt))
if args.submit:
 assert args.reviewed and (w.parent/'228-map-slot-released.json').is_file()
 doc=a/'README.md';base=doc.read_text().rstrip();section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31228/process-exits.json) · [旧城对照](city-31228/map-before.png) · [南向庭院立面](city-31228/map-south-garden-facade.png) · [前廊圆柱与内退的玻璃门窗](city-31228/map-terrace-columns-and-recessed-hall.png) · [远档](city-31228/map-distant.png)'
 if '## 正式城市地图复核' not in base:
  tmp=doc.with_name('.README.228-new.md');tmp.write_text(base+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
 else:assert section in base
 names=[v['filename']for v in r(w/'standalone-originals.json')['views']]
 subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','228','README.md','viewer.json','city-31228',*names],check=True)
