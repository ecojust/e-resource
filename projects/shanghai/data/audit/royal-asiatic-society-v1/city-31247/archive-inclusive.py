"""Verify the original ten museum sessions and retain the additional field and ordinary-page records."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess,sys
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/royal-asiatic-society-v1');e=w/'isolated-evidence';dest=a/'city-31247'
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
for f in ['check-royal-asiatic.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','isolated-inputs.json','archive.py']:save(w/f)
pr246=a.parent/'electric-company-corner-tower-v1/31246-all-http.json'
for n in [246,247]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=(pr246 if n==246 else Path('/tmp/shanghai-yongjia-porch/scenes')/'247-all-http.json');assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-246/246-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=246 if name=='control'else 247
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==h(w/('inscription-compact.cjs' if name=='inscription' else 'check-royal-asiatic.cjs'))==actual['scriptSha256']
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
assets={k:y for k,y in files.items() if '/huangpu-royal-asiatic-society-huqiu-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==21
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19547))!=0

author=Path('/workspace/shanghai-publisher-preservation/city-247')
browser=Path('/workspace/.e-resource-recovery/browser')
review=browser/'247-failures/public-files-with-reframe.json'
assert h(review)=='3f4bd7e0043910611a744553ad7c5eba610447df2cedcd816b49773a52d5b2cf'
for rel,item in r(review).items():
    src=Path(item['source'])
    assert h(src)==item['sha256'] and src.stat().st_size==item['bytes']
    save(src,Path(rel).relative_to('city-31247'))
for name, sig in [('observed.json','d5722760d08778a47e8fe27fb9df66f00417ed7323dbeed8edb6f6ba4d329686'),('supplementary-images.json','2410bd4c59255ad0f185f11cad4f88f4366338361ceefe1f51040eeef292ca7b')]:
    source=browser/'247-independent-views'/name
    assert h(source)==sig
    save(source,'independent-image-review/'+name)
for filename in ('capture-inscription.py','inscription-compact.cjs','capture-front-247.py','street-front-reframe.cjs','capture-oblique-247.py','arches-oblique.cjs','archive-inclusive.py'):
    save(w/filename)
for filename in ('formal-viewer.cjs','formal-viewer-sources.json','actual-viewer.py'):
    save(author/filename,'current-standalone/'+filename)
ordinary=w/'current-standalone/closed.json'
oco=r(ordinary);orp=Path(oco['report']);ov=r(orp)
assert oco['prior_sha256']==h(e/'distant/closed.json') and oco['exit_code']==0 and not oco['remaining'] and oco['chromium'] and oco['passed']
assert h(orp)==oco['report_sha256'] and ov['passed'] and ov['scriptSHA256']==oco['driver_sha256']==h(author/'formal-viewer.cjs')
assert ov['productionSHA256']==h(w/'247-production.json') and ov['downloads']==oco['downloads']
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
previous=e/'distant/closed.json'
for sub,script in [('facade-reframe','street-front-reframe.cjs'),('facade-oblique','arches-oblique.cjs')]:
    folder=w/sub;exitfile=folder/'closed.json';closure=r(exitfile);rep=folder/'main-browser.json';result=r(rep)
    assert closure['exit']==0 and closure['cdp_closed'] and not closure['remaining'] and closure['observed_chromium_pid_and_starttime']
    assert closure['predecessor']['sha256']==h(previous) and closure['report_sha256']==h(rep) and closure['source_code_sha256']==h(w/script)==result['scriptSha256']
    assert result['completed'] and not (result['failed'] or result['errors'] or result['warnings']) and result['realDirectoryEntry']['pointer']['trusted']
    view,=result['views'];assert view['asset']['variant']=='full' and view['asset']['verifiedAsset']['modelId']==pins['id'] and not view['contextLost'] and not view['glError']
    assert len(result['ground'])==21 and all(g['found']==g['expected'] for g in result['ground'])
    for item in [*result['screenshots'],result['canvasCapture']]:
        f=folder/item['file'];assert h(f)==item['sha256'] and f.stat().st_size==item['bytes']
        save(f,sub+'/'+f.name);images.append(dict(file=sub+'/'+f.name,sha256=h(f),bytes=f.stat().st_size))
    for f in (rep,exitfile):save(f,sub+'/'+f.name)
    rows.append(dict(phase=sub,exit_code=0,finished=closure['finished'],node=closure['node_pid'],chromium=closure['observed_chromium_pid_and_starttime'],report_sha256=h(rep),closed_sha256=h(exitfile)))
    previous=exitfile
def guest(src,sub,name=None):
    save(src,'guest-returns/'+sub+'/'+(name or src.name))
work312=Path('/tmp/yide-changhua312')
for f in ('native-closed.json','raw-312-confirmed.json','viewer-closed.json','formal-312-complete.json'):
    guest(work312/f,'312')
for f in ('312-native-deferred.json','312-viewer-deferred.json'):guest(w/f,'312')
for f in sorted((work312/'handoff').glob('native-*.log')):guest(f,'312')
for f in sorted((work312/'handoff').glob('native-*/physical-exit.json')):guest(f,'312',f.parent.name+'-physical.json')
for f in (1939105,1939927):guest(author/'312-blender-identity'/f'{f}.json','312')
n312=r(work312/'native-closed.json');v312=r(work312/'viewer-closed.json')
assert n312['passed'] and n312['exit_code']==0 and n312['remaining']==[] and len(n312['blender_pids'])==2
assert v312['passed'] and v312['exit_code']==0 and v312['remaining']==[] and v312['views']==6 and v312['downloads']==4 and n312['assets']==v312['assets']
home554=Path('/tmp/changle272-554')
for filename in ('247-native-returned.json','early-240-native-returned.json','after-247.py','recheck-after-247.py'):
    guest(home554/filename,'554')
g554=r(home554/'247-native-returned.json');assert g554['already_completed'] and g554['previous_completed_exit']==0 and g554['host_sha256']==h(e/'desktop-pin/closed.json')
guest(Path('/run/codex-docker/user/shanghai-247-profile/sequence-restart-1.log'),'554','first-field-check.log')
home580=Path('/dev/shm/root-jkk580/development-native')
first580=home580/'attempt-01-group-descriptor'
for fn in ('physical.json','early-development-returned.json','closed.json','native.log','prepare.log'):
    guest(first580/fn,'580/first-attempt')
guest(home580/'storage/attempt-1795349968038290512/render.log','580/first-attempt')
for fn in ('physical.json','early-development-returned.json','closed.json'):guest(home580/fn,'580')
t580=home580/'early-development-returned.json';actual580=r(t580)
assert actual580['passed'] and actual580['exit_code']==0 and actual580['host_sha256']==h(ordinary) and actual580['all_children_exited'] and actual580['remaining_children']==[]
assert actual580['physical_sha256']==h(home580/'physical.json')
pairpath=Path('/tmp/pingliang25-658/247-658-662-returned.json');pair=r(pairpath)
assert pair['passed'] and pair['orders']==[658,662] and pair['after_580_sha256']==h(t580) and pair['host_sha256']==h(ordinary)
assert pair['exit_code']==0 and not pair['remaining_children'] and pair['all_children_exited']
guest(pairpath,'658-662')
for item in pair['physical_returns']:
    path=Path(item['return_file']);assert h(path)==item['return_sha256'] and r(path)['passed'] and len(item['four_assets'])==4
    guest(path,str(item['order']))
for f in sorted(Path('/tmp/shanyin274-662/247-first-physical-before-blender-exec').iterdir()):
    if f.is_file():guest(f,'662/first-attempt')
assert len(images)==18 and len(rows)==13
record=dest/'process-exits.json'
put(record,dict(order=247,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,actual_saved_downloads=ov['downloads'],screens=images,ground=floor,standalone_views=4,ordinary_city_screens=10,supplemental_screens=4,late_guests={'312':h(work312/'viewer-closed.json'),'554':h(home554/'247-native-returned.json'),'580':h(t580),'658-662':h(pairpath)}))
if args.reviewed:
    note=w/'observations.md';detail=w/'reviewed-images.json'
    reviewed=r(detail);assert {k:v['sha256'] for k,v in reviewed.items()}=={x['file']:x['sha256'] for x in images} and all(v['observation'].strip()for v in reviewed.values())
    assert note.is_file() and note.read_text().strip()
    save(note);save(detail)
    receipt=w.parent/'247-map-slot-released.json'
    if not receipt.exists():put(receipt,dict(order=247,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,views_reviewed=True,real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),review_sha256=h(note),screenshots=images,reports=rows,actual_saved_downloads=ov['downloads'],manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
    assert r(receipt)['report_sha256']==h(record)
    print(receipt,h(receipt))
if args.submit:
    assert args.reviewed
    doc=a/'README.md'
    section='## 正式城市地图复核\n\n'+note.read_text().strip()+'\n\n[各图的观察与指纹](city-31247/reviewed-images.json) · [实机、地面与四种下载](city-31247/process-exits.json) · [街面原景](city-31247/map-huqiu-three-stone-arches.png) · [入口正面](city-31247/facade-reframe/map-three-arches-front.png) · [入口斜角](city-31247/facade-oblique/map-stone-arches-oblique.png) · [八角窗](city-31247/map-octagonal-window-and-gate.png) · [独立页](city-31247/current-standalone/viewer-desktop-full.png)'
    baseline=doc.read_text().rstrip()
    if '## 正式城市地图复核' not in baseline:
        temp=doc.with_name('.reviewed-247.md');temp.write_text(baseline+'\n\n'+section+'\n');temp.chmod(doc.stat().st_mode);temp.replace(doc)
    else:assert section in baseline
    subprocess.run([sys.executable,'-Bu','/tmp/shanghai-signed-release-inbox/submit.py','247','README.md','city-31247'],check=True)
