from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time,tempfile
from shutil import disk_usage
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/young-apartments-v1';case=a/'map-case.json';out=w/'segments';out.mkdir(exist_ok=True)
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
     try:subprocess.run([sys.executable,'-Bu',w/'host-279.py','native'if sec=='phone'else'viewer'],check=True)
     finally:fcntl.flock(light,fcntl.LOCK_EX)
    if sec=='return':
     fcntl.flock(light,fcntl.LOCK_UN)
     try:subprocess.run([sys.executable,'-Bu',w/'after-desktop.py'],check=True)
     finally:fcntl.flock(light,fcntl.LOCK_EX)
    prior=sec=='control';dest=w/'pre' if prior else out/sec;dest.mkdir(exist_ok=True);signal=out/(sec+'-closed.json');report=dest/('control-browser.json'if prior else 'main-browser.json')
    if signal.is_file()and json.loads(signal.read_bytes())['exit']==0 and json.loads(report.read_bytes())['completed']:continue
    if report.exists():raise RuntimeError('Preserve failed section before retry: '+str(dest))
    # Avoid starting beside a currently building native preview when its memory working set is large.
    tick=time.monotonic()
    while current()<1_000_000_000 and time.monotonic()-tick<45:time.sleep(2)
    candidates=[Path('/tmp'),Path('/dev/shm')]
    if disk_usage('/dev/net').free>=20*1024*1024:candidates.append(Path('/dev/net'))
    top=max(candidates,key=lambda f:disk_usage(f).free)
    temp=Path(tempfile.mkdtemp(prefix='shanghai-young214-'+sec+'-',dir=top));begin=now()
    env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(w/'city214'),QA_SEGMENT=sec,QA_OUTPUT_DIR=str(dest),QA_CDP_PORT='9814',MODEL_BASE_URL='http://127.0.0.1:'+('31213'if prior else'31214')+'/')
    # Use the low-residency process layout that already passed the formal 31207 city sessions.
    launch_module=w/'low-memory-chromium.cjs'
    assert sha(launch_module)=='e2e4017f179c3d6125cb71e0de5c0223788185c6a74cceb494e186b62362c3d7'
    env['NODE_OPTIONS']=(env.get('NODE_OPTIONS','')+' --require '+str(launch_module)).strip()
    env['QA_LOW_MEMORY_LAUNCHER_SHA256']=sha(launch_module)
    if prior:
     cat=w/'city213/data/candidate-city-integrations.json';env.update(QA_CONTROL_CATALOG=str(cat),QA_CONTROL_CITY_COUNT='250',QA_CONTROL_CATALOG_SHA256=sha(cat))
    print('start',sec,begin,current(),disk_usage(top).free,flush=True)
    with(out/(sec+'.log')).open('ab',buffering=0)as log:
     proc=subprocess.Popen(['node',w/'check-map.cjs',case,*(['--control']if prior else[])],env=env,stdout=log,stderr=log,start_new_session=True)
     import psutil
     observed=set()
     watchdog=psutil.Process(proc.pid)
     while proc.poll() is None:
      try:
       observed.update(child.pid for child in watchdog.children(recursive=True) if child.name() in ('chromium','chrome','headless_shell'))
      except psutil.NoSuchProcess:pass
      time.sleep(.4)
     rc=proc.returncode
    for j in range(20):
     if not live(temp):break
     time.sleep(.5)
    closure=dict(name=sec,launcher_sha256=sha(launch_module),started=begin,finished=now(),exit=rc,node_pid=proc.pid,node_closed=not psutil.pid_exists(proc.pid),chromium_pids=sorted(observed),remaining_chromium=live(temp),profile=str(temp),report=str(report),report_sha256=sha(report)if report.exists()else None);wr(signal,closure)
    print('exit',sec,closure,flush=True)
    if temp.is_dir() and not any(temp.iterdir()):temp.rmdir()
    assert rc==0 and not closure['remaining_chromium'] and json.loads(report.read_bytes())['completed'],closure
  records=[json.loads((out/k/'main-browser.json').read_bytes())for k in ['phone','desktop','return','placement','distant']];dst=w/'post';dst.mkdir(exist_ok=True);merged={**records[0]}
  for key in ('catalog','caseSha256','scriptSha256','bindings','camera'):assert all(r[key]==records[0][key]for r in records)
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
