"""Archive the actual Carlowitz city and standalone views after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/carlowitz-jiujiang-front-v1');e=w/'isolated-evidence';dest=a/'city-31233'
ap=argparse.ArgumentParser();ap.add_argument('--reviewed',action='store_true');ap.add_argument('--submit',action='store_true');args=ap.parse_args()
r=lambda f:json.loads(f.read_bytes());h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,rel=None):
 t=dest/(rel or f.name);t.parent.mkdir(exist_ok=True,parents=True)
 if not t.exists():
  try:os.link(f,t)
  except OSError:shutil.copyfile(f,t)
 assert h(t)==h(f);return t
def put(f,q):
 if f.exists():assert r(f)==q;return
 z=f.with_suffix('.temp');z.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');z.replace(f)
pins=r(w/'isolated-inputs.json');intake=r(w/'signed-comparison.json');assert all(h(w/k)==v for k,v in pins['frozen_program_and_inputs'].items())
for f in ['check-carlowitz.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','isolated-inputs.json','archive.py','check-pixels.py','pixel-inspection.json']:save(w/f)
for n in [232,233]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-all-http.json';assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
for file in (w/'real-drivers').glob('*.cjs'):save(file,'actual-physical-map-drivers/'+file.name)
for file in ('cdp-city-page-233.cjs','nine-case-neighbors.json','read-control-device.cjs','finish-control-evidence.py'):save(w/file)
for file in (w/'control-device-followup').iterdir():
 if file.name!='node.log':save(file,'verified-control-input/'+file.name)
for label in ('mobile','desktop'):
 pointer=w/('prior-'+label+'-tap-and-route.json')
 binding=r(pointer)
 for path_key,sha_key in [('report','reportSha256'),('close','closeSha256')]:
  assert h(w/binding[path_key])==binding[sha_key]
 save(pointer,'actual-browser-phases/'+pointer.name)
for item in ('mobile-card-close-intervention.json','mobile-pin-close-intervention.json'):
 save(w/item,'actual-browser-phases/'+item)
save(w/'second-distant-within-near-threshold/distant/actual-camera-eye.json','actual-browser-phases/first-measured-distant-eye.json')
save(w/'confirm-street-presented-frame.py','street-original-camera/confirm-street-presented-frame.py')
for source in (w/'street-presented-frame-reconciliation').iterdir():save(source,'street-original-camera/'+source.name)
for stage in pins['stage_order']:
 for diagnostic in ('physical-process-exit.json','background-bund-transfers.json'):
  measured=e/stage/diagnostic
  if measured.exists():save(measured,'actual-browser-phases/'+stage+'-'+diagnostic)
 shutdown=e/stage/'browser-shutdown.json'
 if shutdown.exists():save(shutdown,'actual-browser-phases/'+stage+'-shutdown.json')
from importlib.machinery import SourceFileLoader
supplement=SourceFileLoader('desktop_photo',str(w/'confirm-destination-picture.py')).load_module().read(w)
for label in ('check-mouse-destination-pixels.cjs','capture-mouse-destination.py','obtain-destination-picture.py','confirm-destination-picture.py','desktop-pin-automatic-camera.json'):
 save(w/label,'mouse-destination-supplement/'+label)
for file in [w/'desktop-pin-visual-supplement/selected.json', *(f for f in supplement[0].iterdir() if f.suffix=='.json')]:
 save(file,'mouse-destination-supplement/'+file.name)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-232/232-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=232 if name=='control'else 233
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==actual['scriptSha256'] and c['source_code_sha256'] in {h(w/'check-carlowitz.cjs'),*(h(p) for p in (w/'real-drivers').glob('*.cjs'))}
 assert c['predecessor']['sha256']==h(old);old=folder/'closed.json'
 if name in ('mobile-pin','desktop-pin'):
  origin=actual['priorRouteStart'];assert origin['fromActualDirectoryLink'] and origin['id']==actual['localExisting'] and origin['normalStartupFinished']
 else:assert actual['realDirectoryEntry']['pointer']['trusted']
 assert actual['completed'] and not (actual['failed'] or actual['errors'] or actual['warnings']) and actual['phase']==name and actual['server']==f'http://127.0.0.1:{31000+n}/'
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
 im,=actual['screenshots'];impath=folder/im['file']
 if name=='desktop-pin':
  save(impath,'mouse-destination-supplement/original-loading-frame.png')
  im=supplement[3];impath=supplement[0]/im['file']
 assert h(impath)==im['sha256'] and impath.stat().st_size==im['bytes'];save(impath);images.append(im)
 for rec in actual['files']:
  f=rec['file'];assert rec['sha256']==sig.get(f,native.get(f,{}).get('sha256'));files[f]=rec
 save(path,'actual-browser-phases/'+name+'.json');save(old,'actual-browser-phases/'+name+'-closed.json')
 rows.append({'phase':name,'exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':h(path),'closed_sha256':h(old)})
i=e/'independent';ic=r(i/'closed.json');iv=r(i/'viewer.json')
assert ic['passed'] and ic['exit_code']==0 and not ic['remaining_chromium'] and ic['observed_chromium_pid_and_starttime'] and ic['report_sha256']==h(i/'viewer.json')
assert len(iv['views'])==4 and len(iv['downloads'])==4
for picture in iv['views']:assert h(i/picture['filename'])==picture['sha256'];save(i/picture['filename'],'standalone/'+picture['filename'])
for page in ['viewer.json','closed.json']:save(i/page,'standalone/'+page)
for evidence in ['source-ray-sightlines.json','camera-sightlines.json','independent.py']:save(w/evidence)
for evidence in ['formal-viewer.cjs','formal-viewer-sources.json']:save(w/evidence,'standalone/'+evidence)
rows.append({'phase':'independent','exit_code':0,'finished':ic['finished'],'node':ic['node_pid'],'chromium':ic['observed_chromium_pid_and_starttime'],'report_sha256':h(i/'viewer.json'),'closed_sha256':h(i/'closed.json')})
assets={k:y for k,y in files.items() if '/huangpu-carlowitz-jiujiang-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==pins['ground_checks']
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19533))!=0
record=dest/'process-exits.json';put(record,dict(order=233,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor))
if args.reviewed:
 assert r(w/'pixel-inspection.json')['passed']
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 receipt=w.parent/'233-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=233,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,sessions=rows,reports={x['phase']:x for x in rows},real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 print(receipt,h(receipt))
if args.submit:
 assert args.reviewed and (w.parent/'233-map-slot-released.json').is_file()
 doc=a/'README.md';base=doc.read_text().rstrip();section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31233/process-exits.json) · [旧城对照](city-31233/map-before.png) · [九江路街面立面](city-31233/map-jiujiang-street-front.png) · [东端两跨弧窗与石栏](city-31233/map-eastern-bowed-windows.png) · [远档](city-31233/map-distant.png)'
 if '## 正式城市地图复核' not in base:
  tmp=doc.with_name('.README.233-new.md');tmp.write_text(base+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
 else:assert section in base
 names=[v['filename']for v in r(w/'standalone-originals.json')['views']]
 subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','233','README.md','viewer.json','city-31233',*names],check=True)
