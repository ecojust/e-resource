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
 phases=['before','phone','desktop','architecture','mouse','touch','distant']
 single=len(sys.argv)>1
 if single:
  assert len(sys.argv)==3 and sys.argv[1]=='--single-map-phase' and sys.argv[2] in phases[2:]
  prior=phases[phases.index(sys.argv[2])-1]
  closed=json.loads((w/prior/'process.json').read_bytes())
  assert closed['exit_code']==0 and not closed['remaining_children'] and closed['node_closed'] and (w/prior/'real-frames.json').is_file()
  assert (w.parent/'329-native-result.json').is_file() and (w/'phone/process.json').is_file()
  phases=[sys.argv[2]]
 for phase in phases:
  if not single and phase in ('phone','desktop'):
   prior_phase='before' if phase=='phone' else 'phone'
   subphase='native' if phase=='phone' else 'viewer'
   previous=json.loads((w/prior_phase/'process.json').read_bytes())
   assert previous['exit_code']==0 and previous['node_closed'] and previous['remaining_chromium']==[]
   subprocess.run([sys.executable,'-B',w.parent/'offer-329-recovered.py',subphase,str(w/prior_phase/'process.json')],check=True)
  d=w/phase;d.mkdir(exist_ok=True)
  closed_before=d/'process.json'
  if closed_before.is_file() and json.loads(closed_before.read_bytes()).get('exit_code')!=0:
   failed=json.loads(closed_before.read_bytes())
   assert failed['remaining_children']==[] and not failed['remaining_chromium'],failed
   key=phase+'-'+str(time.time_ns())
   keep=w/'failed-attempts'/key;keep.mkdir(parents=True)
   for src in list(d.iterdir())+[w/(phase+'.log'),w/(phase+'.exit')]:
    if src.exists() or src.is_symlink():
     dest=keep/src.name
     try:os.rename(src,dest)
     except OSError:
      if src.is_symlink():dest.symlink_to(os.path.abspath(os.path.join(src.parent,os.readlink(src))))
      elif src.is_dir():shutil.copytree(src,dest)
      else:shutil.copy2(src,dest)
      assert src.is_dir() or hashlib.sha256(src.read_bytes()).digest()==hashlib.sha256(dest.read_bytes()).digest()
      if src.is_symlink():src.unlink()
      elif src.is_dir():shutil.rmtree(src)
      else:src.unlink()
   inventory={p.relative_to(keep).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in keep.rglob('*') if p.is_file()}
   assert inventory['process.json'] and ('actual-driver.cjs' in inventory or not failed.get('node_pids'))
   (keep/'retained-checksums.json').write_text(json.dumps(inventory,indent=2)+'\n')
  rp=d/('control-browser.json' if phase=='before' else 'main-browser.json')
  rcfile=w/(phase+'.exit');close=d/'process.json'
  if close.is_file():
   row=json.loads(close.read_bytes())
   assert row['exit_code']==0 and not row['remaining_chromium'] and rp.is_file() and row['report_sha256']==hashlib.sha256(rp.read_bytes()).hexdigest() and row['source_code_sha256']==hashlib.sha256((d/'actual-driver.cjs').read_bytes()).hexdigest()
   subprocess.run([sys.executable,'-B',w/'verify-map-frames.py',rp,d/'real-frames.json'],check=True)
   continue
  assert not rp.exists(), 'Archive incomplete evidence before a new run'
  began=now()
  proc=subprocess.Popen(['python','-B',w/'run-waterworks-measured.py',phase],start_new_session=True)
  observed={}
  while proc.poll() is None:
   observed.update(sample_processes(proc.pid))
   time.sleep(.5)
  rc=proc.returncode;profile=P(os.environ.get('CITY264_MATERIALIZED','/tmp/w264'))/('profile-'+phase)
  for i in range(15):
   if not alive(profile):break
   time.sleep(1)
  nodes={pid:state for pid,state in observed.items() if state[1] in ('node','nodejs','MainThread')}
  chromes={pid:state for pid,state in observed.items() if state[1] in ('chromium','chrome')}
  live_nodes=remaining_processes(nodes);live_chromes=remaining_processes(chromes)
  row=dict(order=264,report=str(rp),phase=phase,exit_code=rc,node_pids=sorted(nodes),chromium_pids=sorted(chromes),node_closed=bool(nodes) and not live_nodes,remaining_children=sorted(live_nodes+live_chromes),started=began,finished=now(),remaining_chromium=alive(profile),report_sha256=hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None)
  if (d/'actual-driver.cjs').is_file():
   row['actual_source']=str(d/'actual-driver.cjs')
   row['source_code_sha256']=hashlib.sha256((d/'actual-driver.cjs').read_bytes()).hexdigest()
  port_record=d/'actual-debug-port.json'
  if port_record.is_file():row['debug_port']=json.loads(port_record.read_bytes())['port']
  close.write_text(json.dumps(row,indent=2)+'\n')
  assert rc==0 and rcfile.read_text().strip()=='0' and json.loads(rp.read_bytes())['completed'] and row['node_closed'] and chromes and not row['remaining_children'] and not row['remaining_chromium'],row
  subprocess.run([sys.executable,'-B',w/'verify-map-frames.py',rp,d/'real-frames.json'],check=True)
 if not single:(w/'all-real-processes-closed.json').write_text(json.dumps({'closed_time':now(),'phases':7})+'\n')
