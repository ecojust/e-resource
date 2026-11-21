"""Exercise each viewport on the same signed site, store the reports and real process outcomes."""
import datetime,subprocess,os,time,fcntl,json,hashlib,shutil
from pathlib import Path as P
w=P(__file__).parent;
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

with (w/'runner.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for phase in ['before','phone','desktop','architecture','mouse','touch','distant']:
  if phase=='phone':subprocess.run(['python','-Bu',w/'return-276.py'],check=True)
  if phase=='desktop':subprocess.run(['python','-Bu',w/'offer-276-after-phone.py'],check=True)
  if phase=='desktop':
   while not (w/'325-cpu-return.json').is_file():time.sleep(.5)
   cpu=json.loads((w/'325-cpu-return.json').read_bytes());assert cpu['passed'] and cpu['remaining']==[] and cpu['exit']==0 and cpu['host_sha256']==hashlib.sha256((w/'phone/process.json').read_bytes()).hexdigest()
  d=w/phase;d.mkdir(exist_ok=True)
  rp=d/('control-browser.json' if phase=='before' else 'main-browser.json')
  rcfile=w/(phase+'.exit');close=d/'process.json'
  if close.is_file():
   row=json.loads(close.read_bytes())
   assert row['exit_code']==0 and not row['remaining_chromium'] and rp.is_file()
   continue
  assert not rp.exists(), 'Archive incomplete evidence before a new run'
  began=now()
  proc=subprocess.Popen(['python','-B',w/'run.py',phase],start_new_session=True)
  observed={}
  while proc.poll() is None:
   current=sample_processes(proc.pid)
   if any(p not in observed for p in current):
    observed.update(current)
    journal=d/'live-census.json';temp=journal.with_suffix('.new');temp.write_text(json.dumps(dict(stage=phase,started=began,wrapper=proc.pid,processes=observed)));temp.replace(journal)
   time.sleep(.5)
  rc=proc.returncode;profile=P(os.environ.get('CITY212_MATERIALIZED','/dev/shm/city-212-actual'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes())['completed'] and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
 viewer=P('/tmp/royal212/standalone-31212')
 assert hashlib.sha256((viewer/'inputs.json').read_bytes()).hexdigest()=='69d7770c4ab40113eb6443086553d0b50f1a238c6de9d9a79d8d7570bccfcae5'
 subprocess.run(['python','-Bu',viewer/'run.py',w/'distant/process.json'],check=True)
 final_view=json.loads((viewer/'closed.json').read_bytes())
 assert final_view['passed'] and final_view['node_closed'] and final_view['chromium_pids'] and not final_view['remaining_chromium']
 (w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':7})+'\n')
