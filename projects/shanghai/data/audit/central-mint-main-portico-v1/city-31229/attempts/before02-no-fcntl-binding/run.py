"""Run a selected real putuo-central-mint-main-portico map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime,fcntl
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/central-mint-main-portico-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='putuo-central-mint-main-portico';bank=Path(os.environ.get('CITY229_MATERIALIZED','/dev/shm/city-229-actual'))
for n in (228,229):
 target=bank/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==229:names.append('assets/models/candidates/'+ident+'/manifest.json')
 for f in names:
  actual=target/f;required=s['files'][f]
  if actual.is_file() and hashlib.sha256(actual.read_bytes()).hexdigest()==required:continue
  actual.parent.mkdir(parents=True,exist_ok=True)
  # Bind a detached, immutable file. The working project may advance during the next phase.
  with urlopen(origin+f,timeout=70) as res:assert res.status==200;raw=res.read()
  assert hashlib.sha256(raw).hexdigest()==required
  part=actual.with_name(actual.name+'.checked')
  # A sealed in-memory file stays readable by this viewport's browser checker.
  fd=os.memfd_create('signed-229-'+Path(f).name,os.MFD_ALLOW_SEALING)
  with os.fdopen(os.dup(fd),'wb') as materialized:
   materialized.write(raw)
  fcntl.fcntl(fd,fcntl.F_ADD_SEALS,fcntl.F_SEAL_SHRINK|fcntl.F_SEAL_GROW|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_SEAL)
  part.symlink_to('/proc/'+str(os.getpid())+'/fd/'+str(fd))
  os.replace(part,actual)
 info='source/precise/'+ident+'/footprint-review.json'
 pointer=target/info;pointer.parent.mkdir(parents=True,exist_ok=True)
 if not pointer.exists():pointer.symlink_to(project/info)
before=phase=='before'
d=w/phase;d.mkdir(exist_ok=True);tmp=bank/('profile-'+phase);tmp.mkdir(exist_ok=True)
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'229'),QA_CONTROL_CATALOG=str(bank/'228/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['228']['catalog_sha256'],QA_CONTROL_CITY_COUNT='265',MODEL_BASE_URL=bound['228'if before else'229']['origin'],QA_CDP_PORT='19429',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/tmp/country-tools/node_modules:/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
with (w/(phase+'.log')).open('wb')as out:
 r=subprocess.run(['node',w/'check-map-stages.cjs',case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
(w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
