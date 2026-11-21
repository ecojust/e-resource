from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time,tempfile
from shutil import disk_usage
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/bund-signal-tower-v1';case=a/'map-case.json';out=w/'segments';out.mkdir(exist_ok=True)
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
 assert (w/'city222/data/candidate-city-integrations.json').is_file()
 with (w/'sequence.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
   fcntl.flock(light,fcntl.LOCK_EX)
   for sec in ['control','phone','desktop','return','placement','distant']:
    prior_phase=out/(sec+'-closed.json')
    if prior_phase.is_file():
     z=json.loads(prior_phase.read_bytes())
     if z['exit']==0 and json.loads(Path(z['report']).read_bytes())['completed']:
      assert z['node_closed'] and not z['remaining_chromium'] and z['chromium_pids'] and sha(Path(z['report']))==z['report_sha256']
      continue
    if sec in ('phone','desktop'):
     fcntl.flock(light,fcntl.LOCK_UN)
     subprocess.run([sys.executable,'-Bu','/tmp/signal222/city-31222/dispatch-287.py','native'if sec=='phone'else'viewer'],check=True)
     fcntl.flock(light,fcntl.LOCK_EX)
    if sec=='return':
     guest=Path('/tmp/donghu17-351/mapping/222-desktop-model.py');host=out/'desktop-closed.json'
     assert sha(guest)=='36932c32f4c1f165faad2fd47d57450f68903adf2fa9beb2e3fc8d31cfbf56f2'
     subprocess.run([sys.executable,'-B',guest,host],check=True)
     cpu=json.loads((guest.parent/'222-desktop-cpu-closed.json').read_bytes())
     assert cpu['order']==351 and cpu['host']==222 and cpu['source_sha256']==sha(host) and cpu['host_report_sha256']==json.loads(host.read_bytes())['report_sha256'] and cpu['remaining']==[]
     inspection=Path('/tmp/dongping364/first-geometry/after-222.py');assert sha(inspection)=='8994c00c61699dc2e28383b98a8f6b985a67e323eefbdd9d5ad4dee5d51ac55e'
     previous=guest.parent/'222-desktop-cpu-closed.json'
     subprocess.run([sys.executable,'-Bu',inspection,host,previous],check=True)
     ret=json.loads((inspection.parent/'222-desktop-returned.json').read_bytes());assert ret['host_receipt_sha256']==sha(host) and ret['previous_sha256']==sha(previous) and ret['host_report_sha256']==cpu['host_report_sha256'] and not ret['remaining']
     trial=Path('/tmp/anfu284-368/first-geometry/start.py');upstream=inspection.parent/'222-desktop-returned.json';outcome=trial.parent/'returned.json'
     assert sha(trial)=='dfc25f0d1062a6fa55964801e62756abc13d3a2394b345bf6d8acfd45e4b76ac'
     if not outcome.is_file():
      subprocess.run([sys.executable,'-Bu',trial,upstream])
     observed=json.loads(outcome.read_bytes())
     assert observed['order']==368 and observed['prior_sha256']==sha(upstream) and observed['all_children_exited'] and observed['remaining_children']==[] and observed['log_sha256']==sha(trial.parent/'start.log')
     if Path('/tmp/swire287/222-viewer-deferred.json').is_file() and not Path('/tmp/swire287/independent-closed.json').exists():
      fcntl.flock(light,fcntl.LOCK_UN)
      try:subprocess.run([sys.executable,'-Bu','/tmp/signal222/city-31222/dispatch-287.py','viewer','desktop'],check=True)
      finally:fcntl.flock(light,fcntl.LOCK_EX)
    if sec=='placement':
     physical=out/'return-closed.json';root=Path('/tmp/adeodata353/development-native');starter=root/'start.py';assert sha(starter)=='50dcd03ca0a0a5370297f764a9ec81c0ac616ff40bb9964cf9423954a3c44a48'
     fcntl.flock(light,fcntl.LOCK_UN)
     try:
      child=subprocess.run([sys.executable,'-Bu',starter,physical,'ade10ed264ab23b27ad040e59f59f0983886e156fbd7eb28c61fb36665d73d3c'])
      done=json.loads((root/'physical.json').read_bytes());assert done['order']==353 and done['all_children_exited']and done['remaining_children']==[]and done['exit_code']==child.returncode
     finally:fcntl.flock(light,fcntl.LOCK_EX)
     work=Path('/dev/shm/door-and-stair-reference/354-design/after-222.py');assert sha(work)=='0b4481264320be6ac699ac4bed589ea59144571e0d946e42bc14615dfa4a9376'
     subprocess.run([sys.executable,'-Bu',work,physical,root/'physical.json'],check=True)
     ret=json.loads(Path('/tmp/yuyuan-huaihai354/222-pilot-closed.json').read_bytes())
     assert ret['order']==354 and ret['host_sha256']==sha(physical)and ret['previous_sha256']==sha(root/'physical.json')and not ret['remaining']
     check367=Path('/tmp/anfu233-367/mapping/after-222-return.py');prior354=Path('/tmp/yuyuan-huaihai354/222-pilot-closed.json')
     assert sha(check367)=='b114685d6bb16e80f0fe1baeb697783484bd0bcd1341de93c4d52c5b5558565f'
     subprocess.run([sys.executable,'-Bu',check367,physical,prior354],check=True)
     checked=json.loads(Path('/tmp/anfu233-367/222-return-model-closed.json').read_bytes())
     assert checked.get('host_receipt_sha256',checked.get('host_sha256',checked.get('source_sha256')))==sha(physical) and checked['host_report_sha256']==sha(Path(json.loads(physical.read_bytes())['report'])) and checked['previous_sha256']==sha(prior354) and checked['remaining']==[]
     correction=Path('/tmp/taiyuan363/mapping/after-222-porch.py')
     preceding=Path('/tmp/anfu233-367/222-return-model-closed.json')
     assert sha(correction)=='88ca60fa41742fb74bad7672eb9a92093bba460727739e711a45b4c5f0bdbc0e'
     subprocess.run([sys.executable,'-Bu',correction,physical,preceding],check=True)
     actual=json.loads(Path('/tmp/taiyuan363/222-revised-model-closed.json').read_bytes())
     assert actual['host_receipt_sha256']==sha(physical) and actual['host_report_sha256']==checked['host_report_sha256'] and actual['previous_sha256']==sha(preceding) and actual['all_children_exited'] and actual['remaining']==actual['remaining_children']==[]
    if sec=='distant':
     fix=Path('/tmp/huaihai-1634-research/east-door-supplement');offer=fix/'after-222-placement.py';prior_placement=out/'placement-closed.json'
     assert sha(offer)=='7544085467c36c5cd43a7742dbedd700104c2322a066df11d537cf313beefa53' and sha(fix/'focus-through-map-controls.cjs')=='b213f1ed076bd72de6f040050636ff0c443920239be214fdd879b3e1af97ca6d'
     subprocess.run([sys.executable,'-Bu',offer,prior_placement],check=True)
     got=json.loads((fix/'after-222-placement.json').read_bytes());assert got['order']==217 and got['host']==222 and got['host_receipt_sha256']==sha(prior_placement) and got['node_closed'] and not got['remaining_children']
    prior=sec=='control';dest=w/'pre' if prior else out/sec;dest.mkdir(exist_ok=True);signal=out/(sec+'-closed.json');report=dest/('control-browser.json'if prior else 'main-browser.json')
    if signal.is_file()and json.loads(signal.read_bytes())['exit']==0 and json.loads(report.read_bytes())['completed']:continue
    if report.exists():raise RuntimeError('Preserve failed section before retry: '+str(dest))
    # Avoid starting beside a currently building native preview when its memory working set is large.
    tick=time.monotonic()
    while current()<1_000_000_000 and time.monotonic()-tick<45:time.sleep(2)
    top=max([Path('/tmp'),Path('/dev/shm')],key=lambda f:disk_usage(f).free)
    temp=Path(tempfile.mkdtemp(prefix='shanghai-signal222-'+sec+'-',dir=top));begin=now()
    env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(w/'city222'),QA_SEGMENT=sec,QA_OUTPUT_DIR=str(dest),QA_CDP_PORT='9922',MODEL_BASE_URL='http://127.0.0.1:'+('31221'if prior else'31222')+'/')
    if prior:
     cat=w/'city221/data/candidate-city-integrations.json';env.update(QA_CONTROL_CATALOG=str(cat),QA_CONTROL_CITY_COUNT='258',QA_CONTROL_CATALOG_SHA256=sha(cat))
    signed=w/'verified-scripts';signed.mkdir(exist_ok=True);driver=w/'check-map.cjs';version=signed/(sha(driver)+'.cjs')
    if not version.is_file():shutil.copyfile(driver,version)
    assert sha(version)==sha(driver)
    print('start',sec,begin,current(),disk_usage(top).free,flush=True)
    with(out/(sec+'.log')).open('ab',buffering=0)as log:
     proc=subprocess.Popen(['node',w/'check-map.cjs',case,*(['--control']if prior else[])],env=env,stdout=log,stderr=log,start_new_session=True)
     import psutil
     observer=psutil.Process(proc.pid);observed={};peak=0;events=Path('/sys/fs/cgroup/memory.events').read_text()
     while proc.poll() is None:
      try:
       kids=observer.children(recursive=True);peak=max(peak,sum(v.memory_info().rss for v in [observer,*kids]))
       for child in kids:
        if child.name()in('chrome','chromium','headless_shell'):observed[child.pid]=child.create_time()
      except (psutil.NoSuchProcess,psutil.ZombieProcess):pass
      time.sleep(.12)
     rc=proc.returncode
    def survivors():
     present=set(live(temp))
     for pid,born in observed.items():
      try:
       child=psutil.Process(pid)
       if child.create_time()==born and child.status() not in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD):present.add(pid)
      except (psutil.NoSuchProcess,psutil.ZombieProcess):pass
     return sorted(present)
    for attempt in range(30):
     if not survivors():break
     time.sleep(.20)
    closure=dict(order=222,process_rss_highwater=peak,cgroup_before=events,cgroup_after=Path('/sys/fs/cgroup/memory.events').read_text(),checker_path=str(version),checker_sha256=sha(version),name=sec,phase=sec,started=begin,finished=now(),exit=rc,exit_code=rc,node_pid=proc.pid,node_pids=[proc.pid],node_closed=proc.poll() is not None,chromium_pids=sorted(observed),chromium_births=observed,remaining_chromium=survivors(),remaining_children=survivors(),profile=str(temp),report=str(report),report_sha256=sha(report) if report.is_file() else None)
    wr(signal,closure)
    if rc==0:assert observed and not closure['remaining_chromium'] and closure['node_closed']
    print('exit',sec,closure,flush=True)
    if temp.is_dir() and not any(temp.iterdir()):temp.rmdir()
    assert rc==0 and not closure['remaining_chromium'] and json.loads(report.read_bytes())['completed'],closure
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
    src=out/r['segment']/v['file'];assert sha(src)==v['sha256'];target=dst/v['file']
    if not target.exists():os.link(src,target)
    assert sha(target)==sha(src)
   for key in ('bridgeAtReturn','neighborSelection','keyboardSearch','unloadedWhileAway','ground','groundChecks'):
    if key in r:merged[key]=r[key]
  for r in records:assert r['completed'] and not r['errors'] and not r['failed']
  merged['freshNear']=records[-1]['freshNear']
  merged.update(segment='five independent completed official map sessions',finished=records[-1]['finished'],segments=[json.loads((out/(s+'-closed.json')).read_bytes()) for s in ['phone','desktop','return','placement','distant']]);wr(dst/'main-browser.json',merged)
if __name__=='__main__':
 try:run()
 except Exception:
  (w/'exit').write_text('1\n');raise
 (w/'exit').write_text('0\n')
