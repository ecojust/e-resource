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
  if phase=='architecture':
   domain=P('/tmp/huashan831-371')
   program=domain/'mapping/after-229-desktop.py'
   file_sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
   assert file_sha(program)=='a2a3cad4729914a61e3586d9de2da7548ef6314c55b29eddda1aca60a383ae43'
   previous=w/'desktop/process.json'
   report=w/'desktop/main-browser.json'
   subprocess.run(['python','-B',program,previous],check=True)
   outcome=json.loads((domain/'229-desktop-model-closed.json').read_bytes())
   assert (outcome['host'],outcome['order'],outcome['phase'])==(229,371,'desktop')
   assert outcome['host_receipt_sha256']==file_sha(previous) and outcome['host_report_sha256']==file_sha(report)
   assert outcome['all_children_exited'] and outcome['remaining_children']==outcome['remaining']==[] and outcome['finished']
   if outcome['attempted']:
    assert outcome['started'] and outcome['pid']>0 and outcome['pid_birth']>0 and outcome['exit_code']==outcome['exit']
    assert outcome['passed']==(outcome['exit_code']==0) and file_sha(P(outcome['log']))==outcome['log_sha256']
    if outcome['passed']:
     assert outcome['files'] and all(file_sha(domain/name)==value for name,value in outcome['files'].items())
   else:
    assert outcome['deferred'] and not outcome['started'] and outcome['missing']
  if phase=='mouse':
   domain=P('/tmp/kaiwen378'); entry=domain/'design/after-229-model.py'
   physical=w/'architecture/process.json'; report=physical.parent/'main-browser.json'
   digest=lambda name:hashlib.sha256(P(name).read_bytes()).hexdigest()
   assert digest(entry)=='3d02e39686b5055094deb05e91253763089274cb2b0ae664d796cc2a2b4fbcd8'
   subprocess.run(['python','-Bu',entry,physical],check=True)
   guest=json.loads((domain/'229-model-closed.json').read_bytes())
   assert (guest['order'],guest['host'],guest['phase'])==(378,229,'architecture')
   assert guest['host_sha256']==digest(physical) and guest['host_report_sha256']==digest(report)
   assert guest['attempted'] and guest['finished'] and guest['all_children_exited'] and guest['remaining']==[]
   assert guest['phases'] and all(s['pid']>0 and s['remaining']==[] and s['log_sha256']==digest(s['log']) for s in guest['phases'])
   assert guest['phases'][-1]['exit_code']==guest['exit_code'] and guest['passed']==(guest['exit_code']==0)
   if guest['passed']:
    assert [s['phase'] for s in guest['phases']]==['model','views','rays'] and len(guest['results'])==3
    assert all(digest(domain/'pilot'/name)==value for name,value in guest['results'].items())
  if phase=='touch':
   entry=P('/tmp/wuyuan251-369/after-229-mouse.py')
   hostfile=w/'mouse'/'process.json'
   parent_report=hostfile.parent/'main-browser.json'
   sha=lambda f:hashlib.sha256(P(f).read_bytes()).hexdigest()
   assert sha(entry)=='5b00bc40311550caf224f20a35e87b7d0744f029bfee43d411420e0ddce39938'
   witness=P('/tmp/wuyuan251-369/229-pilot-closed.json')
   if witness.exists():
    assert sha(witness)=='63b8b67fabe4f24d417018abb1e203d3370a93292ddf94bb0bad76c10b8e2a2b' and sha(P('/workspace/.e-resource-recovery/history/replay229/check-229-desktop-directory-zoom.cjs'))==json.loads(parent_report.read_bytes())['scriptSha256']
   else:subprocess.run(['python','-Bu',entry,hostfile],check=True)
   guest=json.loads(witness.read_bytes())
   assert guest['host']==229 and guest['order']==369 and guest['remaining']==[] and guest['finished']
   assert guest['host_sha256']==sha(hostfile) and guest['host_report_sha256']==sha(parent_report)
   assert guest['exit']==guest['exit_code'] and guest['passed']==(guest['exit_code']==0) and guest['stages']
   assert all(x['pid']>0 and x['log_sha256']==sha(x['log']) for x in guest['stages'])
   if guest['passed']:assert len(guest['stages'])==3 and len(guest['evidence'])==4 and all(sha(f)==digest for f,digest in guest['evidence'].items())
  if phase in ('phone','desktop'):
   prior_phase='before' if phase=='phone' else 'phone'
   subphase='native' if phase=='phone' else 'viewer'
   previous=json.loads((w/prior_phase/'process.json').read_bytes())
   assert previous['exit_code']==0 and previous['node_closed'] and previous['remaining_chromium']==[]
   book=P('/tmp/guangdong306-294');done=book/(subphase+'-closed.json');skip=book/(str(229)+'-'+subphase+'-deferred.json')
   entry=book/'offer-229.py';assert hashlib.sha256(entry.read_bytes()).hexdigest()=='4588e4111dfaeaac83fe0db7556c3859317cff4d014a8678f09c5f8896344d5c'
   assert hashlib.sha256((book/'recovered-controls.json').read_bytes()).hexdigest()=='ecb57f4f5ae4a5374f7e9858cfa7e4b22b33260d0f992045caf9d5247e969de9'
   held=book/'229-viewer-at-first-handoff.json'
   if subphase=='viewer' and held.is_file():
    assert hashlib.sha256(held.read_bytes()).hexdigest()=='c02b360461b41fda559e45cac05b32d440133f57ee77ca80fe71f2929aa0e6bb'
    other=json.loads(skip.read_bytes())
    assert hashlib.sha256(skip.read_bytes()).hexdigest()=='a34662f10dd031d122c1d1672357bb9c5dc382322ed4471c9e0a672e1be57dcb' and other['deferred'] and other['physical_exit']==str(w/prior_phase/'process.json')
    assert json.loads(held.read_bytes())['host_sha256']==hashlib.sha256((w/prior_phase/'process.json').read_bytes()).hexdigest()
    skip=held
   else:subprocess.run(['python','-Bu',entry,subphase,w/prior_phase/'process.json'],check=True)
   while not done.is_file() and not skip.is_file():time.sleep(2)
   if done.is_file():
    receipt=json.loads(done.read_bytes());assert receipt['order']==294 and receipt['exit']==0 and receipt['passed']
    assert not receipt.get('remaining_blender',[]) and not receipt.get('remaining_chromium',[])
   else:
    receipt=json.loads(skip.read_bytes());assert receipt['deferred'] and not receipt.get('blender_started') and not receipt.get('browser_started')
  if phase=='phone':
   entry=P('/tmp/yangtze-hankou292/handoff/offer-late.py')
   assert hashlib.sha256(entry.read_bytes()).hexdigest()=='75ce5056d2af40ee244a053b0e673be5e8a87680ef5c0288a57a4abde6eb8f1c'
   firsthand=w/'before/process.json'; up=done if done.is_file() else skip
   subprocess.run(['python','-Bu',entry,firsthand,up],check=True)
   pe=P('/tmp/yangtze-hankou292/229-viewer-returned.json'); row=json.loads(pe.read_bytes())
   assert row['host']==229 and row['order']==292 and row['remaining_children']==[] and row['all_children_exited']
   assert row['host_sha256']==hashlib.sha256(firsthand.read_bytes()).hexdigest() and row['previous_sha256']==hashlib.sha256(up.read_bytes()).hexdigest()
   dev=P('/tmp/yangtze-hankou292/handoff/development-at-229-verified.py');assert hashlib.sha256(dev.read_bytes()).hexdigest()=='9dd1ee727cf8d9f198247ca831364ed55f9cac518e8dc860613ec61fd4868e9c'
   subprocess.run(['python','-Bu',dev,firsthand,pe],check=True)
   borrowed=json.loads(P('/tmp/yangtze-hankou292/229-development-viewer-returned.json').read_bytes())
   assert borrowed['host_sha256']==hashlib.sha256(firsthand.read_bytes()).hexdigest() and borrowed['previous_sha256']==hashlib.sha256(pe.read_bytes()).hexdigest()
   assert borrowed['all_children_exited'] and borrowed['remaining_children']==[]
   arch_entry=P('/dev/shm/v388r/after-229-before.py');assert hashlib.sha256(arch_entry.read_bytes()).hexdigest()=='f448e55592b1aabf2afbafd019f490f8ec3ff57133b030044a122b4acd79dd3e'
   previous_return=P('/tmp/yangtze-hankou292/229-development-viewer-returned.json')
   subprocess.run(['python','-Bu',arch_entry,firsthand,previous_return],check=True)
   released=json.loads(P('/dev/shm/v388r/229-viewer-returned.json').read_bytes())
   assert released['all_children_exited'] and released['remaining_children']==[] and released['host_receipt_sha256']==hashlib.sha256(firsthand.read_bytes()).hexdigest()
   assert released['previous_sha256']==hashlib.sha256(previous_return.read_bytes()).hexdigest()
   # Both real checks completed after the initial low-storage attempt before phone.
   for closed,digest in [(P('/workspace/.e-resource-recovery/history/replay229/388-ordinary-check/229-viewer-returned.json'),'69cd442187ae87cfb2c5167e0ea996e479e07cc688cab772337741b651406454'),(P('/tmp/yangtze-hankou292/229-after-388-short-path-closed.json'),'234c11978a58f596d788cb58ba868b2673059c421a9d801f80c59f407fd0b0af')]:
    result=json.loads(closed.read_bytes());assert hashlib.sha256(closed.read_bytes()).hexdigest()==digest and result['exit_code']==0 and result['all_children_exited'] and not result['remaining_children']
  if phase=='desktop':
   entry=P('/dev/shm/v293s/293-viewer-small/offer-229.py')
   assert hashlib.sha256(entry.read_bytes()).hexdigest()=='fb1c3d47e2b4ab46c2cc60d65d85a47f8bb35ff41a374c950de327b83b1e455e'
   firsthand=w/'phone/process.json';handed=held if held.is_file() else (done if done.is_file() else skip)
   original_return=P('/dev/shm/v293s/229-viewer-returned.json')
   if original_return.exists():
    old=json.loads(original_return.read_bytes());assert old['passed'] and old['exit_code']==0 and hashlib.sha256(P(old['physical']).read_bytes()).hexdigest()==old['physical_sha256'] and hashlib.sha256(original_return.read_bytes()).hexdigest()=='0f5ea7afe0d27a2c5cde9ca3b5bd0ee54103e54f689a067c62f7b9891f6e9de9'
   else:subprocess.run(['python','-Bu',entry,firsthand,handed],check=True)
   returned=json.loads(P('/dev/shm/v293s/229-viewer-returned.json').read_bytes())
   assert returned['host_sha256']==hashlib.sha256(firsthand.read_bytes()).hexdigest() and returned['previous_sha256']==hashlib.sha256(handed.read_bytes()).hexdigest()
   assert returned['host']==229 and returned['order']==293 and returned['all_children_exited'] and returned['remaining_children']==[]
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
  rc=proc.returncode;profile=P(os.environ.get('CITY229_MATERIALIZED','/dev/shm/city-229-actual'))/('profile-'+phase)
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
