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
  if phase=='touch':
   guest=P('/tmp/chekiang-bank518/recheck-after-237.py')
   assert hashlib.sha256(guest.read_bytes()).hexdigest()=='e60731179bae7a59162b229b1d0ef39b4602ff6f04ce15bfadf3b800827d2903'
   receipt=w/'mouse/process.json';report=w/'mouse/main-browser.json'
   subprocess.run(['python','-Bu',guest,receipt],check=True)
   returned=json.loads((guest.parent/'237-native-returned.json').read_bytes())
   assert (returned['order'],returned['host'],returned['phase'])==(518,237,'mouse')
   assert returned['host_sha256']==hashlib.sha256(receipt.read_bytes()).hexdigest()
   assert returned['host_report_sha256']==hashlib.sha256(report.read_bytes()).hexdigest()
   assert returned['all_children_exited'] and returned['remaining_children']==[] and returned['phases']
   assert returned['passed'] and returned['already_completed'] and not returned['attempted']
   assert returned['previous_completed_exit']==0 and returned['exit_code'] is None
   assert set(returned['four_assets'])=={'raw','full','lod','native'}
   for stage in returned['phases']:
    assert stage['exit_code']==0 and hashlib.sha256(P(stage['physical']).read_bytes()).hexdigest()==stage['physical_sha256']
  if phase in ('phone','desktop'):
   prior_phase='before' if phase=='phone' else 'phone'
   subphase='native' if phase=='phone' else 'viewer'
   previous=json.loads((w/prior_phase/'process.json').read_bytes())
   assert previous['exit_code']==0 and previous['node_closed'] and previous['remaining_chromium']==[]
   prior_report=w/prior_phase/('control-browser.json' if prior_phase=='before' else 'main-browser.json')
   assert previous['remaining_children']==[] and previous['chromium_pids'] and previous['node_pids']
   assert json.loads(prior_report.read_bytes())['completed'] and hashlib.sha256(prior_report.read_bytes()).hexdigest()==previous['report_sha256']
   if subphase=='native':
    sha=lambda p:hashlib.sha256(P(p).read_bytes()).hexdigest()
    formal=P('/tmp/qianguild301/offer-real-31301.py');programs=P('/tmp/shanghai-main-236/301-formal-programs.json')
    assert sha(formal)=='7133eb022df07fb0fd7b332c012bb9a02b2e448e4188996697248b7cac7bf8f6' and sha(programs)=='1b12a2af37df23253217f771cc668c8352857af15b0aa5b4d3451c1ca7b944f3'
    subprocess.run(['python','-Bu',formal,w/prior_phase/'process.json'],check=True)
    ret=json.loads((formal.parent/'237-formal-viewer-returned.json').read_bytes())
    assert ret['host_sha256']==sha(w/prior_phase/'process.json') and ret['host_report_sha256']==sha(prior_report) and ret['remaining_chromium']==[]
    if ret.get('started'):assert ret['process']>0 and ret['closure_sha256']==sha(ret['closure'])
    if ret.get('passed'):assert ret['receipt_sha256']==sha(formal.parent/'formal-independent-closed.json')
    elif not ret.get('started'):assert ret['deferred'] and ret['missing']
   provider=P('/tmp/shanghai-fourth-302/mapping/handoff/admit-window.py')
   subprocess.run(['python','-B',provider,subphase,w/prior_phase/'process.json'],check=True)
   book=P('/tmp/shanghai-fourth-302');done=book/(subphase+'-closed.json');skip=book/(str(237)+'-'+subphase+'-deferred.json')
   while not done.is_file() and not skip.is_file():time.sleep(2)
   if done.is_file():
    receipt=json.loads(done.read_bytes());assert receipt['order']==302 and receipt['exit']==0 and receipt['passed']
    assert receipt['remaining']==[] and not receipt.get('remaining_blender',[]) and not receipt.get('remaining_chromium',[])
   else:
    receipt=json.loads(skip.read_bytes());assert receipt['order']==302 and receipt['deferred'] and not receipt.get('blender_started') and not receipt.get('browser_started')
  d=w/phase;d.mkdir(exist_ok=True)
  rp=d/('control-browser.json' if phase=='before' else 'main-browser.json')
  rcfile=w/(phase+'.exit');close=d/'process.json'
  if close.is_file():
   row=json.loads(close.read_bytes())
   assert row['exit_code']==0 and row['node_closed'] and row['chromium_pids'] and not row['remaining_children'] and not row['remaining_chromium'] and rp.is_file()
   assert json.loads(rp.read_bytes())['completed'] and hashlib.sha256(rp.read_bytes()).hexdigest()==row['report_sha256']
   continue
  assert not rp.exists(), 'Archive incomplete evidence before a new run'
  began=now()
  proc=subprocess.Popen(['python','-B',w/'run.py',phase],start_new_session=True)
  observed={}
  while proc.poll() is None:
   observed.update(sample_processes(proc.pid))
   time.sleep(.5)
  rc=proc.returncode;profile=P(os.environ.get('CITY237_MATERIALIZED','/dev/shm/city-237-actual'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes())['completed'] and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
 hook=P('/tmp/hongkou-412-study/development-native/link-237.py')
 sha=lambda f:hashlib.sha256(P(f).read_bytes()).hexdigest()
 assert sha(hook)=='caf5e8b4528ba36fa1c4e89815ef9cf6a6e9fc8f65ecac9945604a18532effa9'
 subprocess.run(['python','-Bu',hook,w/'distant/process.json',w/'distant/main-browser.json'],check=True)
 result=json.loads((hook.parent/'237-development-returned.json').read_bytes())
 assert result['order']==412 and result['host']==237 and result['host_sha256']==sha(w/'distant/process.json') and result['host_report_sha256']==sha(w/'distant/main-browser.json')
 assert result['all_children_exited'] and not result['remaining_children'] and result['physical_sha256']==sha(result['physical'])
 standalone=P('/workspace/.e-resource-recovery/browser/237-ordinary/after-412.py')
 assert sha(standalone)=='7c7b2a6d657c2d1a4a5b881337fd2ee01efce06aa8b3a225c023badac8ffe116'
 subprocess.run(['python','-Bu',standalone,w/'distant/process.json',hook.parent/'237-development-returned.json'],check=True)
 final=read_actual=json.loads((w/'actual-standalone/closed.json').read_bytes())
 assert final['exit_code']==0 and final['node_closed'] and not final['remaining_chromium'] and len(final['views'])==6 and set(final['downloads'])=={'raw','full','lod','native'}
 (w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':7})+'\n')
