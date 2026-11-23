"""Run the Shanghai Commercial and Savings Bank Roof Pavilion city views with two signed windows for the Park Apartments paired arches."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).absolute().parent;old=Path('/tmp/shanghai-main-272/272-map-slot-released.json');ev=w/'isolated-evidence'
r=lambda f:json.loads(f.read_bytes());h=lambda f:sha256(f.read_bytes()).hexdigest()
def write(p,data):
 if p.exists():return r(p)
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
 return data
def trueclose(p):
 rec=r(p);rc=next((rec[k]for k in ['exit','exit_code','returncode','code']if k in rec),None)
 assert rc==0 and not any(rec.get(k)for k in ['remaining','remaining_chromium','remaining_blender','remaining_oidn','remaining_processes']),p
 return rec
def use(stage):
 target=ev/stage/'closed.json'
 if not target.is_file():
  with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);subprocess.run([sys.executable,'-Bu',str(w/'capture-measured.py'),stage,*([str(old)]if stage=='control'else[])],check=True)
 closed=trueclose(target);assert closed['phase']==stage and closed['cdp_closed'] and closed['observed_chromium_pid_and_starttime']
 assert h(Path(closed['report']))==closed['report_sha256']
 print('closed',stage,closed['finished'],flush=True)
 return target
def external(kind,prior):
 offer=w.parent/'offer-338-recovered.py'
 assert h(offer)=='fecd650977c33cb2668ce6e261c7273b06e89cdbf0b06c2700c6f8b69d22905f'
 subprocess.run([sys.executable,'-Bu',offer,kind,prior],check=True)

with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and (predecessor.get('views_reviewed') or predecessor.get('all_captures_visually_reviewed') or predecessor.get('visually_reviewed'))
 assert predecessor['order']==272 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'));use('mobile-card');external('viewer',use('mobile-pin'))
 for stage in ['desktop-card','desktop-pin','street','roof','timber-screens','glazed-eaves','distant']:
  use(stage)
 subprocess.run([sys.executable,'-Bu',w/'verify-standalone.py'],check=True)
 print('All 273 main-scene sessions have closed. Inspect the ten actual city views together with the independent assets.',flush=True)
