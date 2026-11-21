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
  if phase in ('phone','desktop'):
   subprocess.run(['python','-B',w/'offer-282.py','before' if phase=='phone' else 'phone'],check=True)
  if phase=='phone':
   guest=P('/tmp/kemi334/design/217-window.py')
   assert hashlib.sha256(guest.read_bytes()).hexdigest()=='11068eaad7c3351df18340daefe5d480f9974f3e7a50d254677c0aeeec187ce8'
   subprocess.run(['python','-B',guest,w/'before/process.json'],check=True)
  if phase=='architecture':
   guest=P('/tmp/shanghai-main-278/217-desktop-cpu.py')
   assert hashlib.sha256(guest.read_bytes()).hexdigest()=='483c55f3caef8c8b403616353b4eccd8b2017cb693827c7b3e89904f6db625ae'
   subprocess.run(['python','-B',guest,w/'desktop/process.json'],check=True)
   returned=json.loads(P('/tmp/shanghai-main-278/217-desktop-cpu-closed.json').read_bytes())
   assert returned['source_sha256']==hashlib.sha256((w/'desktop/process.json').read_bytes()).hexdigest() and not returned['remaining']
  if phase=='mouse':
   guest=P('/tmp/shanghai-main-217/offer-348-development.py')
   assert hashlib.sha256(guest.read_bytes()).hexdigest()=='3210f7366e1cf30c23213567aa816915c53335d0aa5f34de1728e8e37af61da2'
   subprocess.run(['python','-B',guest,'native'],check=True)
   returned=json.loads(P('/tmp/shanghai-main-217/348-native-returned.json').read_bytes())
   assert returned['all_children_exited'] and not returned['remaining_children'] and returned['guest']==348
  if phase=='touch':
   guest=P('/tmp/fuxing341/217-mouse-cpu.py')
   assert hashlib.sha256(guest.read_bytes()).hexdigest()=='62bd4f3b39650831c1b8752092ad4a0c569e655473f3fe070cee0c0a8766fcf6'
   subprocess.run(['python','-B',guest,w/'mouse/process.json'],check=True)
   result=json.loads(P('/tmp/fuxing341/217-mouse-cpu-closed.json').read_bytes())
   assert result['host_receipt_sha256']==hashlib.sha256((w/'mouse/process.json').read_bytes()).hexdigest() and result['remaining']==[]
  if phase=='touch':
   guest=P('/tmp/shanghai-main-217/offer-348-development.py')
   assert hashlib.sha256(guest.read_bytes()).hexdigest()=='3210f7366e1cf30c23213567aa816915c53335d0aa5f34de1728e8e37af61da2'
   subprocess.run(['python','-B',guest,'regression'],check=True)
   returned=json.loads(P('/tmp/shanghai-main-217/348-regression-returned.json').read_bytes())
   assert returned['all_children_exited'] and not returned['remaining_children'] and returned['guest']==348
  if phase=='distant':
   guest=P('/tmp/park-fuxing338/design/217-touch-cpu.py')
   assert hashlib.sha256(guest.read_bytes()).hexdigest()=='11f9e5065c6a211c3e94a52b7960bec992d16852f4e38a68bc53f06bdf6d6240'
   subprocess.run(['python','-B',guest,w/'touch/process.json'],check=True)
   returned=json.loads(P('/tmp/park-fuxing338/217-touch-cpu-closed.json').read_bytes())
   assert returned['host_receipt_sha256']==hashlib.sha256((w/'touch/process.json').read_bytes()).hexdigest() and not returned['remaining']
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
   observed.update(sample_processes(proc.pid))
   time.sleep(.5)
  rc=proc.returncode;profile=P(os.environ.get('CITY217_MATERIALIZED','/dev/shm/city-217-actual'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes())['completed'] and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
 guest=P('/tmp/anhe345/217-after-distant.py')
 assert hashlib.sha256(guest.read_bytes()).hexdigest()=='e921cb0939cbb6b11dab9e25becc416b0efe974506561c500c30ed8a391b91b6'
 subprocess.run(['python','-B',guest,w/'distant/process.json'],check=True)
 returned=json.loads(P('/tmp/anhe345/217-distant-mesh-closed.json').read_bytes())
 assert returned['host_receipt_sha256']==hashlib.sha256((w/'distant/process.json').read_bytes()).hexdigest() and returned['remaining']==[]
 (w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':7})+'\n')
