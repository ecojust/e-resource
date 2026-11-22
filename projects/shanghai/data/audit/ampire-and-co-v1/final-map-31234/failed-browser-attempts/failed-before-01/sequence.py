"""Exercise each viewport on the same signed site, store the reports and real process outcomes."""
import sys,datetime,subprocess,os,time,fcntl,json,hashlib,shutil
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
   prior_phase='before' if phase=='phone' else 'phone'
   subphase='native' if phase=='phone' else 'viewer'
   previous=json.loads((w/prior_phase/'process.json').read_bytes())
   assert previous['exit_code']==0 and previous['node_closed'] and previous['remaining_chromium']==[]
   subprocess.run([sys.executable,'-B',w.parent/'offer-299.py',subphase,str(w/prior_phase/'process.json')],check=True)
  if phase=='mouse':
   entry=P('/tmp/jiangsu796-449/early-234-development/offer-234.py');assert hashlib.sha256(entry.read_bytes()).hexdigest()=='488ea31dcc685f6b78ab2e7e948ab77019e399ec1cf8e4c5488224f7bcb8ae6f'
   actual=w/'architecture/process.json';report=actual.with_name('main-browser.json')
   subprocess.run([sys.executable,'-Bu',entry,actual],check=True)
   prior=json.loads((entry.parent/'234-development-returned.json').read_bytes())
   assert prior['host_receipt_sha256']==hashlib.sha256(actual.read_bytes()).hexdigest() and prior['host_report_sha256']==hashlib.sha256(report.read_bytes()).hexdigest()
   assert prior['order']==449 and prior['host']==234 and prior['all_children_exited'] and prior['remaining_children']==[] and prior['physical_sha256']==hashlib.sha256(P(prior['physical']).read_bytes()).hexdigest()
  if phase in ('phone','desktop','mouse'):
   number,prior_phase={'phone':(549,'before'),'desktop':(553,'phone'),'mouse':(557,'architecture')}[phase]
   entry=w.parent/'offer-compact-studies.py'
   assert hashlib.sha256(entry.read_bytes()).hexdigest()=='6779d483c32390599de8ab9fbda9dda2332c9a06f548782c307a0ec1eed8cdc6'
   subprocess.run([sys.executable,'-Bu',entry,str(number),w/prior_phase/'process.json'],check=True)
  if phase=='touch':
   helper=P('/tmp/guangxie506/recheck-after-234.py');original=w/'mouse/process.json';reference=w/'mouse/main-browser.json'
   digest=lambda file:hashlib.sha256(file.read_bytes()).hexdigest()
   assert digest(helper)=='6fa4db934d3e8d9bbd37267cc80ad9ec1a3a6dfa87e4ca0d6746ec1d01535b1a'
   subprocess.run([sys.executable,'-Bu',helper,original],check=True)
   back=json.loads((helper.parent/'234-native-returned.json').read_bytes())
   assert back['order']==506 and back['host']==234 and back['phase']=='mouse'
   assert back['host_sha256']==digest(original) and back['host_report_sha256']==digest(reference)
   assert back['all_children_exited'] and back['remaining_children']==[] and back['phases']
   for event in back['phases']:
    assert event['pid']>1 and event['log_sha256'] and isinstance(event['exit_code'],int)
    if event['physical']:assert digest(P(event['physical']))==event['physical_sha256']
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
  rc=proc.returncode;profile=P(os.environ.get('CITY234_MATERIALIZED','/dev/shm/city-234-actual'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes())['completed'] and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
 (w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':7})+'\n')
