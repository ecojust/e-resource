"""Exercise each viewport on the same signed site, store the reports and real process outcomes."""
import datetime,subprocess,os,time,fcntl,json,hashlib,shutil
from pathlib import Path as P
w=P(__file__).parent;s=w/'separate';s.mkdir(exist_ok=True);model=P('/workspace/e-resource/projects/shanghai/data/audit/clements-apartments-west-front-v1/map-case.json')
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def alive(profile):
 result=[]
 for f in P('/proc').glob('[0-9]*/cmdline'):
  try:b=f.read_bytes().split(b'\0')
  except OSError:continue
  if b'chromium' in b[0] and any(os.fsencode(profile) in arg for arg in b):result.append(int(f.parent.name))
 return result
def sample_processes(pid):
 processes={}
 children={}
 for f in P('/proc').glob('[0-9]*/stat'):
  try:
   fields=f.read_text().rsplit(')',1)[1].split()
   current=int(f.parent.name); parent=int(fields[1])
   processes[current]=(fields[19],(f.parent/'comm').read_text().strip())
   children.setdefault(parent,[]).append(current)
  except (OSError,IndexError,ValueError):continue
 pending=[pid];seen={}
 while pending:
  current=pending.pop()
  if current in seen or current not in processes:continue
  seen[current]=processes[current]
  pending.extend(children.get(current,[]))
 return seen

def remaining_processes(samples):
 running=[]
 for pid,(start,exe) in samples.items():
  try:stat=(P('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
  except OSError:continue
  if stat[19]==start and stat[0] not in ('Z','X'):running.append(pid)
 return sorted(running)

with (s/'runner.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 flag=w/'separate-active';flag.write_text(now())
 try:
  for phase in ['phone','desktop','architecture','mouse','touch','distant']:
   if phase=='desktop':
    subprocess.run([os.sys.executable,'-B',w/'allow-266-viewer.py'],check=True)
   directory=s/phase;directory.mkdir(exist_ok=True);report=directory/'main-browser.json';closure=directory/'process.json'
   if closure.is_file():
    prior=json.loads(closure.read_bytes());assert prior['exit_code']==0 and not prior['remaining_chromium'] and json.loads(report.read_bytes())['completed'];continue
   profile=P('/dev/shm/202-separate-city-profiles')/phase if shutil.disk_usage('/dev/shm').free>40*2**20 else w/'separate-profiles'/phase
   profile.mkdir(parents=True,exist_ok=True)
   assert not alive(profile)
   env={**os.environ,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','TMPDIR':str(profile),'QA_OUTPUT_DIR':str(directory),'SHANGHAI_PROJECT_ROOT':str(w/'202'),'MODEL_BASE_URL':'http://127.0.0.1:31202/'}
   begin=now()
   with(directory/'browser.log').open('ab',buffering=0)as log:
    proc=subprocess.Popen(['node',w/'check-separate-views.cjs',model,phase],stdout=log,stderr=log,env=env,start_new_session=True)
    observed={}
    while proc.poll() is None:
     observed.update(sample_processes(proc.pid));time.sleep(.65)
    rc=proc.returncode
   browser_ids={pid:v for pid,v in observed.items() if v[1] in ('chromium','chrome')}
   assert browser_ids,(phase,observed)
   pending=remaining_processes(observed)
   for i in range(15):
    if not pending:break
    time.sleep(.5);pending=remaining_processes(observed)
   for n in range(15):
    if not alive(profile):break
    time.sleep(1)
   result=dict(phase=phase,base=env['MODEL_BASE_URL'],exit_code=rc,pid=proc.pid,started=begin,finished=now(),remaining_chromium=sorted(set(alive(profile))|set(remaining_processes(browser_ids))),remaining_children=pending,observed_chromium={str(pid):v[0]for pid,v in browser_ids.items()},report_sha256=hashlib.sha256(report.read_bytes()).hexdigest() if report.exists()else None)
   closure.write_text(json.dumps(result,indent=2)+'\n')
   assert rc==0 and not pending and not result['remaining_chromium'] and json.loads(report.read_bytes())['completed'],result
  (s/'finished').write_text(now()+'\n')
 finally:
  flag.unlink(missing_ok=True)
