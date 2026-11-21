from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time,tempfile
from shutil import disk_usage
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/gaoyang-building-south-front-v1';case=a/'map-case.json';out=w/'segments';out.mkdir(exist_ok=True)
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
    prior=sec=='control';dest=w/'pre' if prior else out/sec;signal=out/(sec+'-closed.json');report=dest/('control-browser.json' if prior else 'main-browser.json')
    if signal.is_file() and report.is_file():
     receipt=json.loads(signal.read_bytes());capture=json.loads(report.read_bytes())
     if receipt['exit']==0 and capture['completed']:
      assert receipt['node_closed'] and receipt['chromium_pids'] and not receipt['remaining_chromium'] and receipt['report_sha256']==sha(report)
      continue
    if sec in ('phone','desktop'):
     fcntl.flock(light,fcntl.LOCK_UN)
     try:subprocess.run([sys.executable,'-Bu',w/'host-290.py','native'if sec=='phone'else'viewer'],check=True)
     finally:fcntl.flock(light,fcntl.LOCK_EX)
    if sec=='desktop':
     camera346=Path('/tmp/jingu-shaoxing346/design/after-225-camera.py');phone=out/'phone-closed.json'
     prior290=Path('/tmp/strand290/independent-closed.json')
     if not prior290.is_file():prior290=prior290.with_name('225-viewer-deferred.json')
     assert sha(camera346)=='8e02acd6531b32ad8e19abd78799a7a42d268046d650f1650cc7b2618b64c7d4'
     subprocess.run([sys.executable,'-Bu',camera346,phone,prior290],check=True)
     covered=json.loads((camera346.parents[1]/'225-camera-closed.json').read_bytes())
     assert covered['host_sha256']==sha(phone) and covered['host_report_sha256']==json.loads(phone.read_bytes())['report_sha256'] and covered['previous_sha256']==sha(prior290) and not covered['remaining']
     artist358=Path('/tmp/fenyang-jewish-hospital358/after-225-six-views.py')
     exit346=camera346.parents[1]/'225-camera-closed.json'
     assert sha(artist358)=='231598c19a0fe69280313a9953cdd7f2581588009c9a36fb2ccb99b30d00a075'
     subprocess.run([sys.executable,'-Bu',artist358,phone,exit346],check=True)
     result358=json.loads((artist358.parent/'225-six-views-closed.json').read_bytes())
     assert result358['host_sha256']==sha(phone) and result358['host_report_sha256']==covered['host_report_sha256']
     assert result358['previous_sha256']==sha(exit346) and result358['all_children_exited'] and not result358['remaining']
     pilot387=Path('/tmp/rong-gaoan387/author/after-225.py')
     exit358=artist358.parent/'225-six-views-closed.json'
     assert sha(pilot387)=='8721c99f9447274b454ebcb0610a85634e0ff1397b2ad70ff718ee6c6cda87b8'
     subprocess.run([sys.executable,'-Bu',pilot387,phone,exit358],check=True)
     result387=json.loads((pilot387.parents[1]/'225-first-study-closed.json').read_bytes())
     assert result387['host_sha256']==sha(phone) and result387['host_report_sha256']==covered['host_report_sha256']
     assert result387['previous_sha256']==sha(exit358) and result387['all_children_exited'] and not result387['remaining']
    if sec=='phone':
     gate=Path('/tmp/anfu233-367/mapping/after-225-control.py');closed=out/'control-closed.json'
     parent=Path('/tmp/strand290/native-closed.json')
     if not parent.exists():parent=parent.with_name('225-native-deferred.json')
     assert sha(gate)=='385883d71ad3cda0c99e0b608c104a8b9947a4dfe64a65a5d22dad7a31b7d804'
     fcntl.flock(light,fcntl.LOCK_UN)
     try:subprocess.run([sys.executable,'-Bu',gate,closed,parent],check=True)
     finally:fcntl.flock(light,fcntl.LOCK_EX)
     response=json.loads((gate.parents[1]/'225-control-model-closed.json').read_bytes())
     assert response['host_receipt_sha256']==sha(closed) and response['previous_sha256']==sha(parent) and response['all_children_exited'] and response['remaining']==[]
    if sec=='desktop':
     archive=Path('/tmp/shanghai-retired-site-store/closed-raw-tree-index-258-278')
     prior=Path('/tmp/rong-gaoan387/225-first-study-closed.json');ticket=archive/'225-2-returned.json'
     assert sha(archive/'at-225.py')=='2e27fdd065b4416df54509dff416df752685eaa9dd7a6af775892a11db74f7fe'
     if not ticket.exists():subprocess.run([sys.executable,'-Bu',archive/'at-225.py',prior,'2'])
     receipt=json.loads(ticket.read_bytes());assert receipt['host_sha256']==sha(prior) and receipt['events'] and not receipt['remaining']
    if sec in ('return','distant'):
     past='desktop'if sec=='return'else'placement';source=out/(past+'-closed.json')
     pilot=Path('/tmp/blackstone361/after-225-city.py')
     assert sha(pilot)=='38149168dcc66049634f71860eb7ffc85995ca24175cb31950fdb94d283883f8'
     fcntl.flock(light,fcntl.LOCK_UN)
     try:subprocess.run([sys.executable,'-Bu',pilot,source,past],check=True)
     finally:fcntl.flock(light,fcntl.LOCK_EX)
     result=json.loads((pilot.parent/('225-'+past+'-site-closed.json')).read_bytes())
     assert result['host_sha256']==sha(source) and result['host_report_sha256']==json.loads(source.read_bytes())['report_sha256'] and result['remaining']==[]
    if sec=='distant':
     source=out/'placement-closed.json';previous=Path('/tmp/blackstone361/225-placement-site-closed.json')
     eval362=Path('/tmp/baoqing20-362/design/after-225-model.py')
     assert sha(eval362)=='50c1755e8498904304bc83e6ff943fee9d0bf57d31aeb6f20a9e4f80dea7b098'
     subprocess.run([sys.executable,'-Bu',eval362,source,previous],check=True)
     outcome=json.loads(Path('/tmp/baoqing20-362/225-model-closed.json').read_bytes())
     assert outcome['host_sha256']==sha(source) and outcome['host_report_sha256']==json.loads(source.read_bytes())['report_sha256'] and outcome['previous_sha256']==sha(previous) and outcome['remaining']==[]
    if sec=='placement':
     pilot=Path('/tmp/fenyang357/development-native/after-225.py');source=out/'return-closed.json'
     assert sha(pilot)=='8b8b61c501f602e55913001062414b871ee74923d7ed31ea75247045c0081fdd'
     fcntl.flock(light,fcntl.LOCK_UN)
     try:subprocess.run([sys.executable,'-Bu',pilot,source],check=True)
     finally:fcntl.flock(light,fcntl.LOCK_EX)
     done=json.loads((pilot.parent/'225-development-returned.json').read_bytes())
     assert done['host_sha256']==sha(source) and done['host_report_sha256']==json.loads(source.read_bytes())['report_sha256'] and not done['remaining_children']
     assert done.get('deferred') or done['physical_sha256']==sha(Path(done['physical']))
     city349=Path('/tmp/jiangvilla349/225-final-runtime.py');prior357=pilot.parent/'225-development-returned.json'
     assert sha(city349)=='d4cdbad2b271604ca3fe0b46414baf31c15d22ade7c62897516220ada1cefee1'
     subprocess.run([sys.executable,'-Bu',city349,source,prior357],check=True)
     grounded=json.loads((city349.parent/'225-cpu-closed.json').read_bytes())
     assert grounded['host_receipt_sha256']==sha(source) and grounded['previous_sha256']==sha(prior357) and not grounded['remaining']

    prior=sec=='control';dest=w/'pre' if prior else out/sec;dest.mkdir(exist_ok=True);signal=out/(sec+'-closed.json');report=dest/('control-browser.json'if prior else 'main-browser.json')
    if signal.is_file()and json.loads(signal.read_bytes())['exit']==0 and json.loads(report.read_bytes())['completed']:continue
    if report.exists():raise RuntimeError('Preserve failed section before retry: '+str(dest))
    # Avoid starting beside a currently building native preview when its memory working set is large.
    tick=time.monotonic()
    while current()<1_000_000_000 and time.monotonic()-tick<45:time.sleep(2)
    top=max([Path('/tmp'),Path('/dev/shm')],key=lambda f:disk_usage(f).free)
    temp=Path(tempfile.mkdtemp(prefix='shanghai-gaoyang225-'+sec+'-',dir=top));begin=now()
    env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(w/'city225'),QA_SEGMENT=sec,QA_OUTPUT_DIR=str(dest),QA_CDP_PORT='9825',MODEL_BASE_URL='http://127.0.0.1:'+('31224'if prior else'31225')+'/')
    # Use the low-residency process layout that already passed the formal 31207 city sessions.
    launch_module=w/'low-memory-chromium.cjs'
    assert sha(launch_module)=='e2e4017f179c3d6125cb71e0de5c0223788185c6a74cceb494e186b62362c3d7'
    env['NODE_OPTIONS']=(env.get('NODE_OPTIONS','')+' --require '+str(launch_module)).strip()
    env['QA_LOW_MEMORY_LAUNCHER_SHA256']=sha(launch_module)
    if prior:
     cat=w/'city224/data/candidate-city-integrations.json';env.update(QA_CONTROL_CATALOG=str(cat),QA_CONTROL_CITY_COUNT='261',QA_CONTROL_CATALOG_SHA256=sha(cat))
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
  guest375=Path('/tmp/hengshan10-375/author/after-225.py')
  source375=out/'distant-closed.json'
  assert sha(guest375)=='3d4f9e520d6bf60829f67fa09703b291a4532408b537160b46498f4486140b3a'
  subprocess.run([sys.executable,'-B',guest375,source375],check=True)
  result375=json.loads((guest375.parents[1]/'225-distant-model-closed.json').read_bytes())
  assert result375['host_receipt_sha256']==sha(source375) and result375['host_report_sha256']==json.loads(source375.read_bytes())['report_sha256'] and not result375['remaining']
  guest376=Path('/tmp/libo-rows-376/development-native/after-225.py');prev375=guest375.parents[1]/'225-distant-model-closed.json'
  assert sha(guest376)=='e316634a2c341cc9cfb9e775768211820a1435618bac38d42c8989d7d2fa3a1b'
  subprocess.run([sys.executable,'-B',guest376,source375,prev375],check=True)
  tail376=json.loads((guest376.parent/'225-development-returned.json').read_bytes())
  assert tail376['host_receipt_sha256']==sha(source375) and tail376['previous_sha256']==sha(prev375) and tail376['all_children_exited'] and not tail376['remaining_children']
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
