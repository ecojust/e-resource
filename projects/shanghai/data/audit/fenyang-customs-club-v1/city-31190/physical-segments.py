from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time,tempfile
from shutil import disk_usage
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/fenyang-customs-club-v1';case=a/'map-case.json';out=w/'segments';out.mkdir(exist_ok=True)
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
   for sec in ['control','phone','desktop','return','placement','distant']:
    prior=sec=='control';dest=w/'pre' if prior else out/sec;dest.mkdir(exist_ok=True);signal=out/(sec+'-closed.json');report=dest/('control-browser.json'if prior else 'main-browser.json')
    if signal.is_file()and json.loads(signal.read_bytes())['exit']==0 and json.loads(report.read_bytes())['completed']:continue
    if report.exists():raise RuntimeError('Preserve failed section before retry: '+str(dest))
    if sec=='phone':
     control=json.loads((out/'control-closed.json').read_bytes())
     assert control['exit']==0 and not control['remaining_chromium'] and not Path('/proc',str(control['node_pid'])).exists()
     approved=Path('/tmp/chienhsin257/native-closed.json')
     print('Old city is closed. Holding the phone launch for the scheduled 257 native job.',flush=True)
     while not approved.is_file():time.sleep(2)
     receipt=json.loads(approved.read_bytes());assert receipt['exit']==0
     joint=receipt['files'];assert set(joint)=={'raw','full','lod','native'}
     project=p/'assets/models/candidates'
     model=next(x for x in project.iterdir()if (x/joint['native']['file']).is_file())
     for item in joint.values():
      file=model/item['file'];assert file.stat().st_size==item['bytes'] and sha(file)==item['sha256']
     wr(out/'257-native-handoff.json',dict(control_sha256=sha(out/'control-closed.json'),native_receipt_sha256=sha(approved),native_four_files=joint,finished=now()))
    if sec=='desktop':
     phone=json.loads((out/'phone-closed.json').read_bytes())
     assert phone['exit']==0 and not phone['remaining_chromium'] and not Path('/proc',str(phone['node_pid'])).exists()
     approved=Path('/tmp/eastasian256/standalone-closed.json')
     print('Phone is closed. Holding the desktop launch for the scheduled 256 viewer.',flush=True)
     while not approved.is_file():time.sleep(2)
     receipt=json.loads(approved.read_bytes());assert receipt['order']==256 and receipt['exit_code']==0 and receipt['passed'] and receipt['all_exited'] and not receipt['remaining_chromium']
     wr(out/'256-viewer-handoff.json',dict(phone_sha256=sha(out/'phone-closed.json'),viewer_receipt_sha256=sha(approved),finished=now()))
    fcntl.flock(light,fcntl.LOCK_EX)
    # Avoid starting beside a currently building native preview when its memory working set is large.
    tick=time.monotonic()
    while current()<1_000_000_000 and time.monotonic()-tick<45:time.sleep(2)
    top=max([Path('/tmp'),Path('/dev/shm')],key=lambda f:disk_usage(f).free)
    temp=Path(tempfile.mkdtemp(prefix='shanghai-fenyang190-'+sec+'-',dir=top));begin=now()
    env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(w/'city190'),QA_SEGMENT=sec,QA_OUTPUT_DIR=str(dest),QA_CDP_PORT='9890',MODEL_BASE_URL='http://127.0.0.1:'+('31189'if prior else'31190')+'/')
    if prior:
     cat=w/'city189/data/candidate-city-integrations.json';env.update(QA_CONTROL_CATALOG=str(cat),QA_CONTROL_CITY_COUNT='226',QA_CONTROL_CATALOG_SHA256=sha(cat))
    print('start',sec,begin,current(),disk_usage(top).free,flush=True)
    with(out/(sec+'.log')).open('ab',buffering=0)as log:
     driver=w/('paired-placement.cjs' if sec=='placement' else 'check-direct-distant.cjs' if sec=='distant' else 'check-map.cjs')
     proc=subprocess.Popen(['node',driver,case,*(['--control']if prior else[])],env=env,stdout=log,stderr=log,start_new_session=True);rc=proc.wait()
    for j in range(20):
     if not live(temp):break
     time.sleep(.5)
    closure=dict(name=sec,started=begin,finished=now(),exit=rc,node_pid=proc.pid,remaining_chromium=live(temp),profile=str(temp),report=str(report),report_sha256=sha(report)if report.exists()else None);wr(signal,closure)
    fcntl.flock(light,fcntl.LOCK_UN)
    print('exit',sec,closure,flush=True)
    if temp.is_dir() and not any(temp.iterdir()):temp.rmdir()
    assert rc==0 and not closure['remaining_chromium'] and json.loads(report.read_bytes())['completed'],closure
  records=[json.loads((out/k/'main-browser.json').read_bytes())for k in ['phone','desktop','return','placement','distant']];dst=w/'post';dst.mkdir(exist_ok=True);merged={**records[0]}
  for key in ('catalog','caseSha256','bindings','camera'):assert all(r[key]==records[0][key]for r in records)
  assert all(r['scriptSha256']==sha(w/('check-paired-placement.cjs' if r['segment']=='placement' else 'check-direct-distant.cjs' if r['segment']=='distant' else 'check-map.cjs')) for r in records)
  merged['segmentDriverSha256']={r['segment']:r['scriptSha256'] for r in records}
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
