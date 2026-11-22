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
  if phase=='touch':
   gate=P('/tmp/union-apartments522/recheck-after-239.py')
   assert hashlib.sha256(gate.read_bytes()).hexdigest()=='99a9a041c957b643ce66dd3852a02720f805a94275111a5617d21b1fae4837dc'
   mouse=w/'mouse/process.json'; source=w/'mouse/main-browser.json'
   subprocess.run([sys.executable,'-Bu',gate,mouse],check=True)
   ticket=json.loads((gate.parent/'239-native-returned.json').read_bytes())
   assert ticket['order']==522 and ticket['host']==239 and ticket['phase']=='mouse'
   assert ticket['host_sha256']==hashlib.sha256(mouse.read_bytes()).hexdigest() and ticket['host_report_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
   assert ticket['all_children_exited'] and ticket['remaining_children']==[] and ticket['phases'] and ticket['phases'][-1]['exit_code']==ticket['exit_code']
   for item in ticket['phases']:
    if item['physical']:assert hashlib.sha256(P(item['physical']).read_bytes()).hexdigest()==item['physical_sha256']
  if phase in ('phone','desktop'):
   prior_phase='before' if phase=='phone' else 'phone'
   subphase='native' if phase=='phone' else 'viewer'
   previous=json.loads((w/prior_phase/'process.json').read_bytes())
   assert previous['exit_code']==0 and previous['node_closed'] and previous['remaining_chromium']==[]
   if subphase=='native':
    def digest(f):
     with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
    supplement=P('/workspace/.e-resource-recovery/browser/reboot238/supplement-303.py')
    assert digest(supplement)=='e60c022352caf6e4f48d042a9f618d0ff191104058be2227656378cd48183cb6'
    source=w/'before/process.json';report=w/'before/control-browser.json';subprocess.run([sys.executable,'-Bu',supplement,source],check=True)
    received=json.loads(P('/tmp/rongzhai303/239-before-formal-viewer-returned.json').read_bytes())
    assert received['host_sha256']==digest(source) and received['host_report_sha256']==digest(report) and received['all_children_exited'] and not received['remaining_children']
    if received['passed']:
     assert received['physical_sha256']==digest(P(received['physical'])) and received['views']==6 and set(received['downloads'])=={'raw','full','lod','native'}
    elif not received['started']:assert received['deferred'] and received['missing']
    else:assert received['attempted'] and received['failed'] and received['pid'] and 'exit_code' in received
   subprocess.run([sys.executable,'-B',w.parent/'offer-304.py',subphase,str(w/prior_phase/'process.json')],check=True)
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
  rc=proc.returncode;profile=P(os.environ.get('CITY239_MATERIALIZED','/dev/shm/city-239-actual'))/('profile-'+phase)
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
