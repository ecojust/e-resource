"""Archive the genuine Asia Realty map sessions and the exact historical viewer bytes; issue the physical handoff only after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/asia-realty-front-v1');e=w/'isolated-evidence';dest=a/'city-31242'
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
for f in ['check-asia-realty.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','isolated-inputs.json','archive.py']:save(w/f)
for n in [241,242]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-all-http.json';assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-241/241-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=241 if name=='control'else 242
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==h(w/'check-asia-realty.cjs')==actual['scriptSha256']
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
assets={k:y for k,y in files.items() if '/huangpu-asia-realty-sichuan-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==26
ordinary=e/'independent';closure=r(ordinary/'closed.json');viewer=r(ordinary/'viewer.json')
assert closure['passed'] and closure['exit_code']==0 and closure['all_children_exited'] and not closure['remaining_chromium']
assert closure['host_sha256']==h(e/'distant/closed.json') and closure['report_sha256']==h(ordinary/'viewer.json')
assert viewer['passed'] and len(viewer['views'])==6 and len(viewer['downloads'])==4
for image in viewer['views']:
 actual=ordinary/image['file'];assert h(actual)==image['sha256'];save(actual,'ordinary-page/'+image['file'])
for x in viewer['downloads'].values():
 actual=ordinary/x['saved'];assert x['saveAsVerified'] and actual.stat().st_size==x['bytes'] and h(actual)==x['sha256']
for f in ['closed.json','viewer.json']:save(ordinary/f,'ordinary-page/'+f)
for f in ['verify-normal-page.cjs','after-distant-page.py']:save(w/f)
record=dest/'process-exits.json';put(record,dict(order=242,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor,ordinary_page=closure,actual_saved_downloads=viewer['downloads']))
if args.reviewed:
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 receipt=w.parent/'242-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=242,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,real_browser_process_exits=rows+[closure],actual_saved_downloads=viewer['downloads'],ordinary_page_sha256=h(ordinary/'viewer.json'),report_sha256=h(record),evidence=str(record),review_sha256=h(note),screenshots=images+viewer['views'],views_reviewed=True,reports=rows+[closure],manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 print(receipt,h(receipt))
if args.submit:
 assert args.reviewed and (w.parent/'242-map-slot-released.json').is_file()
 doc=a/'README.md';base=doc.read_text().rstrip();section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31242/process-exits.json) · [旧城对照](city-31242/map-before.png) · [四川中路凹入口与门柱](city-31242/map-sichuan-recessed-doorways.png) · [南端入口及其柱窗](city-31242/map-southern-column-doorway.png) · [远档](city-31242/map-distant.png)'
 if '## 正式城市地图复核' not in base:
  tmp=doc.with_name('.README.242-new.md');tmp.write_text(base+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
 else:assert section in base
 names=[v['filename']for v in r(w/'standalone-originals.json')['views']]
 subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','242','README.md','viewer.json','city-31242',*names],check=True)
