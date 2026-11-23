"""Archive the genuine Jiangxi Road waterworks map sessions and the exact historical viewer bytes; issue the physical handoff only after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/zili-waterworks-office-v1');e=w/'isolated-evidence';dest=a/'city-31265'
ap=argparse.ArgumentParser();ap.add_argument('--reviewed',action='store_true');ap.add_argument('--submit',action='store_true');args=ap.parse_args()
r=lambda f:json.loads(f.read_bytes());h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
plain=r;file_hash=h
def unpacked_bytes(f):return __import__('gzip').decompress(Path(str(f)+'.gz').read_bytes())
r=lambda f:plain(f)if f.exists()else json.loads(unpacked_bytes(f))
h=lambda f:file_hash(f)if f.exists()else hashlib.sha256(unpacked_bytes(f)).hexdigest()
def save(f,rel=None):
 t=dest/(rel or f.name);f=f.resolve(strict=True);t.parent.mkdir(exist_ok=True,parents=True)
 if not t.exists():
  try:os.link(f,t)
  except OSError:shutil.copyfile(f,t)
 assert h(t)==h(f);return t
def put(f,q):
 if f.exists():assert r(f)==q;return
 z=f.with_suffix('.temp');z.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');z.replace(f)
pins=r(w/'isolated-inputs-recovered.json');intake=r(w/'signed-comparison.json');assert all(h(w/k)==v for k,v in pins['frozen_program_and_inputs'].items())
for f in ['check-zili-office.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','standalone-visual-review.json','isolated-inputs.json','archive.py']:save(w/f)
pr264=Path('/tmp/shanghai-yongjia-porch/scenes/264-all-http.json')
for n in [264,265]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=(pr264 if n==264 else a/'31265-all-http.json');assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
for f in ['check-zili-office-measured.cjs','isolated-inputs-recovered.json','check-parent-264-recovered.py','capture-recovered.py','sequence-recovered.py','archive-recovered.py']:save(w/f)
home=Path('/workspace/shanghai-publisher-preservation/city-265')
for f in ['formal-viewer.cjs','actual-viewer.py','formal-viewer-sources.json','attest-sites.py','verify-ordinary.py']:save(home/f,'standalone/'+f)
viewer=__import__('runpy').run_path(str(home/'verify-ordinary.py'))['verify'](w,save)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-264/264-map-slot-released.json')
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=264 if name=='control'else 265
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==h(w/'check-zili-office-measured.cjs')==h(folder/'actual-driver.cjs')==actual['scriptSha256']
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
 cal=actual['viewportCalibration'];gl,=actual['webglCaptures'];display,=actual['displayCaptures']
 for fname,digest in ((cal['image'],cal['sha256']),(gl['file'],gl['sha256']),(display['displayImage'],display['displayImageSha256']),('actual-driver.cjs',c['source_code_sha256'])):
  source=folder/fname;assert h(source)==digest;save(source,'actual-browser-phases/'+name+'/'+fname)
 for rec in actual['files']:
  f=rec['file'];assert rec['sha256']==sig.get(f,native.get(f,{}).get('sha256'));files[f]=rec
 save(path,'actual-browser-phases/'+name+'.json');save(old,'actual-browser-phases/'+name+'-closed.json')
 rows.append({'phase':name,'exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':h(path),'closed_sha256':h(old)})
assets={k:y for k,y in files.items() if '/huangpu-zili-waterworks-office-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==57
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19565))!=0
record=dest/'process-exits.json';put(record,dict(order=265,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor))
if args.reviewed:
 note=w/'observations.md';assert note.is_file() and note.read_text().strip()
 notes=r(w/'visual-review.json')['images']
 expected={v['file']:v['sha256'] for v in images}
 expected.update({'standalone/'+v['filename']:v['sha256'] for v in viewer['views']})
 assert set(notes)==set(expected) and all(notes[k]['sha256']==v and notes[k]['observation'].strip() for k,v in expected.items())
 save(note);save(w/'visual-review.json')
 receipt=w.parent/'265-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=265,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,views_reviewed=True,real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),review_sha256=h(note),screenshots=images,reports=rows,actual_saved_downloads=viewer['downloads'],standalone_views=viewer['views'],standalone_receipt_sha256=h(w/'current-standalone/closed.json'),manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 helper=Path('/workspace/.e-resource-recovery/placement/host265-444/handoff.py')
 assert h(helper)=='a99bdf776815736d670ea0bc72d70d7f262851d9afaf88671e8891e317cdf375'
 subprocess.run([__import__('sys').executable,'-Bu',helper,'run'],check=True)
 early=Path('/dev/shm/root-shanyin652/development-native/link-265.py')
 returned444=Path('/workspace/.e-resource-recovery/root/changning-444-study/development-native/265-development-returned.json')
 assert h(early)=='e91368df98d76ebd5bc1ab5df3cb721e51cd558d950780c11775bb8f51798013'
 observer=None
 if not (early.parent/'early-development-returned.json').is_file():
  monitor=Path('/workspace/.e-resource-recovery/history/zili265-measured/retain-652-downloads.py');assert h(monitor)=='ecd7af3abd7b01f1d0acb90467085acb9a764767e80e8cf8005f68327a3cae5c'
  observer=subprocess.Popen([__import__('sys').executable,'-Bu',monitor])
 try:
  subprocess.run([__import__('sys').executable,'-Bu',early,receipt,returned444],check=True)
  if observer is not None:assert observer.wait(timeout=60)==0
 finally:
  if observer is not None and observer.poll() is None:observer.terminate();observer.wait()

 finished=early.parent/'early-development-returned.json';result=r(finished)
 assert result['order']==652 and result['host']==265 and result['passed'] and result['exit_code']==0 and result['all_children_exited'] and not result['remaining_children']
 assert result['host_sha256']==h(receipt) and result['prior_in_this_window_sha256']==h(returned444) and result['physical_sha256']==h(Path(result['physical']))
 # The second residence has its own editable model, viewer and four actual downloads.
 companion=Path('/workspace/.e-resource-recovery/placement/companion-229-265/after-main-short-socket.py')
 assert h(companion)=='1d0d649c63823139cf98097aa02df03e9280b7b6e8aba4bbddcee56790a3375c'
 companion_out=Path('/dev/shm/root-shanyin652/bay229/development-native/early-companion-returned.json')
 if not companion_out.exists():
  subprocess.run([__import__('sys').executable,'-Bu',companion,finished],check=True)
 bay=r(companion_out)
 assert bay['id']=='hongkou-shanyin-229-canted-bay' and bay['companion'] and bay['order']==652 and bay['host']==265
 assert bay['passed'] and bay['exit_code']==0 and bay['all_children_exited'] and not bay['remaining_children']
 assert Path(bay['source']).samefile(finished) and bay['source_sha256']==h(finished) and bay['parent_physical_sha256']==h(Path(result['physical']))
 assert bay['author_sha256']=='e8aa2bf4bbef1c050a8596cbe228fdfc3a65936d177bd248ee84ddd14af9ab81'
 assert len(bay['processes'])>=4 and all(q['code']==0 for q in bay['processes'])
 assert len(bay['files'])>=6 and all(h(Path(p))==sig for p,sig in bay['files'].items())
 assert set(bay['downloads'])=={'native','raw','full','lod'} and len(bay['views'])==10
 assert all(q['saveAsVerified'] and h(Path(q['saved']))==q['sha256'] for q in bay['downloads'].values())
 bay_view=next(Path(p) for p in bay['files'] if Path(p).name=='viewer.json')
 assert all(h(bay_view.parent/q['filename'])==q['sha256'] for q in bay['views'])
 print(receipt,h(receipt))
if args.submit:
 assert args.reviewed and (w.parent/'265-map-slot-released.json').is_file()
 doc=a/'README.md';base=doc.read_text().rstrip();section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31265/process-exits.json) · [旧城对照](city-31265/map-before.png) · [江西中路464号券门与街墙](city-31265/map-jiangxi-464-street.png) · [砖券、门牌及上层红砖窗带](city-31265/map-orange-arch-and-house-number.png) · [远档](city-31265/map-distant.png)'
 if '## 正式城市地图复核' not in base:
  tmp=doc.with_name('.README.265-new.md');tmp.write_text(base+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
 else:assert section in base
 names=[v['filename']for v in r(w/'standalone-originals.json')['views']]
 subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','265','README.md','viewer.json','city-31265',*names],check=True)
