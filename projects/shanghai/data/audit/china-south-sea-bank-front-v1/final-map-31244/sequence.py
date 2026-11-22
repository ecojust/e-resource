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

def verify_previous_city():
 ticket=P('/tmp/shanghai-main-243/243-map-slot-released.json')
 prior=json.loads(ticket.read_bytes())
 assert prior['order']==243 and prior['passed'] and prior['exit_code']==0 and prior['remaining_chromium']==[]
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
   if not report.exists():os.link(previous_report,report)
   assert hashlib.sha256(report.read_bytes()).hexdigest()==previous['report_sha256']
   for image in r['screenshots']:
    src=previous_report.parent/image['file'];dst=evidence/image['file']
    if not dst.exists():os.link(src,dst)
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==image['sha256']
   receipt={**previous,'order':244,'port':31243 if prior_phase=='before' else 31244,'passed':True,'exit':0,'node_pid':previous['node_pids'][0],'pid':previous['node_pids'][0],'remaining':[],'report':str(report),'screenshots':r['screenshots']}
   closing=evidence/'closed.json';pending=closing.with_suffix('.new')
   pending.write_text(json.dumps(receipt,indent=2)+'\n');os.replace(pending,closing)
   provider=P('/tmp/jueyuan309/mapping/handoff/admit-window.py')
   if provider.exists():
    binding=json.loads((w.parent/'guest-309.json').read_bytes())
    assert hashlib.sha256(provider.read_bytes()).hexdigest()==binding['admit_sha256']
    assert hashlib.sha256(P(binding['dispatch']).read_bytes()).hexdigest()==binding['dispatch_sha256']
    book=P('/tmp/jueyuan309'); highest=P('/tmp/shanghai-yongjia-porch/scenes/309-all-http.json')
    if subphase=='viewer' and not (book/'viewer-closed.json').is_file() and not highest.is_file():
     deferred=book/'244-viewer-deferred.json'
     if not deferred.exists():
      data=dict(order=309,host=244,kind='viewer',deferred=True,started=False,blender_started=False,browser_started=False,
                previous_receipt=str(closing),previous_sha256=hashlib.sha256(closing.read_bytes()).hexdigest(),report_sha256=previous['report_sha256'],missing=[str(highest)],checked=now())
      temporary=deferred.with_suffix('.pending');temporary.write_text(json.dumps(data,indent=2)+'\n');temporary.replace(deferred)
    elif (book/(subphase+'-closed.json')).is_file():
     done=json.loads((book/(subphase+'-closed.json')).read_bytes())
     assert done['passed'] and done['exit']==0 and done['wrapper_closed'] and done['order']==309
     assert done['admitted_from']==hashlib.sha256(closing.read_bytes()).hexdigest() and not done['remaining']
     if subphase=='native':
      assert done['blender_pids'] and not done['remaining_blender'] and not done['remaining_oidn']
      manifest=P(done['manifest']);assert hashlib.sha256(manifest.read_bytes()).hexdigest()==done['manifest_sha256']
      for role,item in json.loads(manifest.read_bytes())['assets'].items():
       artifact=manifest.parent/item['file']
       assert item['bytes']==artifact.stat().st_size and item['sha256']==done['assets'][role]['sha256']==hashlib.sha256(artifact.read_bytes()).hexdigest()
     else:
      assert done['chromium_pids'] and not done['remaining_chromium']
    else:
     subprocess.run(['python','-B',provider,subphase,closing],check=True)
   else:
    pending=P('/tmp/jueyuan309')/('244-'+subphase+'-deferred.json')
    pending.parent.mkdir(exist_ok=True);pending.write_text(json.dumps({'order':309,'deferred':True,'started':False,'reason':'admission program absent at real closure','source':str(closing),'source_sha256':hashlib.sha256(closing.read_bytes()).hexdigest()},indent=2)+'\n')
   book=P('/tmp/jueyuan309');done=book/(subphase+'-closed.json');skip=book/(str(244)+'-'+subphase+'-deferred.json')
   while not done.is_file() and not skip.is_file():time.sleep(2)
   if done.is_file():
    receipt=json.loads(done.read_bytes());assert receipt['order']==309 and receipt['exit']==0 and receipt['passed']
    assert not receipt.get('remaining_blender',[]) and not receipt.get('remaining_chromium',[])
   else:
    receipt=json.loads(skip.read_bytes());assert receipt['deferred'] and not receipt.get('started') and not receipt.get('blender_started') and not receipt.get('browser_started')
  if phase=='touch':
   callback=P('/tmp/taichang542/after-244.py')
   fingerprint=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
   assert fingerprint(callback)=='5fee2c7a7736363fb24f38bfdd602d872a193b0f3410fc140fc0bc102de2bbc7'
   event=w/'mouse/process.json';report=event.with_name('main-browser.json')
   subprocess.run(['python','-Bu',callback,event],check=True)
   result=json.loads((callback.parent/'244-native-returned.json').read_bytes())
   assert result['order']==542 and result['host']==244 and result['phase']=='mouse'
   assert result['host_sha256']==fingerprint(event) and result['host_report_sha256']==fingerprint(report)
   assert result['all_children_exited'] and result['remaining_children']==[]
   if result.get('already_completed'):
    assert result['attempted'] is False and result['exit_code'] is None and result['previous_completed_exit']==0
    assert fingerprint(P(result['earlier']))==result['earlier_sha256']
   for item in result['phases']:
    assert item['pid']>1 and isinstance(item['exit_code'],int) and item['log_sha256']
    if item['physical']:assert fingerprint(P(item['physical']))==item['physical_sha256']
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
  rc=proc.returncode;profile=P(os.environ.get('CITY244_MATERIALIZED','/dev/shm/city-244-actual'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes())['completed'] and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
 supplement=P('/workspace/.e-resource-recovery/grace/reboot244/supplement-309.py')
 assert hashlib.sha256(supplement.read_bytes()).hexdigest()=='9fb7ff8485a7d060342d04f065fd03863fdf3d53fc95d7333b4a7611b6e97ed2'
 subprocess.run(['python','-Bu',supplement,w/'distant/process.json'],check=True)
 supplement_report=json.loads(P('/tmp/jueyuan309/244-distant-ordinary-returned.json').read_bytes())
 assert supplement_report['host_sha256']==hashlib.sha256((w/'distant/process.json').read_bytes()).hexdigest()
 assert supplement_report['all_children_exited'] and supplement_report['remaining_children']==[]
 provider=P('/workspace/.e-resource-recovery/browser/244-ordinary/after-distant.py')
 assert hashlib.sha256(provider.read_bytes()).hexdigest()=='d3ecac772a4f5ac2521ffc1356e1c1f9e35db7e6ed4d35e95d8ba408c884c704'
 subprocess.run(['python','-Bu',provider,w/'distant/process.json','/tmp/taichang542/244-native-returned.json'],check=True)
 page=json.loads((w.parent/'actual-standalone/closed.json').read_bytes())
 assert page['passed'] and page['node_closed'] and page['exit_code']==0 and not page['remaining_children'] and not page['remaining_chromium']
 (w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':7})+'\n')
