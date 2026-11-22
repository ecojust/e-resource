"""Exercise each viewport on the same signed site, store the reports and real process outcomes."""
import datetime,subprocess,os,time,fcntl,json,hashlib,shutil
from pathlib import Path as P
w=P('/tmp/shanghai-main-229/final-map-31229');
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


d=P(__file__).parent
def h(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not (d/'process.json').exists() and not (d/'control-browser.json').exists()
original=w/'before/process.json';mouse=w/'mouse/process.json';assert json.loads(mouse.read_bytes())['exit_code']==0
begin=now()
proc=subprocess.Popen([__import__('sys').executable,'-Bu',d/'run-before.py','before'],start_new_session=True)
seen={}
while proc.poll() is None:
 seen.update(sample_processes(proc.pid));time.sleep(.35)
nodes={p:v for p,v in seen.items() if v[1] in ('node','nodejs','MainThread')};chromes={p:v for p,v in seen.items() if v[1] in ('chrome','chromium')}
rp=d/'control-browser.json';rem=remaining_processes({**nodes,**chromes});rec=dict(order=229,mode='before-desktop',started=begin,finished=now(),exit_code=proc.returncode,node_pids=sorted(nodes),chromium_pids=sorted(chromes),remaining_children=rem,node_closed=bool(nodes) and not remaining_processes(nodes),all_children_exited=not rem,prior_sha256=h(original),mouse_closed_sha256=h(mouse),driver_sha256=h(d/'before-desktop.cjs'),report_sha256=h(rp) if rp.is_file() else None)
(d/'process.json').write_text(json.dumps(rec,indent=2)+'\n')
assert not rem and nodes and chromes and proc.returncode==0
r=json.loads(rp.read_bytes());assert r['completed'] and r['mode']=='frozen-before' and r['catalog']['count']==265 and r['server']=='http://127.0.0.1:31228/' and r['screenshots'][0]['sha256']==h(d/'map-before.png')
