"""Run a selected real huangpu-shanghai-waterworks-484-corner map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/shanghai-waterworks-484-corner-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='huangpu-shanghai-waterworks-484-corner';bank=Path(os.environ.get('CITY264_MATERIALIZED','/dev/shm/city-264-actual'))
for n in (263,264):
 target=bank/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==264:names.append('assets/models/candidates/'+ident+'/manifest.json')
 for f in names:
  actual=target/f;required=s['files'][f]
  if actual.is_file() and hashlib.sha256(actual.read_bytes()).hexdigest()==required:continue
  actual.parent.mkdir(parents=True,exist_ok=True)
  with urlopen(origin+f,timeout=70) as res:assert res.status==200;raw=res.read()
  assert hashlib.sha256(raw).hexdigest()==required
  blobs=w/'input-blobs';blobs.mkdir(exist_ok=True)
  choices=[Path('/tmp/shanghai-main-263/formal-31263/immutable-bytes')/required,Path('/tmp/shanghai-yongjia-porch/blobs')/required,Path('/tmp/shanghai-riyue-courtyard/blobs')/required,Path('/tmp/shanghai-bridge-walking-221/blobs')/required,Path('/tmp/shanghai-main-199/immutable-checker-bytes')/required,Path('/tmp/waterworkscornerlog299/projects/shanghai')/f]
  if n==263:choices.insert(0,Path('/tmp/puguangfront298/projects/shanghai')/f)
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
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'264'),QA_CONTROL_CATALOG=str(bank/'263/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['263']['catalog_sha256'],QA_CONTROL_CITY_COUNT='298',MODEL_BASE_URL=bound['263'if before else'264']['origin'],QA_CDP_PORT='19464',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
with (w/(phase+'.log')).open('wb')as out:
 r=subprocess.run(['node',w/'check-map-stages.cjs',case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
(w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
