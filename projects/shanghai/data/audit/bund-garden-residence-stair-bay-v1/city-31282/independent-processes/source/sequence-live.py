"""Run the Bund garden residence staggered stair windows city views with two signed windows for the Shaoxing Road No.9 entrance."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-281/281-map-slot-released.json');ev=w/'isolated-evidence'
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
   fcntl.flock(lock,fcntl.LOCK_EX);subprocess.run([sys.executable,'-Bu',str(w/'capture-live.py'),stage,*([str(old)]if stage=='control'else[])],check=True)
 closed=trueclose(target);assert closed['phase']==stage and closed['cdp_closed'] and closed['observed_chromium_pid_and_starttime']
 assert h(Path(closed['report']))==closed['report_sha256']
 print('closed',stage,closed['finished'],flush=True)
 return target
def external(kind,prior):
 env=dict(os.environ)
 if kind=='viewer':env['NODE_OPTIONS']='--require='+str(w/'keep-saved.cjs')
 result=Path('/tmp/shaoxing9-347')/(kind+'-closed.json')
 ticket=w.parent/f'347-{kind}-returned.json'
 if ticket.is_file() and result.is_file():
  import runpy
  handed=r(ticket);assert handed['passed'] and handed['host_closed_sha256']==h(prior) and handed['sha256']==h(result)
  assert runpy.run_path(str(w.parent/'guest_result.py'))['verify'](kind,prior,result)=='complete'
 else:
  subprocess.run([sys.executable,'-B',w.parent/'offer-347-live.py',kind,str(prior)],check=True,env=env)
 if kind=='viewer' and result.is_file():
  done=r(result);report=Path(done['report']);assert h(report)==done['report_sha256'] and done['host_receipt_sha256']==h(prior)
  guest=Path('/tmp/shaoxing9-347')
  candidates=[report.parent,*guest.joinpath('handoff').glob('viewer-attempt-*')]
  attempts=[q for q in candidates if (q/'saved').is_dir() and (q/'viewer.json').is_file() and h(q/'viewer.json')==h(report)]
  assert attempts,report
  for item in r(report)['downloads'].values():
   f=attempts[0]/'saved'/item['file'];assert f.stat().st_size==item['bytes'] and h(f)==item['sha256']
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and (predecessor.get('views_reviewed') or predecessor.get('all_captures_visually_reviewed') or predecessor.get('visually_reviewed'))
 assert predecessor['order']==281 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'));use('mobile-card');phone=use('mobile-pin')
 # The same signed phone offer has already been handed to the independent viewer.
 window=Path('/tmp/shaoxing9-347/handoff/viewer-window.json')
 accepted=r(window);assert accepted['sha256']==h(phone)

 for stage in ['desktop-card','desktop-pin','street','roof','lower-stair-windows','upper-stair-windows','distant']:
  use(stage)
 guest=Path('/tmp/shaoxing9-347')
 while not (guest/'viewer-closed.json').is_file() or not (w.parent/'347-viewer-returned.json').is_file():time.sleep(3)
 external('viewer',phone)
 for k in ('native','viewer'):assert trueclose(guest/(k+'-closed.json'))['passed']
 subprocess.run([sys.executable,'-Bu',w/'ordinary-live.py'],check=True)
 print('All 282 main-scene sessions have closed. Inspect the ten actual city views together with the independent assets.',flush=True)
