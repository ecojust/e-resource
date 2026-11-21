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
  existing=w/phase/'process.json'
  if existing.is_file():
   receipt=json.loads(existing.read_bytes())
   rp=existing.parent/('control-browser.json' if phase=='before' else 'main-browser.json')
   assert receipt['exit_code']==0 and receipt['node_closed'] and receipt['node_pids'] and receipt['chromium_pids']
   assert receipt['remaining_chromium']==receipt['remaining_children']==[] and receipt['report_sha256']==hashlib.sha256(rp.read_bytes()).hexdigest()
   assert json.loads(rp.read_bytes())['completed']
   continue
  if phase=='distant':
   preceding=w/'touch/process.json';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
   guest=P('/tmp/wuyuan314-370/design/after-226-touch.py')
   assert sha(guest)=='9c5013a23b76eabfb6f47dbd965fd0c5242170172d2189f8fde61ab2e6eb781a'
   subprocess.run(['python','-Bu',guest,preceding],check=True)
   place=guest.parents[1];res=json.loads((place/'226-model-and-views-closed.json').read_bytes())
   assert (res['order'],res['host'],res['phase'])==(370,226,'touch')
   assert res['host_sha256']==sha(preceding) and res['host_report_sha256']==sha(preceding.parent/'main-browser.json')
   assert res['attempted'] and res['all_children_exited'] and not res['remaining']
   assert res['phases'] and all(v['pid']>0 and not v['remaining'] and sha(P(v['log']))==v['log_sha256'] for v in res['phases'])
   assert res['passed']==(res['exit_code']==0 and all(v['exit_code']==0 for v in res['phases']))
   if res['passed']:assert len(res['results'])==3 and all(sha(place/'pilot'/f)==v for f,v in res['results'].items())
   after370=P('/tmp/wuyuan314-370/226-model-and-views-closed.json')
   after373=P('/tmp/jiaotong373/after-226-touch.py');assert sha(after373)=='2ddc1c821a8da66ab06566e4ecb474227437aa5eed41d6d294730a1fc2d8f2a4'
   subprocess.run(['python','-Bu',after373,preceding,after370],check=True)
   end373=P('/tmp/jiaotong373/226-model-closed.json');state=json.loads(end373.read_bytes())
   assert (state['order'],state['host'],state['phase'])==(373,226,'touch') and state['all_children_exited']
   assert state['remaining']==state['remaining_children']==[] and state['host_sha256']==sha(preceding) and state['previous_sha256']==sha(after370)
   if state['attempted']:
    assert state['passed']==(state['exit_code']==0) and state['stages'] and all(s['pid']>0 and sha(P(s['log']))==s['log_sha256'] for s in state['stages'])
    if state['passed']:assert all(sha(P(f))==h for f,h in state['evidence'].items())
   else:assert state['deferred'] and state['missing']
  if phase=='mouse':
   preceding=w/'architecture/process.json'
   sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
   guest=P('/tmp/huashan831-371/mapping/after-226-architecture.py')
   assert sha(guest)=='ed00fa1961dca276f593014d8c6da85394e78d830794373da98533eca0646df7'
   subprocess.run(['python','-Bu',guest,preceding],check=True)
   place=guest.parents[1];res=json.loads((place/'226-architecture-model-closed.json').read_bytes())
   assert (res['order'],res['host'],res['phase'])==(371,226,'architecture')
   assert res['host_receipt_sha256']==sha(preceding) and res['host_report_sha256']==sha(preceding.parent/'main-browser.json')
   assert res['remaining']==res['remaining_children']==[] and res['all_children_exited']
   if res['started']:
    assert res['attempted'] and res['pid']>0 and res['pid_birth']>0 and sha(P(res['log']))==res['log_sha256']
    assert res['exit']==res['exit_code'] and res['passed']==(res['exit']==0)
    if res['passed']:assert all(sha(place/'first-model'/name)==v['sha256'] for name,v in res['files'].items())
   else:assert res['deferred'] and not res['attempted'] and res['missing']
   previous371=place/'226-architecture-model-closed.json'
   wall=P('/tmp/anting43-385/after-226-architecture.py')
   assert sha(wall)=='e769286e73de8061424908d4b51940beb2f88c1df4dee8252037a67f9b0ce229'
   subprocess.run(['python','-Bu',wall,preceding,previous371],check=True)
   state=json.loads((wall.parent/'226-wall-check-closed.json').read_bytes())
   assert (state['order'],state['host'],state['phase'])==(385,226,'architecture')
   assert state['host_sha256']==sha(preceding) and state['host_report_sha256']==sha(preceding.parent/'main-browser.json')
   assert state['previous_sha256']==sha(previous371) and state['all_children_exited'] and state['remaining']==[]
  if phase=='touch':
   preceding=w/'mouse/process.json'
   latest=json.loads(preceding.read_bytes())
   assert latest['phase']=='mouse' and latest['exit_code']==0 and latest['remaining_chromium']==latest['remaining_children']==[]
   guest=P('/tmp/soong-dongping365/after-226-mouse.py')
   sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
   assert sha(guest)=='c5d30379ba4e96dd16f7bf041454af20275725233f71a92f42420c98642fc830'
   subprocess.run(['python','-Bu',guest,preceding],check=True)
   returned=guest.parent/'226-pilot-closed.json';res=json.loads(returned.read_bytes())
   assert res['order']==365 and res['host']==226 and res['host_sha256']==sha(preceding) and res['host_report_sha256']==latest['report_sha256']
   assert res['remaining']==[] and res['exit']==res['exit_code'] and res['passed']==(res['exit']==0) and res['stages']
   assert all(step['pid']>0 and step['pid'] in {int(pid)for pid in res['observed_births']} and sha(P(step['log']))==step['log_sha256'] for step in res['stages'])
   assert all(sha(P(f))==v for f,v in res['evidence'].items())
  if phase=='architecture':
   host=w/'desktop/process.json'
   helper=P('/workspace/.e-resource-recovery/grace/donghu350/after-interruption/226-desktop.py')
   sha=lambda p:hashlib.sha256(P(p).read_bytes()).hexdigest()
   assert sha(helper)=='08325ae185ea02e01521c23d0a455f87112dee6aef5da0a4559059c58ab7989f'
   subprocess.run(['python','-Bu',helper,host],check=True)
   root=P('/tmp/donghu-70-350')
   result=json.loads((root/'226-interruption-returned.json').read_bytes())
   assert (result['host'],result['order'],result['host_sha256'],result['host_report_sha256'])==(226,350,sha(host),sha(host.parent/'main-browser.json'))
   assert result['ground_sha256']==sha(root/'226-ground-closed.json') and result['views_sha256']==sha(root/'226-six-views-closed.json')
   for field in ['ground','views']:
    rec=json.loads(P(result[field]).read_bytes())
    assert rec['deferred'] and rec['attempted'] is rec['started'] is False and rec['missing'] and rec['remaining']==[] and rec['all_children_exited']
  if phase in ('phone','desktop'):
   prior_phase='before' if phase=='phone' else 'phone'
   subphase='native' if phase=='phone' else 'viewer'
   previous=json.loads((w/prior_phase/'process.json').read_bytes())
   assert previous['exit_code']==0 and previous['node_closed'] and previous['remaining_chromium']==[]
   book=P('/tmp/chinahotel291');done=book/(subphase+'-closed.json');skip=book/(str(226)+'-'+subphase+'-deferred.json')
   while not done.is_file() and not skip.is_file():time.sleep(2)
   if done.is_file():
    receipt=json.loads(done.read_bytes());assert receipt['order']==291 and receipt['exit']==0 and receipt['passed']
    assert not receipt.get('remaining_blender',[]) and not receipt.get('remaining_chromium',[])
   else:
    receipt=json.loads(skip.read_bytes());assert receipt['deferred'] and not receipt.get('blender_started') and not receipt.get('browser_started')
  if phase=='phone':
   after291=done if done.is_file() else skip
   prev=w/'before/process.json';supplement=P('/tmp/shanghai-main-290/formal-31290/early-signed-page.py')
   sig=lambda f:hashlib.sha256(P(f).read_bytes()).hexdigest()
   assert sig(supplement)=='c285454ba817a975fb20fd79c9fb34ff38f8895d58cbfb64c0d6b9a6e0c29262'
   subprocess.run(['python','-Bu',supplement,'226',prev,after291],check=True)
   note=json.loads(P('/tmp/strand290/226-formal-viewer-returned.json').read_bytes())
   assert note['order']==290 and note['host']==226 and note['all_children_exited'] and note['remaining_children']==[]
   assert note['host_receipt_sha256']==sig(prev) and note['host_report_sha256']==sig(prev.parent/'control-browser.json') and note['previous_sha256']==sig(after291)
   if note.get('started'):assert note['exit_code']==0 or not note['passed']
   else:assert note.get('already_closed') or note.get('deferred')
  if phase=='desktop':
   sha=lambda f:hashlib.sha256(P(f).read_bytes()).hexdigest()
   phone=w/'phone/process.json';after291=done if done.is_file() else skip
   guest=P('/tmp/jianguo598-383/author/after-226.py')
   assert sha(guest)=='8c033ac2081874c8225e01ba8057f0be0b8c987612152faa5009133d4ad47661'
   subprocess.run(['python','-Bu',guest,phone,after291],check=True)
   response=json.loads((guest.parents[1]/'226-model-closed.json').read_bytes())
   assert (response['order'],response['host'],response['phase'])==(383,226,'phone') and response['all_children_exited'] and response['remaining']==[]
   assert response['host_receipt_sha256']==sha(phone) and response['host_report_sha256']==sha(phone.parent/'main-browser.json') and response['previous_sha256']==sha(after291)
   if response['attempted']:
    assert response['pid']>0 and response['started'] and response['passed']==(response['exit_code']==0) and sha(response['log'])==response['log_sha256']
    if response['passed']:assert sha(response['result'])==response['result_sha256']
   else:assert response['deferred'] and response['missing'] and not response['started']
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
  rc=proc.returncode;profile=P(os.environ.get('CITY226_MATERIALIZED','/dev/shm/city-226-actual'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes())['completed'] and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
 entry=P('/tmp/anfu233-367/mapping/after-226-distant-restored.py')
 hostfile=w/'distant'/'process.json'
 parent_report=hostfile.parent/'main-browser.json'
 sha=lambda f:hashlib.sha256(P(f).read_bytes()).hexdigest()
 assert sha(entry)=='36f597ef032c1dc4a6d4806c0e1e111cdd5cd750e4178d8ba85c31778362d82c'
 subprocess.run(['python','-Bu',entry,hostfile],check=True)
 guest=json.loads(P('/tmp/anfu233-367/mapping/226-distant-city-closed.json').read_bytes())
 assert guest['host']==226 and guest['order']==367 and guest['remaining']==[] and guest['finished']
 assert guest['phase']=='distant' and guest['host_receipt_sha256']==sha(hostfile) and guest['host_report_sha256']==sha(parent_report)
 assert guest['all_children_exited'] and guest['remaining_children']==[]
 if guest['attempted']:
  assert guest['started'] and guest['passed']==(guest['exit_code']==0) and guest['exit']==guest['exit_code']
  assert all(stage['pid']>0 and sha(stage['log'])==stage['log_sha256'] for stage in guest['stages'])
  if guest['passed']:assert len(guest['stages'])==3 and sha(guest['evidence'])==guest['evidence_sha256'] and set(guest['summary'])=={'desktop','mobile'}
 else:assert guest['deferred'] and not guest['started'] and guest['missing']
 extra=w/'after-367-development-380.py';assert sha(extra)=='2eb1e710d791fd71e59b2cc3014bfa4b2f401d3640400d6ac9482364f9ec1cd5'
 subprocess.run(['python','-Bu',extra],check=True)
 entry396=P('/tmp/zikawei-396-architecture/development-native/link-226.py')
 assert sha(entry396)=='1928e8d345b18d759b62349134ff6e72220e36187e598a38a02ea54f0afc54e8'
 subprocess.run(['python','-Bu',entry396],check=True)
 (w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':7})+'\n')
