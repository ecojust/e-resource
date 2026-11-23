"""Run a selected real huangpu-ta-ching-bank-southwest-tower map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/ta-ching-bank-southwest-tower-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
def full(n):return json.loads((Path('/dev/shm/restart-'+str(n))/f'31-{n}-production.json').read_bytes())
bound=json.loads((w/'bound-live.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='huangpu-ta-ching-bank-southwest-tower';bank=Path(os.environ.get('CITY280_MATERIALIZED','/dev/shm/taching280-live/bank'))
for n in (279,280):
 target=bank/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==280:names.append('assets/models/candidates/'+ident+'/manifest.json')
 for f in names:
  actual=target/f;required=s['files'][f]
  if actual.is_file() and not actual.is_symlink() and hashlib.sha256(actual.read_bytes()).hexdigest()==required:continue
  actual.parent.mkdir(parents=True,exist_ok=True)
  with urlopen(origin+f,timeout=70) as res:assert res.status==200;raw=res.read()
  assert hashlib.sha256(raw).hexdigest()==required
  blobs=w/'input-blobs';blobs.mkdir(exist_ok=True)
  choices=[Path('/tmp/shanghai-main-279/formal-31279/immutable-bytes')/required,Path('/tmp/shanghai-yongjia-porch/blobs')/required,Path('/tmp/shanghai-riyue-courtyard/blobs')/required,Path('/tmp/shanghai-bridge-walking-221/blobs')/required,Path('/tmp/shanghai-main-199/immutable-checker-bytes')/required,Path('/tmp/tachingbanktower315/projects/shanghai')/f]
  if n==279:choices.insert(0,Path('/tmp/arnholdcorner314/projects/shanghai')/f)
  for candidate in choices:
   if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest()==required:
    src=candidate.resolve();break
  else:
   src=blobs/required
   if not src.exists():src.write_bytes(raw)
  assert hashlib.sha256(src.read_bytes()).hexdigest()==required
  part=actual.with_name(actual.name+'.checked')
  if part.is_symlink():part.unlink()
  part.write_bytes(raw)
  os.replace(part,actual)
 info='source/precise/'+ident+'/footprint-review.json'
 pointer=target/info;pointer.parent.mkdir(parents=True,exist_ok=True)
 if pointer.is_symlink():pointer.unlink()
 if not pointer.exists():pointer.write_bytes((project/info).read_bytes())
before=phase=='before'
sub='architecture/captures/'+os.environ['QA_ARCH_PART'] if phase=='architecture' else phase
d=w/sub;d.mkdir(parents=True,exist_ok=True);tmp=bank/('profile-'+phase);tmp.mkdir(exist_ok=True)
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'280'),QA_CONTROL_CATALOG=str(bank/'279/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['279']['catalog_sha256'],QA_CONTROL_CITY_COUNT='314',MODEL_BASE_URL=bound['279'if before else'280']['origin'],QA_CDP_PORT='19480',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
import tempfile,fcntl,shutil
driver=w/('check-tower-camera.cjs' if phase=='architecture' else 'check-tower-pointer-distance.cjs' if phase in ('mouse','touch','distant') else 'check-taching-live.cjs')
shutil.copyfile(driver,d/'actual-driver.cjs')
env.update(QA_X11_SCANNER='/dev/shm/pavilion273/x11-scanlines',QA_ANGLE_BACKEND='swiftshader',MALLOC_ARENA_MAX='1',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
with (d/'run.log').open('wb')as out, Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lock, tempfile.TemporaryDirectory(dir='/dev/shm/taching280-live/graphics',prefix='p280-') as scratch:
 fcntl.flock(lock,fcntl.LOCK_EX); env['TMPDIR']=scratch
 scratch_local='/tmp/g80/profiles/'+Path(scratch).name
 env.update(TMPDIR=scratch_local, XDG_CONFIG_HOME=scratch_local+'/cfg',XDG_CACHE_HOME=scratch_local+'/cache',CHROME_CONFIG_HOME=scratch_local+'/cfg')
 env.update(QA_OUTPUT_DIR='/tmp/g80/evidence/'+sub,SHANGHAI_PROJECT_ROOT='/tmp/g80/bank/280',QA_CONTROL_CATALOG='/tmp/g80/bank/279/data/candidate-city-integrations.json')
 pid=str(json.loads((w.parent/'graphics-tools/keeper.json').read_bytes())['pid'])
 if phase in ('mouse','touch'):
  r=subprocess.run([sys.executable,'-Bu',w/'pointer-sessions.py',pid,driver,case,phase],env=env,stdout=out,stderr=subprocess.STDOUT)
 else:r=subprocess.run(['nsenter','--preserve-credentials','--user','--mount','--target',pid,'--','node',driver,case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
 for artifact in (Path('/dev/shm/taching280-live/evidence')/sub).iterdir():
  dest=d/artifact.name
  if artifact.name.endswith('.json'):shutil.copyfile(artifact,dest)
  elif not dest.exists():dest.symlink_to(artifact)
(d/'raw.exit' if phase=='architecture' else w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
