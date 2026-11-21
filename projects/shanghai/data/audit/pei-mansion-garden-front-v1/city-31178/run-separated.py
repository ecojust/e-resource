"""Exercise each viewport on the same signed site, store the reports and real process outcomes."""
import datetime,subprocess,os,time,fcntl,json,hashlib,shutil
from pathlib import Path as P
w=P(__file__).parent;s=w/'separate';s.mkdir(exist_ok=True);model=P('/workspace/e-resource/projects/shanghai/data/audit/pei-mansion-garden-front-v1/map-case.json')
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def alive(profile):
 result=[]
 for f in P('/proc').glob('[0-9]*/cmdline'):
  try:b=f.read_bytes().split(b'\0')
  except OSError:continue
  if b'chromium' in b[0] and any(os.fsencode(profile) in arg for arg in b):result.append(int(f.parent.name))
 return result
with (s/'runner.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 flag=w/'separate-active';flag.write_text(now())
 try:
  for phase in ['phone','desktop','architecture','mouse','touch','distant']:
   directory=s/phase;directory.mkdir(exist_ok=True);report=directory/'main-browser.json';closure=directory/'process.json'
   if closure.is_file():
    prior=json.loads(closure.read_bytes());assert prior['exit_code']==0 and not prior['remaining_chromium'] and json.loads(report.read_bytes())['completed'];continue
   profile=P('/dev/shm/178-separate-city-profiles')/phase if shutil.disk_usage('/dev/shm').free>40*2**20 else w/'separate-profiles'/phase
   profile.mkdir(parents=True,exist_ok=True)
   assert not alive(profile)
   env={**os.environ,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','TMPDIR':str(profile),'QA_OUTPUT_DIR':str(directory),'SHANGHAI_PROJECT_ROOT':str(w/'live178'),'MODEL_BASE_URL':'http://127.0.0.1:31178/'}
   begin=now()
   with(directory/'browser.log').open('ab',buffering=0)as log:
    proc=subprocess.Popen(['node',w/('check-input-and-street.cjs' if phase=='mouse' else 'check-touch-route.cjs' if phase=='touch' else 'check-separate-views.cjs'),model,phase],stdout=log,stderr=log,env=env,start_new_session=True);rc=proc.wait()
   for n in range(15):
    if not alive(profile):break
    time.sleep(1)
   result=dict(phase=phase,base=env['MODEL_BASE_URL'],exit_code=rc,pid=proc.pid,started=begin,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(report.read_bytes()).hexdigest() if report.exists()else None)
   closure.write_text(json.dumps(result,indent=2)+'\n')
   assert rc==0 and not result['remaining_chromium'] and json.loads(report.read_bytes())['completed'],result
  (s/'finished').write_text(now()+'\n')
 finally:
  flag.unlink(missing_ok=True)
