from hashlib import file_digest
from pathlib import Path
import fcntl,time,sys,json,datetime,os,subprocess,psutil
h=Path('/tmp/shanghai-main-261');s=Path(__file__).parent;f=h/'final-map-31261'
def sha(p):
 with p.open('rb') as stream:return file_digest(stream,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
assert read(f/'all-real-processes-closed.json')['phases']==7
with (s/'one-window.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 predecessor=Path('/tmp/yangpu-register437/development-native/261-development-returned.json')
 while not predecessor.is_file():time.sleep(1)
 r=read(predecessor);assert r['all_children_exited'] and not r['remaining_children'] and (r.get('deferred') or r.get('passed') and r.get('exit_code')==0)
 target=s/'survey';target.mkdir(exist_ok=True)
 out=target/'closed.json'
 assert not out.exists() and not (target/'main-browser.json').exists()
 began=now()
 proc=subprocess.Popen([sys.executable,'-Bu',s/'run-survey.py','architecture'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 p=psutil.Process(proc.pid);children={}
 while proc.poll() is None:
  try:
   for c in p.children(recursive=True):
    n=c.name();cmd=c.cmdline()
    if cmd and (n in ['node','nodejs','MainThread','chromium','chrome'] or 'chromium'in cmd[0]):children[c.pid]=(c.create_time(),n,cmd[:2])
  except psutil.Error:pass
  time.sleep(.12)
 log=proc.stdout.read()
 if log:(target/'wrapper.log').write_bytes(log)
 remaining=[]
 for i,(birth,name,cmd) in children.items():
  try:
   cc=psutil.Process(i)
   if cc.create_time()==birth and cc.status()!=psutil.STATUS_ZOMBIE:remaining.append(i)
  except psutil.Error:pass
 report=target/'main-browser.json'
 try:j=read(report) if report.is_file() else {}
 except (ValueError,OSError) as exc:
  j={};(target/'report-read-error.txt').write_text(str(exc)+'\n')
 code=proc.returncode
 nodes=[p for p,v in children.items() if v[1] in ['node','nodejs','MainThread']]
 chrome=[p for p,v in children.items() if v[1] in ['chromium','chrome']]
 row=dict(phase='two-veranda-details',host=261,started=began,finished=now(),exit_code=code,pid=proc.pid,node_pids=nodes,chromium_pids=chrome,observed=children,remaining_children=remaining,remaining_chromium=[p for p in remaining if p in chrome],driver_sha256=sha(s/'detail-survey.cjs'),launcher_sha256=sha(s/'run-survey.py'),observer_sha256=sha(Path(__file__)),predecessor_sha256=sha(predecessor),report_sha256=sha(report) if report.exists() else None,passed=not code and not remaining and bool(nodes and chrome and j.get('completed')))
 out.write_text(json.dumps(row,indent=2)+'\n')
 if not row['passed']:sys.exit(code or 1)
 subprocess.run([sys.executable,'-B',f/'verify-map-frames.py',report,target/'verified-frames.json'],check=True)
 assert len(j['detailSurvey'])==1 and len(j['screenshots'])==1 and len(j['ground'])==54
 print(sha(out),flush=True)
