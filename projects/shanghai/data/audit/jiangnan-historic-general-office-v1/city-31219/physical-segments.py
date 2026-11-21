from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time,tempfile
from shutil import disk_usage
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/jiangnan-historic-general-office-v1';case=a/'map-case.json';out=w/'segments';out.mkdir(exist_ok=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def wr(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def live(profile):
 found=[]
 for f in Path('/proc').glob('[0-9]*/cmdline'):
  try:args=f.read_bytes()
  except OSError:continue
  if str(profile).encode()in args and b'chromium' in args:found.append(int(f.parent.name))
 return found
def current():
 c=Path('/sys/fs/cgroup');stats=dict(line.split()for line in (c/'memory.stat').read_text().splitlines());return int((c/'memory.max').read_text())-int((c/'memory.current').read_text())+max(0,min(int(stats['inactive_file']),int(stats['file'])-int(stats['shmem'])))+int(stats['slab_reclaimable'])
def run():
 import runpy
 runpy.run_path('/tmp/yangtze239/archive-private-qa-inputs.py')['recover'](w)
 with (w/'sequence.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
   fcntl.flock(light,fcntl.LOCK_EX)
   for sec in ['control','phone','desktop','return','placement','distant']:
    if sec in ('phone','desktop'):
     fcntl.flock(light,fcntl.LOCK_UN)
     try:subprocess.run([sys.executable,'-Bu','/tmp/jiangnan219/host-284.py','native'if sec=='phone'else'viewer'],check=True)
     finally:fcntl.flock(light,fcntl.LOCK_EX)
    if sec in ('phone','desktop'):
     order_phase='control' if sec=='phone' else 'phone';actual=out/(order_phase+'-closed.json');guest=Path('/tmp/anhe345/219-geometry.py')
     assert sha(guest)=='7a33258a954f70a2e377fe340b52c475e7bb5153fecdc33328b03421ffea1993'
     subprocess.run([sys.executable,'-B',guest,order_phase,actual],check=True)
     back=json.loads((guest.parent/('219-'+order_phase+'-closed.json')).read_bytes())
     assert back['order']==345 and back['host']==219 and back['source_sha256']==sha(actual) and back['remaining']==[]
    if sec=='desktop':
     actual=out/'phone-closed.json';prior_guest=Path('/tmp/anhe345/219-phone-closed.json');work=Path('/tmp/adeodata353/after-phone.py')
     assert sha(work)=='1405963f0a0fe39d0af9fc4ee65d0be0cf649f05ffdeb64ec224de58d13d6b2b'
     subprocess.run([sys.executable,'-B',work,actual,prior_guest],check=True)
     returned=json.loads((work.parent/'219-mesh-closed.json').read_bytes())
     assert returned['host_sha256']==sha(actual) and returned['previous_sha256']==sha(prior_guest) and returned['remaining']==[]
    if sec=='return':
     guest=Path('/tmp/wanyi343/mapping/219-desktop-model.py');host=out/'desktop-closed.json'
     assert sha(guest)=='93e8141a02bd2d948019027c9befe895fadb15e1d2acd43dcf079815ed614521'
     subprocess.run([sys.executable,'-B',guest,host],check=True)
     cpu=json.loads(Path('/tmp/wanyi343/mapping/219-desktop-cpu-closed.json').read_bytes())
     assert cpu['order']==343 and cpu['host']==219 and cpu['source_sha256']==sha(host) and cpu['host_report_sha256']==json.loads(host.read_bytes())['report_sha256'] and cpu['remaining']==[]
    if sec=='placement':
     guest=Path('/tmp/huaihai-1634-research/east-door-supplement/after-219-return.py')
     assert sha(guest)=='22f76befc86cefc749945fb9fb0dad8d0a51cd9b2f9b5ddc6b614c8fef2792d8' and sha(guest.parent/'focus.cjs')=='305c281b4112a2c89db005104112d140d3ae157c1d63dd83a3e16166e58ff3af'
     stage=out/'return-closed.json';subprocess.run([sys.executable,'-Bu',guest,stage],check=True)
     response=json.loads((guest.parent/'after-219-return.json').read_bytes());assert response['host_receipt_sha256']==sha(stage) and response['remaining_children']==[] and response['node_closed']
    if sec=='distant':
     guest=Path('/tmp/kemi334/design/219-window.py');stage=out/'placement-closed.json'
     assert sha(guest)=='ea7fd8d043e16063677be87b775b6c805d3dac1eab678267fec037fe25e908eb'
     subprocess.run([sys.executable,'-B',guest,stage],check=True)
     response=json.loads(Path('/tmp/kemi334/219-camera-closed.json').read_bytes())
     assert response['host_receipt_sha256']==sha(stage) and response['host_report_sha256']==json.loads(stage.read_bytes())['report_sha256'] and response['remaining']==[]
     guest = Path('/tmp/jiangnan219/after-334-342-360.py')
     assert sha(guest) == "ce9b7222496671e14fd4e950e58a61f2f760c8b37e3604931feedbfd9584bc67"
     subprocess.run([sys.executable,'-Bu',guest,'--from-sequence'],check=True)
     extra=json.loads((guest.parent/'342-360-after-placement.json').read_bytes())
     assert len(extra['stages'])==2 and not extra['remaining'] and extra['host_sha256']==sha(stage)
    prior=sec=='control';dest=w/'pre' if prior else out/sec;dest.mkdir(exist_ok=True);signal=out/(sec+'-closed.json');report=dest/('control-browser.json'if prior else 'main-browser.json')
    if signal.is_file()and json.loads(signal.read_bytes())['exit']==0 and json.loads(report.read_bytes())['completed']:continue
    if report.exists():raise RuntimeError('Preserve failed section before retry: '+str(dest))
    # Avoid starting beside a currently building native preview when its memory working set is large.
    tick=time.monotonic()
    while current()<1_000_000_000 and time.monotonic()-tick<45:time.sleep(2)
    top=max([Path('/tmp'),Path('/dev/shm')],key=lambda f:disk_usage(f).free)
    temp=Path(tempfile.mkdtemp(prefix='shanghai-jiangnan219-'+sec+'-',dir=top));begin=now()
    env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(w/'city219'),QA_SEGMENT=sec,QA_OUTPUT_DIR=str(dest),QA_CDP_PORT='9819',MODEL_BASE_URL='http://127.0.0.1:'+('31218'if prior else'31219')+'/')
    # Use the low-residency process layout that already passed the formal 31207 city sessions.
    launch_module=w/'low-memory-chromium.cjs'
    assert sha(launch_module)=='e2e4017f179c3d6125cb71e0de5c0223788185c6a74cceb494e186b62362c3d7'
    env['NODE_OPTIONS']=(env.get('NODE_OPTIONS','')+' --require '+str(launch_module)).strip()
    env['QA_LOW_MEMORY_LAUNCHER_SHA256']=sha(launch_module)
    if prior:
     cat=w/'city218/data/candidate-city-integrations.json';env.update(QA_CONTROL_CATALOG=str(cat),QA_CONTROL_CITY_COUNT='255',QA_CONTROL_CATALOG_SHA256=sha(cat))
    signed=w/'verified-scripts';signed.mkdir(exist_ok=True);driver=w/'check-map.cjs';version=signed/(sha(driver)+'.cjs')
    if not version.is_file():shutil.copyfile(driver,version)
    assert sha(version)==sha(driver)
    print('start',sec,begin,current(),disk_usage(top).free,flush=True)
    with(out/(sec+'.log')).open('ab',buffering=0)as log:
     proc=subprocess.Popen(['node',w/'check-map.cjs',case,*(['--control']if prior else[])],env=env,stdout=log,stderr=log,start_new_session=True)
     import psutil
     observed=set();peak=0;trace=[];initial_events=Path('/sys/fs/cgroup/memory.events').read_text()
     watchdog=psutil.Process(proc.pid)
     while proc.poll() is None:
      try:
       children=watchdog.children(recursive=True)
       browsers=[child for child in children if child.name() in ('chromium','chrome','headless_shell')]
       observed.update(child.pid for child in browsers)
       rss=sum(child.memory_info().rss for child in [watchdog,*children] if child.is_running())
       if rss>peak+16*1024*1024:
        peak=rss;trace.append([now(),peak,current()])
      except (psutil.NoSuchProcess,psutil.ZombieProcess):pass
      time.sleep(.4)
     rc=proc.returncode
    for j in range(20):
     if not live(temp):break
     time.sleep(.5)
    closure=dict(name=sec,process_rss_highwater=peak,process_rss_checkpoints=trace,cgroup_before=initial_events,cgroup_after=Path('/sys/fs/cgroup/memory.events').read_text(),launcher_sha256=sha(launch_module),started=begin,finished=now(),exit=rc,node_pid=proc.pid,node_closed=not psutil.pid_exists(proc.pid),chromium_pids=sorted(observed),remaining_chromium=live(temp),profile=str(temp),report=str(report),report_sha256=sha(report)if report.exists()else None);wr(signal,closure)
    print('exit',sec,closure,flush=True)
    if temp.is_dir() and not any(temp.iterdir()):temp.rmdir()
    assert rc==0 and closure['node_closed'] and closure['chromium_pids'] and not closure['remaining_chromium'] and json.loads(report.read_bytes())['completed'],closure
  records=[json.loads((out/k/'main-browser.json').read_bytes())for k in ['phone','desktop','return','placement','distant']];dst=w/'post';dst.mkdir(exist_ok=True);merged={**records[0]}
  for key in ('catalog','caseSha256','bindings','camera'):assert all(r[key]==records[0][key]for r in records)
  for r in records:
   f=w/'verified-scripts'/(r['scriptSha256']+'.cjs');assert f.is_file() and sha(f)==r['scriptSha256']
  merged['checker_sha256_by_segment']={r['segment']:r['scriptSha256']for r in records}
  for key in ('screenshots','views','errors','warnings','failed','beaconInputs','files'):
   merged[key]=[v for r in records for v in r.get(key,[])]
   if key=='files':merged[key]=list({v['file']:(next((item for item in merged[key] if item['file']==v['file'] and item['loadedByScene']),v)) for v in merged[key]}.values())
  for r in records:
   for v in r['screenshots']:
    src=out/r['segment']/v['file'];assert sha(src)==v['sha256'];os.link(src,dst/v['file'])
   for key in ('neighborSelection','keyboardSearch','unloadedWhileAway','ground','groundChecks'):
    if key in r:merged[key]=r[key]
  for r in records:assert r['completed'] and not r['errors'] and not r['failed']
  merged['freshNear']=records[-1]['freshNear']
  merged.update(segment='five independent completed official map sessions',finished=records[-1]['finished'],segments=[json.loads((out/(s+'-closed.json')).read_bytes()) for s in ['phone','desktop','return','placement','distant']]);wr(dst/'main-browser.json',merged)
if __name__=='__main__':
 try:run()
 except Exception:
  (w/'exit').write_text('1\n');raise
 (w/'exit').write_text('0\n')
