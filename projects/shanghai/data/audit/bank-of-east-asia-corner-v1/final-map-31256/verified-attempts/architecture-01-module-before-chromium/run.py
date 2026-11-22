"""Run a selected real huangpu-bank-of-east-asia-corner map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/bank-of-east-asia-corner-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='huangpu-bank-of-east-asia-corner';bank=Path(os.environ.get('CITY256_MATERIALIZED','/dev/shm/city-256-actual'))
for n in (255,256):
 target=bank/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==256:names.append('assets/models/candidates/'+ident+'/manifest.json')
 for f in names:
  actual=target/f;required=s['files'][f]
  if not actual.is_symlink() and actual.is_file() and hashlib.sha256(actual.read_bytes()).hexdigest()==required:continue
  actual.parent.mkdir(parents=True,exist_ok=True)
  # Bind a detached, immutable file. The working project may advance during the next phase.
  with urlopen(origin+f,timeout=70) as res:assert res.status==200;raw=res.read()
  assert hashlib.sha256(raw).hexdigest()==required
  part=actual.with_name(actual.name+'.checked')
  part.write_bytes(raw)
  os.replace(part,actual)
 info='source/precise/'+ident+'/footprint-review.json'
 pointer=target/info;pointer.parent.mkdir(parents=True,exist_ok=True)
 if not pointer.exists():pointer.symlink_to(project/info)
before=phase=='before'
d=w/phase;d.mkdir(exist_ok=True);tmp=bank/('profile-'+phase);tmp.mkdir(exist_ok=True)
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'256'),QA_CONTROL_CATALOG=str(bank/'255/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['255']['catalog_sha256'],QA_CONTROL_CITY_COUNT='290',MODEL_BASE_URL=bound['255'if before else'256']['origin'],QA_CDP_PORT='19456',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
with (w/(phase+'.log')).open('wb')as out:
 checker='check-256-architecture.cjs' if phase=='architecture' else 'directory-views.cjs' if phase in ('desktop','phone') else 'check-physical.cjs' if phase in ('mouse','touch') else 'check-map-stages.cjs'
 actual_driver=d/'actual-driver.cjs'
 expected=(w/checker).read_bytes()
 if actual_driver.exists():assert actual_driver.read_bytes()==expected
 else:actual_driver.write_bytes(expected)
 r=subprocess.run(['node',w/checker,case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
(w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
