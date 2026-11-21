"""Run a selected real Bearn Apartments map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/bearn-apartments-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='huangpu-bearn-apartments';bank=Path(os.environ.get('BEARN_MATERIALIZED','/dev/shm/qa-bearn195'))
for n in (194,195):
 target=bank/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==195:names.append('assets/models/candidates/'+ident+'/manifest.json')
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
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'195'),QA_CONTROL_CATALOG=str(bank/'194/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['194']['catalog_sha256'],QA_CONTROL_CITY_COUNT='231',MODEL_BASE_URL=bound['194'if before else'195']['origin'],QA_CDP_PORT='19595',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
with (w/(phase+'.log')).open('wb')as out:
 r=subprocess.run(['node',w/'check-map-stages.cjs',case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
(w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
