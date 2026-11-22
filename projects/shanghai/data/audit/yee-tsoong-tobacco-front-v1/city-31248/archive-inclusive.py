"""Archive the Yee Tsoong riverside facade map sessions and the exact historical viewer bytes; issue the physical handoff only after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/yee-tsoong-tobacco-front-v1');e=w/'isolated-evidence';dest=a/'city-31248'
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
for f in ['check-yee-tsoong.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','standalone-visual-review.json','isolated-inputs.json','archive.py']:save(w/f)
pr247=Path('/tmp/shanghai-yongjia-porch/scenes/247-all-http.json')
for n in [247,248]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=(pr247 if n==247 else Path('/tmp/shanghai-yongjia-porch/scenes')/'248-all-http.json');assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-247/247-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=247 if name=='control'else 248
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==h(w/('check-control-compact.cjs' if name=='control' else 'check-arcade-street-elevation.cjs' if name=='arcade' else 'check-yee-tsoong.cjs'))==actual['scriptSha256']
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
assets={k:y for k,y in files.items() if '/huangpu-yee-tsoong-tobacco-northeast-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==30
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19548))!=0

author=Path('/workspace/shanghai-publisher-preservation/city-248')
browser=Path('/workspace/.e-resource-recovery/browser/248-failures')
proof=browser/'public-files-all.json'
assert h(proof)=='2604a1e1747a5a4c4988290f60ec73835dc10dcfb4ecc286567938ea6839edf7'
for rel,item in r(proof).items():
    f=Path(item['source']);assert h(f)==item['sha256'] and f.stat().st_size==item['bytes']
    save(f,Path(rel).relative_to('city-31248'))
for name in ('check-arcade-street-elevation.cjs','capture-before-arcade-reframe.py','riverside-window-row.cjs','capture-window-row.py','check-arcade-compact.cjs','capture-before-arcade.py','sequence-before-arcade.py','check-control-compact.cjs','capture-with-verified-runtime.py','sequence-with-restored-558.py','archive-inclusive.py'):
    save(w/name)
for name in ('formal-viewer.cjs','formal-viewer-sources.json','actual-viewer.py','late-313.py','after-viewer-584.py'):
    save(author/name,'current-standalone/'+name)
ordinary=w/'current-standalone/closed.json'
oco=r(ordinary);orp=Path(oco['report']);ov=r(orp)
assert oco['prior_sha256']==h(e/'distant/closed.json') and oco['exit_code']==0 and not oco['remaining'] and oco['chromium'] and oco['passed']
assert h(orp)==oco['report_sha256'] and ov['passed'] and ov['scriptSHA256']==oco['driver_sha256']==h(author/'formal-viewer.cjs')
assert ov['productionSHA256']==h(w/'248-production.json') and ov['downloads']==oco['downloads']
assert set(ov['downloads'])=={'native','raw','full','lod'}
for role,row in ov['downloads'].items():
    f=orp.parent/'saved'/row['file'];assert row['saveAsVerified'] and f.stat().st_size==row['bytes'] and h(f)==row['sha256']
    assert {k:row[k]for k in ('file','bytes','sha256')}==r(w/'standalone-originals.json')['downloads'][role]
for f in (orp,ordinary,orp.parent/'process.json'):
    save(f,'current-standalone/'+f.name)
assert ov['views']==oco['views'] and len(ov['views'])==4
assert {(item['viewport']['width'],item['role']) for item in ov['views']}=={(width,role)for width in (390,1250)for role in ('full','lod')}
for im in ov['views']:
    f=orp.parent/im['filename'];assert h(f)==im['sha256'];save(f,'current-standalone/'+f.name)
    images.append(dict(file='current-standalone/'+f.name,bytes=f.stat().st_size,sha256=h(f)))
rows.append(dict(phase='current-standalone',exit_code=0,finished=oco['finished'],node=oco['node_pid'],chromium=oco['chromium'],report_sha256=h(orp),closed_sha256=h(ordinary)))

guest=Path('/tmp/kangding313')
def keep(f,n):
    return save(f,'guest-returns/'+n+'/'+f.name)
for f in [guest/'native-closed.json',guest/'viewer-closed.json',guest/'raw-313-confirmed.json',w/'313-viewer-deferred.json',w/'313-viewer-after-584.json']:
    keep(f,'313')
denial=w/'control-path-resolution-before-313/original-host.log'
assert "report.parent==source.parent" in denial.read_text() and "AssertionError" in denial.read_text()
keep(denial,'313')
handoff=guest/'handoff'
for file in (handoff/'viewer-2329953.log',handoff/'viewer-deferred.json',handoff/'viewer-20261122T125746279483/physical-exit.json',author/'finish-313-after-archive-error.py'):
    keep(file,'313')
n313=r(guest/'native-closed.json');v313=r(guest/'viewer-closed.json')
assert all(z['passed'] and z['exit']==0 and z['remaining']==[] and z['wrapper_closed'] and z['all_processes_closed'] for z in (n313,v313))
assert len(n313['blender_pids'])==2 and n313['group_count']==30 and n313['assets']==v313['assets']
assert n313['host_receipt_sha256']==h(e/'control/closed.json') and v313['host_receipt_sha256']==h(e/'mobile-pin/closed.json')
assert (v313['views'],v313['downloads'])==(6,4) and h(Path(v313['report']))==v313['receipt_sha256']
assert r(w/'313-viewer-after-584.json')['viewer_closed_sha256']==h(guest/'viewer-closed.json')
g558=Path('/tmp/jingcun558/248-native-returned.json');b=r(g558)
assert b['passed'] and b['already_completed'] and b['previous_completed_exit']==0 and b['host_sha256']==h(e/'desktop-pin/closed.json') and b['earlier_sha256']==h(Path(b['earlier']))
for f in [g558,Path(b['earlier']),g558.parent/'recheck-after-248.py']:keep(f,'558')
d=Path('/dev/shm/root-maylee584/development-native');f584=d/'early-development-returned.json';rr=r(f584)
assert rr['passed'] and rr['exit_code']==0 and rr['all_children_exited'] and rr['remaining_children']==[] and rr['host_sha256']==h(ordinary)
assert rr['physical_sha256']==h(d/'physical.json')
for f in [f584,d/'physical.json',d/'closed.json']:keep(f,'584')
prev=Path('/tmp/shanyin274-662/early-247-native-returned.json');ret={}
for order,home in [(666,'/tmp/duolun123-666'),(670,'/tmp/sanduo670')]:
    f=Path(home)/'early-248-native-returned.json';out=r(f)
    assert out['passed'] and out['all_children_exited'] and not out['remaining_children'] and out['previous_sha256']==h(prev)
    assert len(out['four_assets'])==4 and out['host_sha256']==h(w/'first-control-renderer-crash/failed-exit.json')
    keep(f,str(order));ret[str(order)]=h(f);prev=f
supp=w/'riverside-window-row'
reframed=r(supp/'closed.json');actual=r(supp/'main-browser.json')
assert reframed['exit_code']==0 and reframed['cdp_closed'] and reframed['remaining_chromium']==[]
assert reframed['predecessor']['sha256']==h(w/'313-viewer-after-584.json')
assert h(supp/'main-browser.json')==reframed['report_sha256'] and actual['completed']
assert h(w/'riverside-window-row.cjs')==actual['scriptSha256']==reframed['source_code_sha256']
assert actual['catalog']['sha256']==r(w/'248-production.json')['files']['data/candidate-city-integrations.json'] and actual['server']=='http://127.0.0.1:31248/'
assert actual['views'][0]['asset']['visible'] and actual['views'][0]['asset']['variant']=='full' and len(actual['ground'])==30 and all(x['expected']==x['found'] for x in actual['ground'])
for item in [*actual['screenshots'],actual['canvasCapture']]:
    shot=supp/item['file'];assert h(shot)==item['sha256'] and shot.stat().st_size==item['bytes']
    rel='riverside-window-row/'+shot.name;save(shot,rel);images.append(dict(file=rel,sha256=h(shot),bytes=shot.stat().st_size))
for f in ('closed.json','main-browser.json'):save(supp/f,'riverside-window-row/'+f)
rows.append(dict(phase='north-river-window-row',exit_code=0,finished=reframed['finished'],node=reframed['node_pid'],chromium=reframed['observed_chromium_pid_and_starttime'],report_sha256=reframed['report_sha256'],closed_sha256=h(supp/'closed.json')))
assert len(images)==16 and len(rows)==12
record=dest/'process-exits.json'
put(record,dict(order=248,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,actual_saved_downloads=ov['downloads'],screens=images,ground=floor,standalone_views=4,ordinary_city_screens=10,guest_returns={'313':h(guest/'viewer-closed.json'),'558':h(g558),'584':h(f584),**ret}))
if args.reviewed:
    note=w/'observations.md';detail=w/'reviewed-images.json'
    reviewed=r(detail);assert {k:v['sha256'] for k,v in reviewed.items()}=={x['file']:x['sha256'] for x in images} and all(v['observation'].strip()for v in reviewed.values())
    assert note.is_file() and note.read_text().strip()
    save(note);save(detail)
    receipt=w.parent/'248-map-slot-released.json'
    if not receipt.exists():put(receipt,dict(order=248,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,views_reviewed=True,real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),review_sha256=h(note),screenshots=images,reports=rows,actual_saved_downloads=ov['downloads'],manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
    assert r(receipt)['report_sha256']==h(record)
    print(receipt,h(receipt))
if args.submit:
    assert args.reviewed
    doc=a/'README.md'
    baseline=doc.read_text().rstrip()
    section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31248/process-exits.json) · [旧城对照](city-31248/map-before.png) · [临街转角](city-31248/map-north-river-seven-arched-bays.png) · [临河长排窗](city-31248/riverside-window-row/map-riverside-window-row-canvas.png) · [长拱窗及窗套](city-31248/map-long-arched-windows.png) · [远档](city-31248/map-distant.png)'
    if '## 正式城市地图复核' not in baseline:
        tmp=doc.with_name('.README.248-new.md');tmp.write_text(baseline+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
    else:assert section in baseline
    subprocess.run(['python','-Bu','/tmp/shanghai-signed-release-inbox/submit.py','248','README.md','city-31248'],check=True)
