"""Run a selected real huangpu-qiuxin-shipyard-office-south-veranda map phase with signatures from the live origin."""
from pathlib import Path
import fcntl,json,sys,hashlib,os,subprocess,datetime,tempfile
from urllib.request import urlopen
w=Path('/tmp/shanghai-main-261/final-map-31261');project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/qiuxin-shipyard-office-south-veranda-v1/map-case.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];probe=phase=='check-local';assert probe or phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='huangpu-qiuxin-shipyard-office-south-veranda';bank=Path(os.environ.get('CITY261_MATERIALIZED','/dev/shm/city-261-actual'))
if phase=='architecture':
 import time
 ticket=w.parent/'326-viewer-returned.json'
 while not ticket.is_file():time.sleep(1)
 result=json.loads(ticket.read_bytes())
 returned=Path(result['actual_receipt'])
 assert result['passed'] and returned.samefile('/tmp/ho-tung326/viewer-closed.json')
 with returned.open('rb') as actual:assert hashlib.file_digest(actual,'sha256').hexdigest()==result['sha256']
 assert json.loads(returned.read_bytes())['remaining_chromium']==[]
bank.mkdir(parents=True,exist_ok=True)
stage=tempfile.TemporaryDirectory(prefix='bindings-',dir=bank)
scratch=Path(stage.name)
descriptors={}
for n in (260,261):
 target=scratch/str(n);s=full(n);origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==261:names.append('assets/models/candidates/'+ident+'/manifest.json')
 for f in names:
  actual=target/f;required=s['files'][f]
  actual.parent.mkdir(parents=True,exist_ok=True)
  if required not in descriptors:
   with urlopen(origin+f,timeout=90) as res:
    assert res.status==200
    raw=res.read()
   assert hashlib.sha256(raw).hexdigest()==required,f
   fd=os.memfd_create(f.rsplit('/',1)[-1],os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
   with os.fdopen(fd,'wb',closefd=False) as out:out.write(raw)
   # Linux fcntl.h provides these operations when the local Python build omits them.
   seals=0x1|0x2|0x4|0x8
   fcntl.fcntl(fd,getattr(fcntl,'F_ADD_SEALS',1033),seals)
   assert fcntl.fcntl(fd,getattr(fcntl,'F_GET_SEALS',1034))&seals==seals
   descriptors[required]=fd
  actual.symlink_to('/proc/'+str(os.getpid())+'/fd/'+str(descriptors[required]))
  assert hashlib.sha256(actual.read_bytes()).hexdigest()==required
 info='source/precise/'+ident+'/footprint-review.json'
 pointer=target/info;pointer.parent.mkdir(parents=True,exist_ok=True)
 if not pointer.exists():pointer.symlink_to(project/info)
if probe:
 t=subprocess.run(['node','-e',"const f=require('node:fs');process.stdout.write(f.readFileSync(process.argv[1]))",str(scratch/'261/data/candidate-city-integrations.json')],stdout=subprocess.PIPE,check=True)
 assert hashlib.sha256(t.stdout).hexdigest()==bound['261']['catalog_sha256']
 print('Bound real Node read, '+str(len(descriptors))+' distinct sealed responses')
 sys.exit(0)
before=phase=='before'
d=Path(__file__).parent/'survey';d.mkdir(exist_ok=True);tmp=bank/'profile-supplement';tmp.mkdir(exist_ok=True)
env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(scratch/'261'),QA_CONTROL_CATALOG=str(scratch/'260/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['260']['catalog_sha256'],QA_CONTROL_CITY_COUNT='295',MODEL_BASE_URL=bound['260'if before else'261']['origin'],QA_CDP_PORT='19461',QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
driver=Path(__file__).parent/'detail-survey.cjs';actual=d/'actual-driver.cjs'
if actual.exists():assert actual.read_bytes()==driver.read_bytes()
else:actual.write_bytes(driver.read_bytes())
with (d/'run.log').open('wb')as out:
 r=subprocess.run(['node','--preserve-symlinks-main',actual,case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
(d/'exit-code').write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
