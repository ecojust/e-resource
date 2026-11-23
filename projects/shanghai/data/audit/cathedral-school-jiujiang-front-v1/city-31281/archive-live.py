"""Archive the genuine Cathedral School Jiujiang Road twin-gabled frontage map sessions and the exact historical viewer bytes; issue the physical handoff only after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/cathedral-school-jiujiang-front-v1');e=w/'isolated-evidence';dest=Path('/dev/shm/jiujiang281-live/verified-audit/city-31281')
ap=argparse.ArgumentParser();ap.add_argument('--reviewed',action='store_true');ap.add_argument('--submit',action='store_true');args=ap.parse_args()
r=lambda f:json.loads(f.read_bytes());h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
plain=r;file_hash=h
def actual_bytes(f):return __import__('gzip').decompress(Path(str(f)+'.gz').read_bytes())
r=lambda f:plain(f)if f.exists()else json.loads(actual_bytes(f))
h=lambda f:file_hash(f)if f.exists()else hashlib.sha256(actual_bytes(f)).hexdigest()
def save(f,rel=None):
 t=dest/(rel or f.name);t.parent.mkdir(exist_ok=True,parents=True)
 if not t.exists():
  try:
   if f.is_symlink():shutil.copyfile(f,t)
   else:os.link(f,t)
  except OSError:shutil.copyfile(f,t)
 assert h(t)==h(f);return t
def put(f,q):
 if f.exists():assert r(f)==q;return
 z=f.with_suffix('.temp');z.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');z.replace(f)
pins=r(w/'isolated-inputs.json');intake=r(w/'signed-comparison.json');__import__('frozen_inputs').verify(w)
for f in ['check-jiujiang-school.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','source-proof.json','verify-standalone.py','standalone-visual-review.json','isolated-inputs.json','archive.py','archive-recovered.py','capture-recovered.py','sequence-recovered.py','keep-saved.cjs','reopen-sites.py','ordinary-retained.py','school-viewer-retained.cjs','frozen_inputs.py']:save(w/f)
for program in sorted(w.glob('check-jiujiang-*.cjs')):save(program)
save(w/'school-viewer-live.cjs')
pr280=Path('/workspace/e-resource/projects/shanghai/data/audit/ta-ching-bank-southwest-tower-v1/31280-all-http.json')
for n in [280,281]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=(pr280 if n==280 else a/'31281-all-http.json');assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-280/280-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=280 if name=='control'else 281
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
 save(path,'actual-browser-phases/'+name+'.json');save(old,'actual-browser-phases/'+name+'-closed.json')
 rows.append({'phase':name,'exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':h(path),'closed_sha256':h(old)})
assets={k:y for k,y in files.items() if '/huangpu-cathedral-school-jiujiang-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==68
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19581))!=0
ind=w/'standalone-31281';doc=r(ind/'viewer.json');g=r(w/'current-standalone-closed.json')
assert g['passed'] and g['exit']==0 and not g['remaining_chromium'] and g['chromium_pids'] and g['report_sha256']==h(ind/'viewer.json')
assert doc['passed'] and doc['base']=='http://127.0.0.1:31281/' and len(doc['views'])==6 and not doc['pageErrors']
for shot in doc['views']:
 im=ind/shot['filename'];assert h(im)==shot['sha256'];save(im,'standalone/'+im.name)
save(ind/'viewer.json','standalone/viewer.json');save(w/'current-standalone-closed.json','standalone/closed.json')
for role,item in doc['downloads'].items():
  saved=ind/'saved'/item['file']
  assert item['actualSaved'] and item['sha256']in {q['sha256']for q in assets.values()} and h(saved)==item['sha256'] and saved.stat().st_size==item['bytes']
record=dest/'process-exits.json';put(record,dict(order=281,id=pins['id'],actual_standalone_report_sha256=h(ind/'viewer.json'),standalone_process=g,standalone_views=doc['views'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor))
if args.reviewed:
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 receipt=w.parent/'281-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=281,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,views_reviewed=True,standalone_process=g,standalone_screens=doc['views'],standalone_sha256=h(ind/'viewer.json'),real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),review_sha256=h(note),screenshots=images,reports=rows,actual_saved_downloads=assets,manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
