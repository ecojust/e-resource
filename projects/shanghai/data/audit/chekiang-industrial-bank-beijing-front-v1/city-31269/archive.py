"""Archive the genuine Chekiang Industrial Bank map sessions and the exact historical viewer bytes; issue the physical handoff only after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/chekiang-industrial-bank-beijing-front-v1');e=w/'isolated-evidence';dest=a/'city-31269'
ap=argparse.ArgumentParser();ap.add_argument('--reviewed',action='store_true');ap.add_argument('--submit',action='store_true');args=ap.parse_args()
r=lambda f:json.loads(f.read_bytes());h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
plain=r;file_hash=h
def actual(f):return __import__('gzip').decompress(Path(str(f)+'.gz').read_bytes())
r=lambda f:plain(f)if f.exists()else json.loads(actual(f))
h=lambda f:file_hash(f)if f.exists()else hashlib.sha256(actual(f)).hexdigest()
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
for f in ['check-chekiang-bank.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','standalone-visual-review.json','isolated-inputs.json','archive.py']:save(w/f)
pr268=a.parent/'somekh-building-street-corner-v1/31268-all-http.json'
for n in [268,269]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=(pr268 if n==268 else Path('/tmp/shanghai-yongjia-porch/scenes/269-all-http.json'));assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-268/268-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=268 if name=='control'else 269
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==h(w/'check-chekiang-bank.cjs')==actual['scriptSha256']
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
assets={k:y for k,y in files.items() if '/huangpu-chekiang-industrial-bank-beijing-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==39
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19569))!=0
ind=w/'standalone-31269';doc=r(ind/'viewer.json');g=r(w/'standalone-closed.json')
assert g['passed'] and g['exit']==0 and not g['remaining_chromium'] and g['chromium_pids'] and g['report_sha256']==h(ind/'viewer.json')
assert doc['passed'] and doc['base']=='http://127.0.0.1:31269/' and len(doc['views'])==6 and not doc['pageErrors']
for shot in doc['views']:
 im=ind/shot['filename'];assert h(im)==shot['sha256'];save(im,'standalone/'+im.name)
save(ind/'viewer.json','standalone/viewer.json');save(w/'standalone-closed.json','standalone/closed.json')
for role,item in doc['downloads'].items():assert item['sha256']in {q['sha256']for q in assets.values()}
record=dest/'process-exits.json';put(record,dict(order=269,id=pins['id'],actual_standalone_report_sha256=h(ind/'viewer.json'),standalone_process=g,standalone_views=doc['views'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor))
if args.reviewed:
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 receipt=w.parent/'269-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=269,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,views_reviewed=True,standalone_process=g,standalone_screens=doc['views'],standalone_sha256=h(ind/'viewer.json'),real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),review_sha256=h(note),screenshots=images,reports=rows,actual_saved_downloads=assets,manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 helper=Path('/workspace/.e-resource-recovery/placement/host269-448/handoff.py')
 assert h(helper)=='26ba99fa9c0a6bcfdef2350c7d29f8adcd276f3e93ced08a05aeea2e4279f9f7'
 subprocess.run([__import__('sys').executable,'-Bu',helper,'run'],check=True)
 print(receipt,h(receipt))
if args.submit:
 assert args.reviewed and (w.parent/'269-map-slot-released.json').is_file()
 doc=a/'README.md';base=doc.read_text().rstrip();section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31269/process-exits.json) · [旧城对照](city-31269/map-before.png) · [北京东路第一西窗跨](city-31269/map-first-west-beijing-bay.png) · [双组方回纹几何](city-31269/map-terracotta-double-fret.png) · [远档](city-31269/map-distant.png)'
 if '## 正式城市地图复核' not in base:
  tmp=doc.with_name('.README.269-new.md');tmp.write_text(base+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
 else:assert section in base
 names=[v['filename']for v in r(w/'standalone-originals.json')['views']]
 subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','269','README.md','viewer.json','city-31269',*names],check=True)
