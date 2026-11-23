"""Run a selected real huangpu-hengli-bank-henan-tianjin-corner map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/hengli-bank-henan-tianjin-corner-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
def full(n):return json.loads((Path('/dev/shm/restart-'+str(n))/f'31-{n}-production.json').read_bytes())
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='huangpu-hengli-bank-henan-tianjin-corner';bank=Path(os.environ.get('CITY276_MATERIALIZED','/dev/shm/city-276-actual'))
for n in (275,276):
 target=bank/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==276:names.append('assets/models/candidates/'+ident+'/manifest.json')
 for f in names:
  actual=target/f;required=s['files'][f]
  if actual.is_file() and hashlib.sha256(actual.read_bytes()).hexdigest()==required:continue
  actual.parent.mkdir(parents=True,exist_ok=True)
  with urlopen(origin+f,timeout=70) as res:assert res.status==200;raw=res.read()
  assert hashlib.sha256(raw).hexdigest()==required
  blobs=w/'input-blobs';blobs.mkdir(exist_ok=True)
  choices=[Path('/tmp/shanghai-main-275/formal-31275/immutable-bytes')/required,Path('/tmp/shanghai-yongjia-porch/blobs')/required,Path('/tmp/shanghai-riyue-courtyard/blobs')/required,Path('/tmp/shanghai-bridge-walking-221/blobs')/required,Path('/tmp/shanghai-main-199/immutable-checker-bytes')/required,Path('/tmp/henglibankcorner311/projects/shanghai')/f]
  if n==275:choices.insert(0,Path('/tmp/americanorientalcorner310/projects/shanghai')/f)
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
d=w/phase;d=d/'captures'/os.environ['QA_ARCH_PART'] if phase=='architecture' else d;d.mkdir(exist_ok=True,parents=True);tmp=bank/('profile-'+phase);tmp.mkdir(exist_ok=True)
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'276'),QA_CONTROL_CATALOG=str(bank/'275/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['275']['catalog_sha256'],QA_CONTROL_CITY_COUNT='310',MODEL_BASE_URL=bound['275'if before else'276']['origin'],QA_CDP_PORT='19476',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
import fcntl,tempfile,shutil
env.update(QA_ANGLE_BACKEND='gl-egl',QA_X11_SCANNER='/dev/shm/pavilion273/x11-scanlines',LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='1',LP_NATIVE_VECTOR_WIDTH='128',GALLIVM_PERF='no_opt',MALLOC_ARENA_MAX='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
if phase in ('mouse','touch','distant') or (phase=='architecture' and os.environ.get('QA_ARCH_PART')!='street'):
 env.update(QA_ANGLE_BACKEND='swiftshader',MALLOC_TRIM_THRESHOLD_='65536',MALLOC_MMAP_THRESHOLD_='131072',MESA_SHADER_CACHE_DISABLE='true')
scratch=max(map(Path,['/dev/shm','/run/codex-docker/user','/run/lock']),key=lambda p:shutil.disk_usage(p).free)
log=d/'run.log' if phase=='architecture' else w/(phase+'.log')
with log.open('wb')as out,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as seat,tempfile.TemporaryDirectory(dir=scratch,prefix='h276-')as temp:
 fcntl.flock(seat,fcntl.LOCK_EX);env['TMPDIR']=temp
 r=subprocess.run(['node',w/('check-hengli-camera.cjs' if phase=='architecture' else 'check-hengli-distant.cjs' if phase=='distant' else 'check-hengli-remaining.cjs' if phase in ('mouse','touch') else 'check-hengli-live.cjs'),case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
(d/'raw.exit' if phase=='architecture' else w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
