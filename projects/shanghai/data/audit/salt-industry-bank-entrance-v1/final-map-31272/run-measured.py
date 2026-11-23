"""Run a selected real huangpu-salt-industry-bank-entrance map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=w/'map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
def signed(n):
 f=Path('/tmp/shanghai-yongjia-porch/scenes')/(str(n)+'-production.json')
 return json.loads(f.read_bytes()) if f.is_file() else full(n)
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='huangpu-salt-industry-bank-entrance';bank=Path(os.environ.get('CITY272_MATERIALIZED','/dev/shm/272-city-live/materialized'))
for n in (271,272):
 target=bank/str(n);s=signed(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==272:names.append('assets/models/candidates/'+ident+'/manifest.json')
 for f in names:
  actual=target/f;required=s['files'][f]
  if actual.is_file() and hashlib.sha256(actual.read_bytes()).hexdigest()==required:continue
  actual.parent.mkdir(parents=True,exist_ok=True)
  with urlopen(origin+f,timeout=70) as res:assert res.status==200;raw=res.read()
  assert hashlib.sha256(raw).hexdigest()==required
  blobs=w/'input-blobs';blobs.mkdir(exist_ok=True)
  choices=[Path('/tmp/shanghai-main-271/formal-31271/immutable-bytes')/required,Path('/tmp/shanghai-yongjia-porch/blobs')/required,Path('/tmp/shanghai-riyue-courtyard/blobs')/required,Path('/tmp/shanghai-bridge-walking-221/blobs')/required,Path('/tmp/shanghai-main-199/immutable-checker-bytes')/required,Path('/tmp/saltindustryportico307/projects/shanghai')/f]
  if n==271:choices.insert(0,Path('/tmp/hengfengentrance302/projects/shanghai')/f)
  for candidate in choices:
   if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest()==required:
    src=candidate.resolve();break
  else:
   src=blobs/required
   if not src.exists():src.write_bytes(raw)
  assert hashlib.sha256(src.read_bytes()).hexdigest()==required
  part=actual.with_name(actual.name+'.checked')
  if part.is_symlink():part.unlink()
  part.symlink_to(src)
  os.replace(part,actual)
 info='source/precise/'+ident+'/footprint-review.json'
 pointer=target/info;pointer.parent.mkdir(parents=True,exist_ok=True)
 if not pointer.exists():pointer.symlink_to(project/info)
before=phase=='before'
d=w/phase;d.mkdir(exist_ok=True);tmp=bank/('profile-'+phase);tmp.mkdir(exist_ok=True)
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'272'),QA_CONTROL_CATALOG=str(bank/'271/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['271']['catalog_sha256'],QA_CONTROL_CITY_COUNT='306',MODEL_BASE_URL=bound['271'if before else'272']['origin'],QA_CDP_PORT='19468',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
from socket import socket
with socket() as unused:
 unused.bind(('127.0.0.1',0));port=unused.getsockname()[1]
env.update(QA_CDP_PORT=str(port),QA_ANGLE_BACKEND='gl-egl',LIBGL_ALWAYS_SOFTWARE='1',GALLIVM_PERF='no_opt',LP_NATIVE_VECTOR_WIDTH='128',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MALLOC_ARENA_MAX='1',QA_X11_SCANNER=str(w/'x11-scanlines'),QA_EVIDENCE_VOLUME='/dev/shm/272-city-live')
actual=d/'actual-driver.cjs';actual.write_bytes((w/'check-salt-measured.cjs').read_bytes())
(d/'debug-port').write_text(str(port)+'\n')
import fcntl
with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lock,(w/(phase+'.log')).open('wb')as out:
 fcntl.flock(lock,fcntl.LOCK_EX)
 r=subprocess.run(['node',actual,case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
(w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
