"""Archive the genuine Shanghai Money Guild Ningbo Road frontage map sessions and the exact historical viewer bytes; issue the physical handoff only after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/shanghai-money-guild-front-v1');e=w/'isolated-evidence';u=Path('/dev/shm/moneyguild277-live');out=u/'verified-audit';dest=out/'city-31277'
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
pins=r(w/'live-inputs.json');intake=r(w/'signed-comparison.json');assert all(h(w/k)==v for k,v in pins['frozen_program_and_inputs'].items())
for f in ['check-money-guild.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','source-proof.json','verify-standalone.py','standalone-visual-review.json','isolated-inputs.json','archive.py']:save(w/f)
pr276=Path('/tmp/shanghai-yongjia-porch/scenes/276-all-http.json')
for n in [276,277]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=(pr276 if n==276 else a/'31277-all-http.json');assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-276/276-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=276 if name=='control'else 277
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
  floor=actual['ground'];assert len(floor)==len(cases['ground']) and all(v['found']==v['expected'] for v in floor)
 if name=='distant':
  assert v['asset']['variant']=='distant'
  first=u/'failed-attempts/distant-after-frontage'
  prior=r(first/'failed-exit.json');front=r(first/'main-browser.json')
  assert prior['exit_code']!=0 and not prior['remaining'] and prior['report_sha256']==h(first/'main-browser.json') and prior['source_code_sha256']==h(first/'actual-driver.cjs')==front['scriptSha256']
  wide=front['fullFrontage'];transition=actual['transition'];assert transition['before']['variant']=='full' and transition['after']['variant']=='distant'
  assert wide['state']['asset']['variant']=='full' and wide['state']['asset']['verifiedAsset']['modelId']==pins['id']
  for row in [wide['image'],wide['webgl']]:
   picture=first/row['file'];assert h(picture)==row['sha256'] and picture.stat().st_size==row['bytes'];save(picture)
  display=wide['display'];picture=first/display['displayImage'];assert h(picture)==display['displayImageSha256'];save(picture)
  clear=front['architecturalPixels'][0]['attempts'][-1]['targets'];assert len(clear)==5 and all(x['clear'] for x in clear)
  note_wide=u/'supplemental-frontage.json';assert r(note_wide)['sha256']==wide['image']['sha256'] and r(note_wide)['observation']
  save(note_wide);save(first/'actual-driver.cjs','check-front-distance.cjs');save(first/'failed-exit.json','frontage-session/failed-exit.json');save(first/'main-browser.json','frontage-session/main-browser.json');save(folder/'actual-driver.cjs','check-small-distance.cjs')
 im,=actual['screenshots'];impath=folder/im['file'];assert h(impath)==im['sha256'] and impath.stat().st_size==im['bytes'];save(impath);images.append(im)
 for rec in actual['files']:
  f=rec['file'];assert rec['sha256']==sig.get(f,native.get(f,{}).get('sha256'));files[f]=rec
 save(path,'actual-browser-phases/'+name+'.json');save(old,'actual-browser-phases/'+name+'-closed.json')
 rows.append({'phase':name,'exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':h(path),'closed_sha256':h(old)})
assets={k:y for k,y in files.items() if '/huangpu-shanghai-money-guild-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==227
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19577))!=0
ind=w/'standalone-31277';doc=r(ind/'viewer.json');g=r(w/'standalone-closed.json')
assert g['passed'] and g['exit']==0 and not g['remaining_chromium'] and g['chromium_pids'] and g['report_sha256']==h(ind/'viewer.json')
assert doc['passed'] and doc['base']=='http://127.0.0.1:31277/' and len(doc['views'])==6 and not doc['pageErrors']
for shot in doc['views']:
 im=ind/shot['filename'];assert h(im)==shot['sha256'];save(im,'standalone/'+im.name)
save(ind/'viewer.json','standalone/viewer.json');save(w/'standalone-closed.json','standalone/closed.json')
for role,item in doc['downloads'].items():assert item['sha256']in {q['sha256']for q in assets.values()}
import sys
maker=Path('/workspace/shanghai-publisher-preservation/city-277')
fresh=w/'current-standalone/closed.json'
cur=r(fresh); crep=Path(cur['report']); cres=r(crep)
assert cur['exit_code']==0 and cur['passed'] and not cur['remaining'] and cur['chromium'] and cur['prior_sha256']==h(old)
assert cur['report_sha256']==h(crep) and cres['passed'] and not cres['pageErrors'] and len(cres['views'])==4
assert h(maker/'formal-viewer.cjs')==cres['scriptSHA256']==cur['driver_sha256']
assert set(cres['downloads'])=={'raw','full','lod','native'} and cres['downloads']==cur['downloads']
for role,dl in cres['downloads'].items():
 actual_file=crep.parent/'saved'/dl['file']
 assert dl['saveAsVerified'] and h(actual_file)==dl['sha256']==doc['downloads'][role]['sha256'] and actual_file.stat().st_size==dl['bytes']
for shot in cres['views']:
 im=crep.parent/shot['filename'];assert h(im)==shot['sha256'];save(im,'current-standalone/'+im.name)
for f in (crep,fresh,Path(cur['proof'])):save(f,'current-standalone/'+f.name)
for f in (w/'live-inputs.json',w/'capture-live.py',w/'sequence-live.py',w/'check-money-guild-live.cjs',w/'check-parent-276-live.py',w/'archive-live.py',u/'admit-live.py',w/'isolated-inputs-recovered.json',w/'archive-original.py',w/'archive-recovered.py',w/'sequence-recovered.py',w/'capture-recovered.py',maker/'actual-viewer.py',maker/'formal-viewer.cjs'):save(f,f.name)
guests={}
for kind,stage in [('native','control'),('viewer','mobile-pin')]:
 f=Path('/tmp/sinan-even342')/(kind+'-closed.json');actual_guest=r(f);parent=e/stage/'closed.json'
 assert actual_guest['passed'] and actual_guest['all_processes_closed'] and actual_guest['exit_code']==0
 assert actual_guest['host_receipt_sha256']==h(parent) and actual_guest['host_report_sha256']==r(parent)['report_sha256']
 assert not actual_guest['remaining']
 if kind=='native':assert len(actual_guest['blender_pids'])>=2 and len(actual_guest['assets'])==4
 else:assert actual_guest['views']==6 and actual_guest['downloads']==4 and len(set(actual_guest['node_pids']))==2
 guests[kind]={'file':'guest/'+f.name,'sha256':h(f),'host_phase':stage,'host_sha256':h(parent)}
 save(f,guests[kind]['file'])
record=dest/'process-exits.json' ;put(record,dict(order=277,id=pins['id'],full_frontage=wide,variant_transition=transition,guest_342=guests,actual_standalone_report_sha256=h(ind/'viewer.json'),standalone_process=g,standalone_views=doc['views'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,current_standalone=cur,current_four_downloads=cres['downloads'],screens=images,ground=floor))
if args.reviewed:
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 ordinary_record=a/'city-31277'/record.name;ordinary_record.parent.mkdir(exist_ok=True)
 if not ordinary_record.exists():shutil.copyfile(record,ordinary_record)
 assert h(ordinary_record)==h(record)
 current=r(Path('/dev/shm/field277-independent/visual-review.json'))['images']
 former=r(Path('/dev/shm/field277-independent/earlier-six-review.json'))['images']
 checks={im['file']:im['sha256'] for im in images}
 checks.update({'standalone/'+im['filename']:im['sha256'] for im in cres['views']})
 assert {n:row['sha256'] for n,row in current.items()}==checks and len(current)==14
 assert {n:row['sha256'] for n,row in former.items()}=={im['filename']:im['sha256'] for im in doc['views']} and len(former)==6
 for n,row in {**current,**former}.items():assert row['observation'] in note.read_text()
 receipt=w.parent/'277-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=277,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,views_reviewed=True,standalone_process=g,standalone_screens=doc['views'],standalone_sha256=h(ind/'viewer.json'),real_browser_process_exits=rows,report_sha256=h(record),evidence=str(ordinary_record),guest_342=guests,review_sha256=h(note),screenshots=images,reports=rows,current_standalone=cur,actual_saved_downloads=cres['downloads'],manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 save(receipt,'slot-released.json')
 save(note,'observations.md')
 print(receipt,h(receipt))
