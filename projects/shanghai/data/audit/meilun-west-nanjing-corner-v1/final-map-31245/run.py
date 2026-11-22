"""Run a selected real huangpu-meilun-west-nanjing-corner map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/meilun-west-nanjing-corner-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in tuple(['before','phone','desktop','street','roof','shops','pediments','mouse','touch','distant','standalone'])
ident='huangpu-meilun-west-nanjing-corner';bank=Path(os.environ.get('CITY245_MATERIALIZED','/dev/shm/city-245-actual'))
for n in (244,245):
 target=bank/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==245:
  folder='assets/models/candidates/'+ident+'/'
  names.append(folder+'manifest.json')
  if phase=='standalone':
   with urlopen(origin+folder+'manifest.json',timeout=30)as reply:
    body=reply.read();assert reply.status==200 and hashlib.sha256(body).hexdigest()==s['files'][folder+'manifest.json']
   manifest=json.loads(body)
   names.extend([manifest['viewer_page'],'src/candidate-asset-viewer.js',*[folder+x['file'] for x in manifest['assets'].values()]])

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
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'245'),QA_CONTROL_CATALOG=str(bank/'244/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['244']['catalog_sha256'],QA_CONTROL_CITY_COUNT='279',MODEL_BASE_URL=bound['244'if before else'245']['origin'],QA_CDP_PORT='19445',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
if phase=='standalone':
 proof=bank/'245/data/audit/meilun-west-nanjing-corner-v1/geometry-native.json'
 permanent=Path('/workspace/.e-resource-recovery/grace/reboot245/meilun-geometry-native.json')
 assert hashlib.sha256(permanent.read_bytes()).hexdigest()=='518f0cd246ac439dbef955690d977c4bb000ef9a99b9128b6fbff6d5121a5afd'
 proof.parent.mkdir(parents=True,exist_ok=True)
 if not proof.exists():proof.symlink_to(permanent)
 assert hashlib.sha256(proof.read_bytes()).digest()==hashlib.sha256(permanent.read_bytes()).digest()
 command=['node',w/'check-standalone.cjs',d]
else:
 settings=json.loads((w/'active-phase-observers.json').read_bytes())
 selected=settings['phases'].get(phase,{'program':'check-map-stages.cjs','sha256':settings['original']})
 observer=w/selected['program']
 assert hashlib.sha256(observer.read_bytes()).hexdigest()==selected['sha256']
 command=['node',observer,case,*flags]
with (w/(phase+'.log')).open('wb')as out:
 r=subprocess.run(command,env=env,stdout=out,stderr=subprocess.STDOUT)
(w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
