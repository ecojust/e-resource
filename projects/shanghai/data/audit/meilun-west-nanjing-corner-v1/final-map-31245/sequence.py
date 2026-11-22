"""Exercise each viewport on the same signed site, store the reports and real process outcomes."""
import datetime,subprocess,os,time,fcntl,json,hashlib,shutil
from pathlib import Path as P
from guest_result import verify as verify_guest
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

def verify_previous_city():
 ticket=P('/tmp/shanghai-main-244/244-map-slot-released.json')
 prior=json.loads(ticket.read_bytes())
 assert prior['order']==244 and prior['passed'] and prior['exit_code']==0 and prior['remaining_chromium']==[]
 assert (prior.get('after_real_screenshot_review') or prior.get('all_captures_visually_reviewed') or prior.get('views_reviewed'))
 assert prior['screenshots'] and len(prior['actual_saved_downloads'])==4
 for phase,section in prior['reports'].items():
  report=P(section['report']);closed=P(section.get('exit',section.get('process',section.get('closed',''))))
  assert hashlib.sha256(report.read_bytes()).hexdigest()==section['report_sha256']
  assert hashlib.sha256(closed.read_bytes()).hexdigest()==(section.get('exit_sha256') or section.get('process_sha256') or section['closed_sha256'])
with (w/'runner.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 verify_previous_city()
 for phase in ['before','phone','desktop','street','roof','shops','pediments','mouse','touch','distant','standalone']:
  if phase in ('phone','desktop'):
   prior_phase='before' if phase=='phone' else 'phone'
   subphase='native' if phase=='phone' else 'viewer'
   previous=json.loads((w/prior_phase/'process.json').read_bytes())
   assert previous['exit_code']==0 and previous['node_closed'] and previous['remaining_chromium']==[]
   previous_report=w/prior_phase/('control-browser.json' if prior_phase=='before' else 'main-browser.json')
   r=json.loads(previous_report.read_bytes())
   assert r['completed'] and not r['failed'] and not r['errors'] and r['screenshots']
   assert hashlib.sha256(previous_report.read_bytes()).hexdigest()==previous['report_sha256']
   assert previous['remaining_children']==[] and previous['node_pids'] and previous['chromium_pids']
   evidence=w.parent/'evidence'/prior_phase;evidence.mkdir(parents=True,exist_ok=True)
   report=evidence/'browser.json'
   if not report.exists():os.link(previous_report,report)
   assert hashlib.sha256(report.read_bytes()).hexdigest()==previous['report_sha256']
   for image in r['screenshots']:
    src=previous_report.parent/image['file'];dst=evidence/image['file']
    if not dst.exists():os.link(src,dst)
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==image['sha256']
   receipt={**previous,'order':245,'port':31244 if prior_phase=='before' else 31245,'passed':True,'exit':0,'node_pid':previous['node_pids'][0],'pid':previous['node_pids'][0],'remaining':[],'report':str(report),'screenshots':r['screenshots']}
   closing=evidence/'closed.json';pending=closing.with_suffix('.new')
   pending.write_text(json.dumps(receipt,indent=2)+'\n');os.replace(pending,closing)
   provider=P('/tmp/qinyuan310/mapping/handoff/admit-window.py')
   expected='93daef4c2f1f3bddae4a1e25c823a8ba397656fcb1338b953c9c4a722ccb4a25'
   assert hashlib.sha256(provider.read_bytes()).hexdigest()==expected
   if (provider.parent/'dispatch-contract.json').is_file():
    subprocess.run(['python','-B',w/'admit-seal.py'],check=True)
   book=provider.parents[2];done=book/(subphase+'-closed.json');skip=book/('245-'+subphase+'-deferred.json')
   if not done.is_file() and not skip.is_file():
    highest=P('/tmp/shanghai-yongjia-porch/scenes/310-all-http.json')
    if subphase=='viewer' and not highest.is_file():
     data=dict(order=310,host=245,kind='viewer',stage='viewer',source=str(closing),source_sha256=hashlib.sha256(closing.read_bytes()).hexdigest(),
               previous_report_sha256=previous['report_sha256'],deferred=True,started=False,attempted=False,authorized=False,completed=False,
               reason='Final 31310 catalog pending at the real 245 phone exit',missing=[str(highest)],checked_at=now())
     temp=skip.with_suffix('.pending');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(skip)
    else:
     subprocess.run(['python','-B',provider,subphase,closing],check=True)
   selected=done if done.is_file() else skip
   outcome=verify_guest(subphase,closing,selected)
   record={'kind':subphase,'status':outcome,'source':str(closing),'source_sha256':hashlib.sha256(closing.read_bytes()).hexdigest(),'report_sha256':previous['report_sha256'],'receipt':str(selected),'receipt_sha256':hashlib.sha256(selected.read_bytes()).hexdigest()}
   target=evidence/'guest-310-result.json'
   if target.is_file():
    assert json.loads(target.read_bytes())==record
   else:
    temp=target.with_suffix('.pending');temp.write_text(json.dumps(record,indent=2)+'\n');temp.replace(target)
  if phase in ('mouse','standalone'):
   extra, signature, source, result = {
    'mouse':(P('/workspace/.e-resource-recovery/grace/reboot244/supplement-309.py'),'9fb7ff8485a7d060342d04f065fd03863fdf3d53fc95d7333b4a7611b6e97ed2',w/'pediments/process.json',P('/tmp/jueyuan309/245-pediments-ordinary-returned.json')),
    'standalone':(P('/workspace/.e-resource-recovery/grace/reboot245/supplement-310.py'),'c6a47277a85d1f72443f9ef9e8a87f72a0fc7ae7f35c41c715218708c9804bdc',w/'distant/process.json',P('/tmp/qinyuan310/245-distant-ordinary-returned.json')),
   }[phase]
   assert hashlib.sha256(extra.read_bytes()).hexdigest()==signature
   subprocess.run(['python','-Bu',extra,source],check=True)
   extra_result=json.loads(result.read_bytes())
   assert extra_result['host_sha256']==hashlib.sha256(source.read_bytes()).hexdigest() and extra_result['host_report_sha256']==json.loads(source.read_bytes())['report_sha256']
   assert extra_result['all_children_exited'] and extra_result['remaining_children']==[]
  if phase=='touch':
   source=P('/tmp/suzhou955-546/after-245.py');assert hashlib.sha256(source.read_bytes()).hexdigest()=='c3d9469b468f320c046c4c61c71be763a2c4c8135ec5cf356c9c936a850b76b5'
   previous=w/'mouse/process.json';report=w/'mouse/main-browser.json'
   subprocess.run(['python','-Bu',str(source),str(previous)],check=True)
   returned=json.loads((source.parent/'245-native-returned.json').read_bytes())
   assert returned['order']==546 and returned['host']==245 and returned['phase']=='mouse'
   assert returned['host_sha256']==hashlib.sha256(previous.read_bytes()).hexdigest() and returned['host_report_sha256']==hashlib.sha256(report.read_bytes()).hexdigest()
   assert returned['all_children_exited'] and returned['remaining_children']==[]
   for item in returned['phases']:
    if item['physical']:assert hashlib.sha256(P(item['physical']).read_bytes()).hexdigest()==item['physical_sha256']
  d=w/phase;d.mkdir(exist_ok=True)
  rp=d/('viewer.json' if phase=='standalone' else 'control-browser.json' if phase=='before' else 'main-browser.json')
  rcfile=w/(phase+'.exit');close=d/'process.json'
  if close.is_file():
   row=json.loads(close.read_bytes())
   assert row['exit_code']==0 and row['node_closed'] and row['chromium_pids'] and not row['remaining_children'] and not row['remaining_chromium'] and rp.is_file()
   assert json.loads(rp.read_bytes()).get('completed',json.loads(rp.read_bytes()).get('passed')) and hashlib.sha256(rp.read_bytes()).hexdigest()==row['report_sha256']
   continue
  assert not rp.exists(), 'Archive incomplete evidence before a new run'
  began=now()
  proc=subprocess.Popen(['python','-B',w/'run.py',phase],start_new_session=True)
  observed={}
  while proc.poll() is None:
   observed.update(sample_processes(proc.pid))
   time.sleep(.5)
  rc=proc.returncode;profile=P(os.environ.get('CITY245_MATERIALIZED','/dev/shm/city-245-actual'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes()).get('completed',json.loads(rp.read_bytes()).get('passed')) and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
 (w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':11})+'\n')
