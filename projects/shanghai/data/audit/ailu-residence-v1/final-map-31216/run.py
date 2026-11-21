"""Run a selected real xuhui-ailu-residence-garden-loggia map phase with signatures from the live origin."""
from pathlib import Path
import json,sys,hashlib,os,subprocess,datetime
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/ailu-residence-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];assert phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='xuhui-ailu-residence-garden-loggia';bank=Path(os.environ.get('CITY216_MATERIALIZED','/dev/shm/city-216-actual'))
for n in (215,216):
 target=bank/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==216:names.append('assets/models/candidates/'+ident+'/manifest.json')
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
if phase=='touch':
 guest=w.parent/'retry-vector-before-touch.py';assert hashlib.sha256(guest.read_bytes()).hexdigest()=='48a0d43a7d5b3c5b17d80d5edd637a0bc88e51a1bbc696468cffb4477b4af3fb'
 subprocess.run([sys.executable,'-Bu',guest],check=True)
if phase=='distant':
 event=w.parent/'development-344-after-pointers.py';assert hashlib.sha256(event.read_bytes()).hexdigest()=='2ab0e0718e252bbf7f8b4c85c51139d6cda933bc618175d0244ee9652d4c0355'
 returned=w/'development-344-returned.json'
 if not returned.is_file():subprocess.run([sys.executable,'-Bu',event],check=True)
 rec=json.loads(returned.read_bytes());assert rec['all_children_exited'] and not rec['remaining_children'] and hashlib.sha256(Path(rec['source']).read_bytes()).hexdigest()==rec['sha256']
 guest=w.parent/'348-after-development-344.py';assert hashlib.sha256(guest.read_bytes()).hexdigest()=='3554aae9e6b59ea16fa0670d21026a47d8199c3329ef80d9ab44c2c84585f34e'
 subprocess.run([sys.executable,'-B',guest],check=True)
before=phase=='before'
d=w/phase;d.mkdir(exist_ok=True);tmp=bank/('profile-'+phase);tmp.mkdir(exist_ok=True)
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'216'),QA_CONTROL_CATALOG=str(bank/'215/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['215']['catalog_sha256'],QA_CONTROL_CITY_COUNT='252',MODEL_BASE_URL=bound['215'if before else'216']['origin'],QA_CDP_PORT='19416',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
with (w/(phase+'.log')).open('wb')as out:
 argv=[sys.executable,'-Bu',w/'architecture-cold-sessions.py',case] if phase=='architecture' else ['node',w/('check-distant-scene.cjs' if phase=='distant' else 'check-pointer-visible.cjs' if phase in ('mouse','touch') else 'check-map-stages.cjs'),case,*flags]
 r=subprocess.run(argv,env=env,stdout=out,stderr=subprocess.STDOUT)
(w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
