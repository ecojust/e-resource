from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time,tempfile
from shutil import disk_usage
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/dauphine-apartments-v1';case=a/'map-case.json';out=w/'segments';out.mkdir(exist_ok=True)
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
 with (w/'sequence.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
   fcntl.flock(light,fcntl.LOCK_EX)
   for sec in ['control','phone','desktop','return','placement','distant']:
    if sec=='phone':
     work=Path('/tmp/dauphine200-final-work')
     old=out/'control-closed.json';control_report=w/'pre/control-browser.json';state=json.loads(old.read_bytes())
     assert state['exit']==0 and not state['remaining_chromium'] and json.loads(control_report.read_bytes())['completed']
     target=work/'control-closed.json';tmp=target.with_suffix('.tmp')
     wr(tmp,{**state,'passed':True,'report':str(control_report),'report_sha256':sha(control_report),'driver_exit_file':str(old)})
     os.replace(tmp,target)
     friend=Path('/tmp/zili265/native-closed.json')
     while not friend.exists() and not (work/'265-rescheduled.json').exists():time.sleep(2)
     if friend.exists():
      accepted=json.loads(friend.read_bytes())
      assert accepted['exit']==0 and accepted['passed'] and not accepted.get('remaining',[])
    if sec=='desktop':
     work=Path('/tmp/dauphine200-final-work')
     prior_phone=out/'phone-closed.json'
     phone_state=json.loads(prior_phone.read_bytes())
     phone_report=Path(phone_state['report'])
     assert phone_state['exit']==0 and not phone_state['remaining_chromium'] and sha(phone_report)==phone_state['report_sha256']
     assert json.loads(phone_report.read_bytes())['completed']
     ready=Path('/workspace/e-resource/projects/shanghai/data/audit/puguang-ymca-east-entrance-v1/31263-all-http.json')
     finish=Path('/tmp/puguang263/standalone-closed.json')
     deferred=work/'263-viewer-deferred.json'
     fcntl.flock(light,fcntl.LOCK_UN)
     try:
      agreed=ready.is_file() and not deferred.exists()
      if agreed:
       rr=json.loads(ready.read_bytes())
       assert rr['passed'] and rr['order']==263 and rr['port']==31263
      elif not deferred.exists():
       temp=deferred.with_suffix('.new')
       wr(temp,{'order':263,'deferred':True,'browser_started':False,'reason':'31263 all-HTTP receipt pending at the physical 200 phone closure','checked':now()})
       os.replace(temp,deferred)
      signal_mobile=work/'phone-closed.json'
      if not signal_mobile.exists():
       temp=signal_mobile.with_suffix('.new')
       wr(temp,{**phone_state,'order':200,'passed':True,'ready_263':agreed,'control_closed_file':str(prior_phone)})
       os.replace(temp,signal_mobile)
      if agreed:
       while not finish.is_file():time.sleep(.5)
       outcome=json.loads(finish.read_bytes())
       assert outcome['passed'] and outcome['all_exited'] and outcome['exit_code']==0 and not outcome['remaining_chromium']
     finally:
      fcntl.flock(light,fcntl.LOCK_EX)
    prior=sec=='control';dest=w/'pre' if prior else out/sec;dest.mkdir(exist_ok=True);signal=out/(sec+'-closed.json');report=dest/('control-browser.json'if prior else 'main-browser.json')
    if signal.is_file()and json.loads(signal.read_bytes())['exit']==0 and json.loads(report.read_bytes())['completed']:continue
    if report.exists():raise RuntimeError('Preserve failed section before retry: '+str(dest))
    # Avoid starting beside a currently building native preview when its memory working set is large.
    tick=time.monotonic()
    while current()<1_000_000_000 and time.monotonic()-tick<45:time.sleep(2)
    top=max([Path('/tmp'),Path('/dev/shm')],key=lambda f:disk_usage(f).free)
    temp=Path(tempfile.mkdtemp(prefix='shanghai-dauphine200-'+sec+'-',dir=top));begin=now()
    env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(w/'city200'),QA_SEGMENT=sec,QA_OUTPUT_DIR=str(dest),QA_CDP_PORT='9900',MODEL_BASE_URL='http://127.0.0.1:'+('31199'if prior else'31200')+'/')
    if sec=='placement':env['NODE_OPTIONS']='--require=/tmp/dauphine200-final-work/roof-viewport.cjs'
    if prior:
     cat=w/'city199/data/candidate-city-integrations.json';env.update(QA_CONTROL_CATALOG=str(cat),QA_CONTROL_CITY_COUNT='236',QA_CONTROL_CATALOG_SHA256=sha(cat))
    print('start',sec,begin,current(),disk_usage(top).free,flush=True)
    with(out/(sec+'.log')).open('ab',buffering=0)as log:
     proc=subprocess.Popen(['node',w/'check-map.cjs',case,*(['--control']if prior else[])],env=env,stdout=log,stderr=log,start_new_session=True);rc=proc.wait()
    for j in range(20):
     if not live(temp):break
     time.sleep(.5)
    closure=dict(name=sec,started=begin,finished=now(),exit=rc,node_pid=proc.pid,remaining_chromium=live(temp),profile=str(temp),report=str(report),report_sha256=sha(report)if report.exists()else None);wr(signal,closure)
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
