"""Exercise each viewport on the same signed site, store the reports and real process outcomes."""
import datetime,subprocess,os,time,fcntl,json,hashlib,shutil,errno
from pathlib import Path as P
w=P(__file__).parent;
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def retain_file(source,dest):
 try:
  os.link(source,dest)
 except OSError as exc:
  if exc.errno!=errno.EXDEV:raise
  shutil.copyfile(source,dest)
 assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(dest.read_bytes()).digest()

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
 ticket=P('/tmp/shanghai-main-255/255-map-slot-released.json')
 prior=json.loads(ticket.read_bytes())
 assert prior['order']==255 and prior['passed'] and prior['exit_code']==0 and prior['remaining_chromium']==[]
 assert prior['after_real_screenshot_review'] and prior['views_reviewed'] and prior['reports']==prior['receipts']
 assert prior['screenshots'] and len(prior['actual_saved_downloads'])==4
 for phase,section in prior['reports'].items():
  report=P(section['report']);closed=P(section.get('exit',section.get('process',section.get('closed',''))))
  assert hashlib.sha256(report.read_bytes()).hexdigest()==section['report_sha256']
  assert hashlib.sha256(closed.read_bytes()).hexdigest()==(section.get('exit_sha256') or section.get('process_sha256') or section['closed_sha256'])
with (w/'runner.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 verify_previous_city()
 for phase in ['before','phone','desktop','architecture','mouse','touch','distant']:
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
   if not report.exists():retain_file(previous_report,report)
   assert hashlib.sha256(report.read_bytes()).hexdigest()==previous['report_sha256']
   for image in r['screenshots']:
    src=previous_report.parent/image['file'];dst=evidence/image['file']
    if not dst.exists():retain_file(src,dst)
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==image['sha256']
   receipt={**previous,'order':256,'phase':prior_phase,'port':31255 if prior_phase=='before' else 31256,'passed':True,'exit':0,'node_pid':previous['node_pids'][0],'pid':previous['node_pids'][0],'remaining':[],'report':str(report),'screenshots':r['screenshots']}
   closing=evidence/'closed.json';pending=closing.with_suffix('.new')
   pending.write_text(json.dumps(receipt,indent=2)+'\n');os.replace(pending,closing)
   provider=P('/tmp/liu-changle321/handoff/admit-recovered.py')
   guest=P('/tmp/liu-changle321');handoff=guest/'handoff';dispatch=handoff/'dispatch-recovered.json'
   skip=handoff/(subphase+'-deferred.json');done=guest/(subphase+'-closed.json')
   if provider.is_file() and dispatch.is_file():
    verified={'provider':str(provider),'admit_sha256':hashlib.sha256(provider.read_bytes()).hexdigest(),'dispatch':str(dispatch),'dispatch_sha256':hashlib.sha256(dispatch.read_bytes()).hexdigest(),'host_sha256':hashlib.sha256(closing.read_bytes()).hexdigest()}
    expected=json.loads((w.parent/'guest-321-recovered.json').read_bytes())['authorized_sha256']
    assert verified['admit_sha256']==expected['admit'] and verified['dispatch_sha256']==expected['dispatch']
    (evidence/'guest-programs.json').write_text(json.dumps(verified,indent=2)+'\n')
    if not done.is_file():
     if subphase=='viewer':
      while not (guest/'raw-321-confirmed.json').is_file() or not P('/tmp/shanghai-yongjia-porch/scenes/321-all-http.json').is_file():time.sleep(2)
     subprocess.run(['python','-B',provider,subphase,closing],check=True)
   else:
    missing=[str(p) for p in (provider,dispatch)if not p.is_file()]
    handoff.mkdir(parents=True,exist_ok=True)
    temp=skip.with_suffix('.new')
    temp.write_text(json.dumps(dict(order=321,deferred=True,started=False,blender_started=False,chromium_started=False,attempted=False,missing=missing,host_receipt_sha256=hashlib.sha256(closing.read_bytes()).hexdigest(),host_report_sha256=previous['report_sha256'],source=str(closing),source_sha256=hashlib.sha256(closing.read_bytes()).hexdigest()),indent=2)+'\n');os.replace(temp,skip)
   while not done.is_file() and not skip.is_file():time.sleep(2)
   answer=done if done.is_file() else skip
   r=json.loads(answer.read_bytes())
   assert r['host_receipt_sha256']==hashlib.sha256(closing.read_bytes()).hexdigest() and r['host_report_sha256']==previous['report_sha256']
   if done.is_file():
    assert r['order']==321 and r['passed'] and r.get('exit',r.get('exit_code'))==0
    assert not r.get('remaining',[]) and not r.get('remaining_blender',[]) and not r.get('remaining_chromium',[])
   else:
    r=json.loads(skip.read_bytes());assert r['deferred'] and r['order']==321
    if r.get('attempted'):
     assert r['started'] and r['exit']!=0 and r['remaining']==[] and not r.get('remaining_chromium',[]) and not r.get('remaining_blender',[])
    elif r.get('actual_prior_attempt'):
     assert r['all_processes_closed'] and r['remaining']==[] and r['physical_exit']['wrapper_closed'] and r['physical_exit']['remaining']==[]
    else:assert not any(r.get(k,False)for k in ('started','blender_started','browser_started','chromium_started'))
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
  rc=proc.returncode;profile=P(os.environ.get('CITY256_MATERIALIZED','/dev/shm/city-256-actual'))/('profile-'+phase)
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
