"""Use the signed native or independent page window, observing all descendants across Linux sessions."""
from pathlib import Path
from datetime import datetime,timezone
from tempfile import TemporaryDirectory
import fcntl,json,os,psutil,runpy,shutil,subprocess,sys,time
h=Path(__file__).resolve().parent;w=h.parents[1];common=runpy.run_path(str(h/'admit-window-live.py'));read,save,sha=common['read'],common['save'],common['sha']
k=sys.argv[1];ticket=read(h/(k+'-window.json'));now,_=common['grant'](k,Path(ticket['receipt']));assert now==ticket
cfg=read(w/'raw-config.json');p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit'/cfg['tag'];id=cfg['id'];source=p/'source/precise'/id/'source';assets=p/'assets/models/candidates'/id;model=assets/'manifest.json';pilot=w/'checked';ref=read(pilot/'manifest.json');start=datetime.now(timezone.utc);attempt=Path('/dev/net/i276/attempts')/(k+'-'+start.strftime('%Y%m%dT%H%M%S%f'));attempt.mkdir(parents=True)
def observed(proc):
 births={};names={}
 while proc.poll()is None:
  try:children=psutil.Process(proc.pid).children(recursive=True)
  except psutil.Error:children=[]
  for child in children:
   try:births[child.pid]=child.create_time();names[child.pid]=child.name()
   except psutil.Error:pass
  time.sleep(.1)
 def alive(pid,when):
  try:x=psutil.Process(pid);return x.create_time()==when and x.status()!=psutil.STATUS_ZOMBIE
  except psutil.NoSuchProcess:return False
 for _ in range(50):
  if not any(alive(i,b)for i,b in births.items()):break
  time.sleep(.1)
 return names,births,[i for i,b in births.items() if alive(i,b)]
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as l:
 fcntl.flock(l,fcntl.LOCK_EX);assert not [proc.pid for proc in psutil.process_iter(['name','status']) if proc.info['name']in('chromium','chrome','blender')and proc.info['status']!=psutil.STATUS_ZOMBIE]
 areas=[d for d in [Path('/tmp'),Path('/dev/net'),Path('/dev/shm')]if d.is_dir()]
 with TemporaryDirectory(prefix='s341-',dir=max(areas,key=lambda q:shutil.disk_usage(q).free))as tmp,(attempt/'stdout.log').open('wb')as log:
  env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','TMPDIR':tmp,'PYTHONDONTWRITEBYTECODE':'1','LD_LIBRARY_PATH':'/tmp/country-tools/oidn/lib:'+os.environ.get('LD_LIBRARY_PATH',''),'MODEL_BASE_URL':'http://127.0.0.1:31341/','SHANGHAI_PROJECT_ROOT':str(p),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
  if k=='native':cmd=['taskset','-c',str(min(os.sched_getaffinity(0))),sys.executable,'-Bu',h/'split-scratch.py','--out',assets,'--audit',a,'--gltfpack','/workspace/.e-resource-recovery/toolchain/node_modules/.bin/gltfpack','--blender',h/'blender-one','--oidn','/workspace/.e-resource-recovery/toolchain/one-thread/oidn-single.py']
  else:
   env['SHANGHAI_SIGNED_VIEWER_ROOT']=str(h/'frozen-official-inputs')
   cmd=[sys.executable,'-Bu',h/'run-341-devices.py',id,attempt]
  proc=subprocess.Popen(cmd,stdout=log,stderr=log,env=env,start_new_session=True);names,births,remaining=observed(proc)
 row=dict(order=341,exit=proc.returncode,exit_code=proc.returncode,wrapper_pid=proc.pid,wrapper_closed=proc.poll()is not None,remaining=remaining,observed_processes=names,observed_process_births=births,started=start.isoformat(),finished=datetime.now(timezone.utc).isoformat(),host_receipt_sha256=ticket['sha256'],host_report_sha256=ticket['report_sha256'],log_sha256=sha(attempt/'stdout.log'),attempt=str(attempt))
 save(attempt/'physical-exit.json',row);save(h/(k+'-most-recent-exit.json'),row);assert not remaining and row['wrapper_closed'] and row['exit']==0
 m=read(model);assert m['id']==id and set(m['assets'])=={'raw','full','lod','native'}
 for role,r in m['assets'].items():
  f=assets/r['file'];assert sha(f)==r['sha256'] and f.stat().st_size==r['bytes']
  if role!='native':assert all(r[v]==ref['assets'][role][v]for v in ['bytes','sha256','triangles'])
 if k=='native':
  procs=[i for i,n in names.items()if n=='blender'];assert len(procs)>=2
  geo=read(a/'geometry-native.json');reopen=geo['native_reopened_and_compared'];assert reopen['match_raw'] and geo['meshopt_decoded_oriented_surfaces_match'] and geo['preview_sha256']==sha(a/geo['preview']) and reopen['mesh_count']==ref['editable_groups']['full']
  subprocess.run([sys.executable,'-B',source/'check_surfaces.py','--manifest',model,'--out',a/'surface-checks.json'],check=True)
  checks=read(a/'surface-checks.json');assert set(checks['results'])=={'raw','full','lod'} and all(v['passed'] and len(v['samples'])==read(a/'preflight/model-review.json')['surface_rays_per_level'] for v in checks['results'].values())
  result={**row,'passed':True,'all_processes_closed':True,'remaining_blender':[],'blender_pids':procs,'remaining_oidn':[],'files':[{'role':r,**v}for r,v in m['assets'].items()],'assets':m['assets'],'manifest_sha256':sha(model),'geometry_native_sha256':sha(a/'geometry-native.json'),'group_count':reopen['mesh_count'],'surface_receipt_sha256':sha(a/'surface-checks.json')}
 else:
  chromes=[i for i,n in names.items()if n in ('chrome','chromium')];assert chromes
  file=attempt/'viewer.json';vr=read(file);assert vr['passed']and vr['base']==env['MODEL_BASE_URL']and not vr['pageErrors']and len(vr['views'])==6 and vr['scriptSHA256']==sha(h/'six-view-download-live.cjs')and vr['manifestSHA256']==sha(model)
  target=a/'standalone-31341';target.mkdir(exist_ok=True)
  frozen=read(h/'verified-official-inputs.json')
  assert frozen['inputs']=={cfg['page']:vr['files'][cfg['page']],'src/candidate-asset-viewer.js':vr['files']['src/candidate-asset-viewer.js'],'assets/models/candidates/'+id+'/manifest.json':vr['manifestSHA256']}
  assert all(item.get('saveAsVerified') and item['saved_as']=='observed-'+item['file'] for item in vr['downloads'].values())
  for view in vr['views']:
   f=attempt/view['filename'];assert sha(f)==view['sha256'];shutil.copy2(f,target/f.name)
  for role,item in m['assets'].items():assert all(vr['downloads'][role][q]==item[q]for q in ('file','bytes','sha256'))
  shutil.copy2(file,target/'viewer.json')
  result={**row,'passed':True,'all_processes_closed':True,'node':read(attempt/'desktop-node-exit.json')['node'],'node_pids':[read(attempt/(n+'-node-exit.json'))['node']for n in ['desktop','mobile']],'chromium_pids':chromes,'remaining_chromium':[],'views':6,'downloads':4,'receipt_sha256':sha(file),'report':str(target/'viewer.json'),'report_sha256':sha(target/'viewer.json'),'assets':m['assets'],'signed_viewer_inputs':frozen,'actual_saved_downloads':vr['downloads']}
 save(w/(k+'-closed.json'),result)
