"""Validate a released 234 browser and its guest before rendering one separate photographed study."""
from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import json,sys,fcntl,subprocess,os
root=Path(__file__).parent
targets={549:('shaoxing1-549','before','native'),553:('julu314-553','phone','viewer'),557:('ruijin129-557','architecture',None)}
order=int(sys.argv[1]);folder,phase,guest=targets[order];w=Path('/tmp')/folder/'work'
def dh(f):
 with Path(f).open('rb')as s:return file_digest(s,'sha256').hexdigest()
def read(f):return json.loads(Path(f).read_bytes())
def write(f,q):
 data=(json.dumps(q,indent=2,ensure_ascii=False)+'\n').encode()
 tmp=f.with_suffix('.pending');tmp.write_bytes(data);tmp.replace(f)
host=Path(sys.argv[2]);assert host.samefile(root/'final-map-31234'/phase/'process.json')
h=read(host);r=host.with_name('control-browser.json' if phase=='before' else 'main-browser.json')
assert h['exit_code']==0 and h['node_closed'] and h['node_pids']and h['chromium_pids'] and h['remaining_children']==h['remaining_chromium']==[]
assert dh(r)==h['report_sha256']and read(r)['completed']
close=w.parent/'234-model-returned.json'
saved=w.parent/'234-prior-guest-evidence.json'
if close.is_file():
 rec=read(close)
 assert rec['host_sha256']==dh(host) and rec['host_report_sha256']==dh(r)
 assert saved.is_file() and rec['previous_sha256']==dh(saved) and rec['remaining_children']==[]
 if rec.get('physical'):assert dh(rec['physical'])==rec['physical_sha256']
 sys.exit(0)
if guest:
 true=Path('/tmp/jixian299')/(guest+'-closed.json');later=root/f'299-{guest}-deferred.json'
 if true.is_file():
  previous=true;row=read(true);assert row['passed'] and row['exit']==0 and not row.get('remaining_blender')and not row.get('remaining_chromium')
 else:
  previous=later;row=read(later);assert row['deferred']and row['previous_session_sha256']==dh(host) and not row['blender_started'] and not row['chromium_started']
else:
 previous=Path('/tmp/jiangsu796-449/early-234-development/234-development-returned.json');row=read(previous);assert row['host_receipt_sha256']==dh(host) and row['all_children_exited'] and row['remaining_children']==[]
close=w.parent/'234-model-returned.json';physical=w/'physical.json';program=w/'run.py'
with(w.parent/'234-model.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if close.exists():
  rec=read(close);assert rec['host_sha256']==dh(host)and rec['host_report_sha256']==dh(r)and rec['previous_sha256']==dh(previous) and rec['remaining_children']==[];sys.exit(0)
 original=previous.read_bytes()
 if saved.is_file():assert saved.read_bytes()==original
 else:
  with saved.open('xb') as out:out.write(original)
 assert dh(saved)==dh(previous)
 meta=dict(previous_evidence=str(saved),order=order,host=234,phase=phase,host_receipt=str(host),host_sha256=dh(host),host_report_sha256=dh(r),previous=str(previous),previous_sha256=dh(previous),program_sha256=dh(program))
 stages=[];rc=0
 if not physical.exists():
  commands=[]
  if order==557:
   src=w/'author/source';commands.append(('derive-lettering',[src/'make_lettering.py','/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc','--project','/workspace/e-resource/projects/shanghai']))
  commands.append(('author-study',[program]))
  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MALLOC_ARENA_MAX':'2'}
  for label,cmd in commands:
   log=w.parent/(f'234-{label}.log')
   with log.open('xb')as out:
    t=datetime.now(timezone.utc).isoformat();child=subprocess.Popen(['nice','-n','12',sys.executable,'-Bu',*cmd],stdout=out,stderr=subprocess.STDOUT,env=env);rc=child.wait()
   stages.append(dict(label=label,pid=child.pid,exit_code=rc,started=t,log=str(log),log_sha256=dh(log)))
   if rc:break
 if physical.exists():
  p=read(physical);assert p['id']==read(w/'author/source/package-data.json')['id']and p['remaining']==[]
  for item in p['stages']:assert dh(w/item['log'])==item['log_sha256']and item['remaining']==[]
  for name,art in p['artifacts'].items():assert dh(w/name)==art['sha256']
  rc=p['exit_code']
  if rc==0:assert len(p['artifacts'])==4 and p['passed']
  meta.update(physical=str(physical),physical_sha256=dh(physical),artifacts=p['artifacts'])
 elif not rc:raise ValueError('No physical model return from the invoked study')
 write(close,dict(**meta,real_stages=stages,started=bool(stages),passed=(rc==0),exit_code=rc,all_children_exited=True,remaining_children=[],finished=datetime.now(timezone.utc).isoformat()))
 print(dh(close))
