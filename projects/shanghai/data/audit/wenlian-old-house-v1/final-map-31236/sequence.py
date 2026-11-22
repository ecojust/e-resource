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
   gate=P('/tmp/yarn-bank514/recheck-after-236.py')
   assert hashlib.sha256(gate.read_bytes()).hexdigest()=='f6134b275ee2f2743930855e56aad360e3fa60c3e0dc07a8cca27f641070b90d'
   mouse=w/'mouse/process.json'; source=w/'mouse/main-browser.json'
   subprocess.run([sys.executable,'-Bu',gate,mouse],check=True)
   ticket=json.loads((gate.parent/'236-native-returned.json').read_bytes())
   assert ticket['order']==514 and ticket['host']==236 and ticket['phase']=='mouse'
   assert ticket['host_sha256']==hashlib.sha256(mouse.read_bytes()).hexdigest() and ticket['host_report_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
   assert ticket['all_children_exited'] and ticket['remaining_children']==[] and ticket['phases'] 
   if ticket.get('already_completed'):
    assert ticket['attempted'] is False and ticket['exit_code'] is None and ticket['previous_completed_exit']==ticket['phases'][-1]['exit_code']==0 and len(ticket['four_assets'])==4
    assert hashlib.sha256(P(ticket['earlier']).read_bytes()).hexdigest()==ticket['earlier_sha256']
   else:
    assert ticket['phases'][-1]['exit_code']==ticket['exit_code']
   for item in ticket['phases']:
    if item['physical']:assert hashlib.sha256(P(item['physical']).read_bytes()).hexdigest()==item['physical_sha256']
  if phase in ('phone','desktop'):
   prior_phase='before' if phase=='phone' else 'phone'
   subphase='native' if phase=='phone' else 'viewer'
   previous=json.loads((w/prior_phase/'process.json').read_bytes())
   assert previous['exit_code']==0 and previous['node_closed'] and previous['remaining_chromium']==[]
   subprocess.run([sys.executable,'-B',w.parent/'offer-301.py',subphase,str(w/prior_phase/'process.json')],check=True)
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
  rc=proc.returncode;profile=P(os.environ.get('CITY236_MATERIALIZED','/dev/shm/city-236-actual'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes())['completed'] and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
 # Offer the official standalone page after the last real map process exits.
 evidence=json.loads((w.parent/'301-formal-programs.json').read_bytes())
 assert all(hashlib.sha256(P(path).read_bytes()).hexdigest()==digest for path,digest in evidence.items())
 source=w/'distant/process.json'
 subprocess.run([sys.executable,'-Bu','/tmp/qianguild301/offer-real-31301.py',source],check=True)
 guest=json.loads(P('/tmp/qianguild301/236-formal-viewer-returned.json').read_bytes())
 assert guest['host_sha256']==hashlib.sha256(source.read_bytes()).hexdigest() and not guest['remaining_chromium']
 assert guest.get('passed') or guest.get('deferred') or (guest.get('started') and guest.get('exit_code')!=0)
 helper=P('/tmp/soong-dongping365/development-native/after-236.py')
 assert hashlib.sha256(helper.read_bytes()).hexdigest()=='a83221432834ec9604c62b8482cd59fcfa5b7616d0c81c66108acb9329c4a5dd'
 previous=P('/tmp/qianguild301/236-formal-viewer-returned.json')
 subprocess.run([sys.executable,'-Bu',helper,source,previous],check=True)
 returned=json.loads((helper.parent/'236-development-returned.json').read_bytes())
 assert returned['order']==365 and returned['host']==236 and returned['phase']=='distant'
 assert returned['host_sha256']==hashlib.sha256(source.read_bytes()).hexdigest() and returned['host_report_sha256']==json.loads(source.read_bytes())['report_sha256']
 assert returned['previous_sha256']==hashlib.sha256(previous.read_bytes()).hexdigest() and returned['physical_sha256']==hashlib.sha256(P(returned['physical']).read_bytes()).hexdigest()
 assert returned['all_children_exited'] and not returned['remaining_children'] and isinstance(returned['exit_code'],int)
 (w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':7})+'\n')
