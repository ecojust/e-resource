"""Archive the actual Zikawei convent city and standalone views after visual review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,socket,shutil,os,argparse,subprocess
w=Path(__file__).resolve().parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/zikawei-convent-central-front-v1');e=w/'isolated-evidence';dest=a/'city-31232'
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
for f in ['check-convent-front.cjs','capture.py','sequence.py','candidate-audit-groups.cjs','signed-comparison.json','standalone-originals.json','outside-sources.json','isolated-inputs.json','archive.py','check-pixels.py','pixel-inspection.json']:save(w/f)
for n in [231,232]:
 c=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json';assert r(c)['production_receipt_sha256']==h(w/f'{n}-production.json');save(c)
 full=Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-all-http.json';assert r(full)['passed'] and r(full)['production_receipt_sha256']==h(w/f'{n}-production.json');save(full)
files={};actions=[];floor=[];rows=[];images=[];cases=r(a/'map-case.json');old=Path('/tmp/shanghai-main-231/231-map-slot-released.json')
driver_versions={h(w/'check-convent-front.cjs'):w/'check-convent-front.cjs'}
failed=[]
failed_folders=[*w.glob('*-control-failure-*'),*w.glob('failed-*-??')]
for work in sorted(failed_folders):
 for driver in work.glob('*.cjs'):driver_versions[h(driver)]=driver
 for record in work.rglob('failed-exit.json'):
  closure=r(record);assert closure['exit_code']!=0 and closure['cdp_closed'] and not closure['remaining_chromium']
  directory=record.parent
  rel='failed-browser-attempts/'+work.name+'/'
  files={}
  def take(p):
   archived=save(p,rel+p.name);files[p.name]=h(archived)
  take(record)
  log=directory/'node.log';assert h(log)==closure['stdout_sha256'];take(log)
  report=directory/Path(closure['report']).name
  if closure['report_sha256']:
   assert h(report)==closure['report_sha256'];take(report)
   for shot in r(report).get('screenshots',[]):
    picture=directory/shot['file'];assert h(picture)==shot['sha256'];take(picture)
  failed.append(dict(phase=closure['phase'],attempt=work.name,exit_code=closure['exit_code'],started=closure['started'],finished=closure['finished'],files=files))
boot=w/'prior-independent-launch-long-socket';boot_report=r(boot/'launch-failure.json')
assert boot_report['browser_launch_succeeded'] is False and boot_report['observed_remaining']==[] and h(boot/'independent/viewer.log')==boot_report['log_sha256']
for f in (boot/'launch-failure.json',boot/'independent/viewer.log'):
 save(f,'failed-browser-attempts/independent-original-socket/'+f.name)
if failed:
 dest.joinpath('failed-browser-attempts').mkdir(exist_ok=True)
 put(dest/'failed-browser-attempts/index.json',dict(order=232,attempts=sorted(failed,key=lambda row:row['started'])))
for name in pins['stage_order']:
 folder=e/name;c=r(folder/'closed.json');path=Path(c['report']);actual=r(path);n=231 if name=='control'else 232
 sig=r(w/f'{n}-production.json')['files'];native=intake['original_city_bindings_retrieved_on_both']
 assert c['exit_code']==0 and not c['remaining_chromium'] and c['cdp_closed'] and c['observed_chromium_pid_and_starttime'] and c['report_sha256']==h(path) and c['source_code_sha256']==actual['scriptSha256']
 driver=driver_versions[c['source_code_sha256']];assert h(driver)==c['source_code_sha256']
 save(driver,'actual-browser-phases/source/'+c['source_code_sha256']+'.cjs')
 assert c['predecessor']['sha256']==h(old);old=folder/'closed.json'
 if name in ('mobile-pin','desktop-pin'):
  origin=actual['priorRouteStart'];assert origin['normalStartupFinished'] and origin['fromActualDirectoryLink'] and origin['id']==actual['localExisting']
  assert origin['route']=='#landmark='+origin['id']+'&mode=overview' and actual['trustedBeaconEvent']['picked']==pins['id']
 else:
  entry=actual['realDirectoryEntry'];assert entry['pointer']['trusted'] and entry['normalStartupFinished']
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
  f=rec['file'];site=r(w/'source-geometry-in-both-stations.json')[str(31000+n)]
  alt=site['override']['model'];actual_registered={site['route']:site['sha256'],alt['file']:alt['sha256']}
  expected=sig.get(f) or native.get(f,{}).get('sha256') or actual_registered.get(f)
  assert rec['sha256']==expected,(name,f,expected);files[f]=rec
 save(path,'actual-browser-phases/'+name+'.json');save(old,'actual-browser-phases/'+name+'-closed.json')
 rows.append({'phase':name,'exit_code':c['exit_code'],'finished':c['finished'],'node':c['node_pid'],'chromium':c['observed_chromium_pid_and_starttime'],'report_sha256':h(path),'closed_sha256':h(old)})
i=e/'independent';ic=r(i/'closed.json');iv=r(i/'viewer.json')
assert ic['passed'] and ic['exit_code']==0 and not ic['remaining_chromium'] and ic['observed_chromium_pid_and_starttime'] and ic['report_sha256']==h(i/'viewer.json')
assert len(iv['views'])==4 and set(iv['downloads'])=={'raw','full','lod','native'}
assert all(j['actualSaved'] and j['saveAsVerified']for j in iv['downloads'].values()) and ic['actual_saved_downloads']==iv['downloads']
tail=Path('/workspace/.e-resource-recovery/grace/232-two-natives-returned.json');tr=r(tail)
assert tr['host']==232 and tr['host_sha256']==h(i/'closed.json') and tr['host_report_sha256']==h(i/'viewer.json') and tr['all_children_exited'] and tr['remaining_children']==[]
assert [j['order']for j in tr['jobs']]==[498,502] and all(h(Path(j['receipt']))==j['sha256'] for j in tr['jobs'])

for picture in iv['views']:assert h(i/picture['filename'])==picture['sha256'];save(i/picture['filename'],'standalone/'+picture['filename'])
for page in ['viewer.json','closed.json']:save(i/page,'standalone/'+page)
for evidence in ['source-ray-sightlines.json','camera-sightlines.json','source-geometry-in-both-stations.json','independent.py','cdp-city-page-232.cjs','check-232-viewer.cjs']:save(w/evidence)
rows.append({'phase':'independent','exit_code':0,'finished':ic['finished'],'node':ic['node_pid'],'chromium':ic['observed_chromium_pid_and_starttime'],'report_sha256':h(i/'viewer.json'),'closed_sha256':h(i/'closed.json')})
assets={k:y for k,y in files.items() if '/xuhui-zikawei-convent-central-front/'in k};assert len(assets)==4 and len(actions)==2 and len(floor)==pins['ground_checks']
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19532))!=0
record=dest/'process-exits.json';put(record,dict(order=232,id=pins['id'],real_browser_process_exits=rows,real_pointers=actions,signed_downloads=assets,screens=images,ground=floor))
split=r(e/'distant/main-browser.json')['separateEvidence'];assert split['image_session_exit']==1 and split['image_sha256']==next(x['sha256']for x in images if x['file']=='map-distant.png')
put(dest/'distant-separate-sessions.json',dict(image=split,state_report='actual-browser-phases/distant.json',state_report_sha256=h(e/'distant/main-browser.json'),state_exit=0,previous_failed_attempts=len(failed)))
if args.reviewed:
 assert r(w/'pixel-inspection.json')['passed']
 note=w/'observations.md';assert note.is_file() and note.read_text().strip();save(note)
 receipt=w.parent/'232-map-slot-released.json'
 if not receipt.exists():put(receipt,dict(order=232,passed=True,exit_code=0,remaining_chromium=[],all_captures_visually_reviewed=True,sessions=rows,reports={x['phase']:x for x in rows},real_browser_process_exits=rows,report_sha256=h(record),evidence=str(record),actual_saved_downloads=iv['downloads'],native_development_return_sha256=h(tail),manual_sha256=h(note),finished=datetime.now(timezone.utc).isoformat()))
 else:assert r(receipt)['report_sha256']==h(record)
 print(receipt,h(receipt))
if args.submit:
 assert args.reviewed and (w.parent/'232-map-slot-released.json').is_file()
 doc=a/'README.md';base=doc.read_text().rstrip();section='## 正式城市地图复核\n\n'+(w/'observations.md').read_text().strip()+'\n\n[实机、地面与四种下载](city-31232/process-exits.json) · [旧城对照](city-31232/map-before.png) · [中央庭院立面](city-31232/map-garden-front.png) · [西端封闭玻璃廊](city-31232/map-west-enclosed-veranda.png) · [远档](city-31232/map-distant.png)'
 if '## 正式城市地图复核' not in base:
  tmp=doc.with_name('.README.232-new.md');tmp.write_text(base+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
 else:assert section in base
 names=[v['filename']for v in r(w/'standalone-originals.json')['views']]
 subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','232','README.md','viewer.json','city-31232',*names],check=True)
