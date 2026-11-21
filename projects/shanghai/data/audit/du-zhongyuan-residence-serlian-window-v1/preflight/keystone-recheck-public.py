from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import json,os,time,sys,subprocess,psutil
here=Path(__file__).resolve().parent;w=here.parent;e=w/'packaged'
read=lambda f:json.loads(f.read_bytes())
def sha(p):
    with p.open('rb')as f:return file_digest(f,'sha256').hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
old=w/'packed-exit.json';r=read(old);assert r['all_children_exited']and not r['remaining_children']and r['exit_code']==1
assert [(v['step'],v['exit_code'])for v in r['events']]==[('generate',0),('rays',1),('views',0),('stone-uv',0)]
before=read(e/'geometry-rays.json')
assert all(len(v['cases'])==80 and all(c['name'].startswith('keystone main front') for c in v['cases']if not c['passed']) for v in before.values())
original=here/'physical.json'
if original.is_file():raise SystemExit(read(original)['exit_code'])
started=now();children={}
with (here/'verified-run.log').open('wb')as log:
    proc=subprocess.Popen([sys.executable,'-B',here/'rays.py'],env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','TMPDIR':'/dev/shm'},stdout=log,stderr=subprocess.STDOUT)
    host=psutil.Process(proc.pid)
    while proc.poll()is None:
        try:
            for c in host.children(recursive=True):children[c.pid]=c.create_time()
        except psutil.Error:pass
        time.sleep(.03)
assert proc.returncode==0;live=[]
for pid,born in children.items():
    try:
        p=psutil.Process(pid)
        if p.create_time()==born and p.status()!=psutil.STATUS_ZOMBIE:live.append(pid)
    except psutil.Error:pass
assert not live
last=read(here/'geometry-rays.json');assert all(row['passed']and len(row['cases'])==83 for row in last.values())
assert all(sha(e/path)==digest for path,digest in r['results'].items())
program=Path(os.environ['SHANGHAI_VERIFY_EXPORT'])
res=dict(order=356,passed=True,exit_code=0,all_children_exited=True,remaining_children=live,started=started,ended=now(),pid=proc.pid,observed_children=children,
         accepted_manifest_sha256=sha(e/'manifest.json'),first_geometry_exit_sha256=sha(old),first_results=r['results'],revised_rays_sha256=sha(here/'geometry-rays.json'),program_sha256=sha(program),log_sha256=sha(here/'verified-run.log'),
         reason='The mid-height sample crosses the new carved horizontal roll 0.268 m in front of the wall. The revised physical test checks that material at the measured projection as well as a separately visible patch of the supporting keystone block.')
original.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(sha(original))
