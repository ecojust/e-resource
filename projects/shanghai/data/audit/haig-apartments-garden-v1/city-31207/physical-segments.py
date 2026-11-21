from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time,tempfile
from shutil import disk_usage
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/haig-apartments-garden-v1';case=a/'map-case.json';out=w/'segments';out.mkdir(exist_ok=True)
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
 assert (w/'city207/data/candidate-city-integrations.json').is_file()
 with (w/'sequence.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
   fcntl.flock(light,fcntl.LOCK_EX)
   for sec in ['control','phone','desktop','return','placement','distant']:
    if sec=='phone':
     fcntl.flock(light,fcntl.LOCK_UN)
     subprocess.run([sys.executable,'-Bu','/tmp/haig207/207-city/dispatch-271.py'],check=True)
     fcntl.flock(light,fcntl.LOCK_EX)
    prior=sec=='control';dest=w/'pre' if prior else out/sec;dest.mkdir(exist_ok=True);signal=out/(sec+'-closed.json');report=dest/('control-browser.json'if prior else 'main-browser.json')
    if signal.is_file()and json.loads(signal.read_bytes())['exit']==0 and json.loads(report.read_bytes())['completed']:continue
    if report.exists():raise RuntimeError('Preserve failed section before retry: '+str(dest))
    # Avoid starting beside a currently building native preview when its memory working set is large.
    tick=time.monotonic()
    while current()<1_000_000_000 and time.monotonic()-tick<45:time.sleep(2)
    top=max([Path('/tmp'),Path('/dev/shm')],key=lambda f:disk_usage(f).free)
    temp=Path(tempfile.mkdtemp(prefix='shanghai-haig207-'+sec+'-',dir=top));begin=now()
    env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(w/'city207'),QA_SEGMENT=sec,QA_OUTPUT_DIR=str(dest),QA_CDP_PORT='9907',MODEL_BASE_URL='http://127.0.0.1:'+('31206'if prior else'31207')+'/')
    if prior:
     cat=w/'city206/data/candidate-city-integrations.json';env.update(QA_CONTROL_CATALOG=str(cat),QA_CONTROL_CITY_COUNT='243',QA_CONTROL_CATALOG_SHA256=sha(cat))
    print('start',sec,begin,current(),disk_usage(top).free,flush=True)
    with(out/(sec+'.log')).open('ab',buffering=0)as log:
     proc=subprocess.Popen(['node',w/('check-return-v2.cjs' if sec=='return' else 'check-map.cjs'),case,*(['--control']if prior else[])],env=env,stdout=log,stderr=log,start_new_session=True);rc=proc.wait()
    for j in range(20):
     if not live(temp):break
     time.sleep(.5)
    closure=dict(name=sec,started=begin,finished=now(),exit=rc,node_pid=proc.pid,remaining_chromium=live(temp),profile=str(temp),report=str(report),report_sha256=sha(report)if report.exists()else None);wr(signal,closure)
    print('exit',sec,closure,flush=True)
    if temp.is_dir() and not any(temp.iterdir()):temp.rmdir()
    assert rc==0 and not closure['remaining_chromium'] and json.loads(report.read_bytes())['completed'],closure
  records=[json.loads((out/k/'main-browser.json').read_bytes())for k in ['phone','desktop','return','placement','distant']];dst=w/'post';dst.mkdir(exist_ok=True);merged={**records[0]}
  for key in ('catalog','caseSha256','bindings','camera'):assert all(r[key]==records[0][key]for r in records)
  scripts={r['segment']:r['scriptSha256'] for r in records}
  assert all(digest==sha(w/('check-return-v2.cjs' if segment=='return' else 'check-map.cjs')) for segment,digest in scripts.items())
  merged['segment_scripts']=scripts
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
