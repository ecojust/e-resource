"""Archive the genuine Brookside map sessions and the exact historical viewer bytes; issue the physical handoff only after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/brookside-apartments-v1');e=w/'isolated-evidence';dest=a/'city-31203'
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
for f in ['check-brookside.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','historical-text-continuity.json','isolated-inputs.json','archive.py']:save(w/f)
for name,digest in r(w/'geometry-inputs.json')['frozen_program_and_inputs'].items():assert h(w/name)==digest
for name in ['check-brookside-detail.cjs','capture-geometry.py','sequence-geometry.py','geometry-inputs.json','preserve-retried-phases.py']:save(w/name)
for n in [202,203]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/clements202/202-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=202 if name=='control'else 203
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 js=w/('check-brookside-detail.cjs' if name in ['street','roof','crown','wings','distant'] else 'check-brookside.cjs')
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==h(js)==actual['scriptSha256']
 assert c['predecessor']['sha256']==h(old);old=folder/'closed.json'
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
 im,=actual['screenshots'];impath=folder/im['file'];assert h(impath)==im['sha256'] and impath.stat().st_size==im['bytes'];save(impath);images.append(im)
 for rec in actual['files']:
  f=rec['file'];assert rec['sha256']==sig.get(f,native.get(f,{}).get('sha256'));files[f]=rec
 save(path,'actual-browser-phases/'+name+'.json');save(old,'actual-browser-phases/'+name+'-closed.json')
 rows.append({'phase':name,'exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':h(path),'closed_sha256':h(old)})
for n,sig in r(w/'centered-inputs.json')['frozen_program_and_inputs'].items():assert h(w/n)==sig
for n in ['check-brookside-centered.cjs','capture-centered-far.py','centered-inputs.json','offer-final268.py']:save(w/n)
folder=e/'centered-distant';c=r(folder/'closed.json');actual=r(folder/'main-browser.json');v,=actual['views']
assert c['exit_code']==0 and c['cdp_closed'] and not c['remaining_chromium'] and c['observed_chromium_pid_and_starttime']
assert actual['completed'] and not(actual['failed'] or actual['errors'] or actual['warnings'])
assert c['source_code_sha256']==h(w/'check-brookside-centered.cjs')==actual['scriptSha256'] and c['report_sha256']==h(folder/'main-browser.json')
assert c['predecessor']['sha256']==h(old) and actual['server']=='http://127.0.0.1:31203/' and actual['phase']=='distant'
assert v['asset']['variant']=='distant' and v['asset']['verifiedAsset']['sha256']==r(w/'203-production.json')['files'][v['asset']['verifiedAsset']['file']]
assert v['asset']['visible'] and not v['contextLost'] and v['glError']==0 and v['viewport']==[620,620]
im,=actual['screenshots'];assert h(folder/im['file'])==im['sha256'];save(folder/im['file']);images.append(im)
for name in ['closed.json','main-browser.json']:save(folder/name,'actual-browser-phases/centered-distant-'+name)
rows.append({'phase':'centered-distant','exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':c['report_sha256'],'closed_sha256':h(folder/'closed.json')})
assets={k:y for k,y in files.items() if '/jingan-brookside-apartments/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==16
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19503))!=0
record=dest/'process-exits.json';put(record,dict(order=203,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor))
if args.reviewed:
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 receipt=w.parent/'203-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=203,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 print(receipt,h(receipt))
if args.submit:
 assert args.reviewed and (w.parent/'203-map-slot-released.json').is_file()
 doc=a/'README.md';base=doc.read_text().rstrip();section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31203/process-exits.json) · [旧城对照](city-31203/map-before.png) · [南花园立面](city-31203/map-south-garden-facade.png) · [顶层券廊](city-31203/map-open-upper-arcade-and-pediment.png) · [远档](city-31203/map-distant-centered.png)'
 if '## 正式城市地图复核' not in base:
  tmp=doc.with_name('.README.203-new.md');tmp.write_text(base+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
 else:assert section in base
 names=[v['filename']for v in r(w/'standalone-originals.json')['views']]
 subprocess.run(['python','-B',w/'preserve-retried-phases.py'],check=True)
 extra=['archived-browser-attempts.json'] if (a/'archived-browser-attempts.json').is_file() else []
 assert h(a/'readme-render-equivalence.json')=='b105219c37bc9a38193987bfe9412a984e73905efaef57ff92f8a75ecf1f8abd'
 extra.append('readme-render-equivalence.json')
 subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','203','README.md','viewer.json','city-31203',*names,*extra],check=True)
