"""Run a selected real huangpu-shanghai-waterworks-484-corner map phase with signatures from the live origin."""
from pathlib import Path
import gzip,socket,fcntl,json,sys,hashlib,os,subprocess,datetime,tempfile
from urllib.request import urlopen
w=Path(__file__).parent;project=Path('/workspace/e-resource/projects/shanghai');case=project/'data/audit/shanghai-waterworks-484-corner-v1/map-case.json'
bound=json.loads((w/'bound-inputs.json').read_bytes())
phase=sys.argv[1];probe=phase=='check-local';assert probe or phase in ('before','phone','desktop','architecture','mouse','touch','distant')
ident='huangpu-shanghai-waterworks-484-corner';bank=Path(os.environ.get('CITY264_MATERIALIZED','/tmp/w264'))
bank.mkdir(parents=True,exist_ok=True)
stage=tempfile.TemporaryDirectory(prefix='bindings-',dir=bank)
scratch=Path(stage.name)
descriptors={}
for n in (263,264):
 target=scratch/str(n)
 candidates={263:[Path('/tmp/shanghai-main-263/263-production.json')],264:[Path('/tmp/shanghai-main-265/formal-31265/264-production.json.gz')]}
 original=next(c for c in candidates[n] if c.is_file())
 packed=original.read_bytes();payload=gzip.decompress(packed) if original.suffix=='.gz' else packed
 s=json.loads(payload)
 assert hashlib.sha256(payload).hexdigest()==bound[str(n)]['signature_sha256']
 origin=bound[str(n)]['origin']
 names=['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','data/precise-buildings-v6.json','index.html','landmarks.html']
 if n==264:names.append('assets/models/candidates/'+ident+'/manifest.json')
 for f in names:
  actual=target/f;required=s['files'][f]
  actual.parent.mkdir(parents=True,exist_ok=True)
  if required not in descriptors:
   fd=os.memfd_create(f.rsplit('/',1)[-1],os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
   checksum=hashlib.sha256()
   with urlopen(origin+f,timeout=90) as res, os.fdopen(fd,'wb',closefd=False) as out:
    assert res.status==200
    while chunk:=res.read(131072):
     checksum.update(chunk)
     out.write(chunk)
   assert checksum.hexdigest()==required,f
   # Linux fcntl.h provides these operations when the local Python build omits them.
   seals=0x1|0x2|0x4|0x8
   fcntl.fcntl(fd,getattr(fcntl,'F_ADD_SEALS',1033),seals)
   assert fcntl.fcntl(fd,getattr(fcntl,'F_GET_SEALS',1034))&seals==seals
   descriptors[required]=fd
  actual.symlink_to('/proc/'+str(os.getpid())+'/fd/'+str(descriptors[required]))
  with actual.open('rb') as data:assert hashlib.file_digest(data,'sha256').hexdigest()==required
 info='source/precise/'+ident+'/footprint-review.json'
 pointer=target/info;pointer.parent.mkdir(parents=True,exist_ok=True)
 if not pointer.exists():pointer.symlink_to(project/info)
if probe:
 node_check="const fs=require('node:fs'),h=require('node:crypto').createHash('sha256'),s=fs.createReadStream(process.argv[1]);s.on('data',part=>h.update(part));s.on('end',()=>process.stdout.write(h.digest('hex')));s.on('error',e=>{throw e})"
 t=subprocess.run(['node','-e',node_check,str(scratch/'264/data/candidate-city-integrations.json')],capture_output=True,check=True)
 assert t.stdout.decode()==bound['264']['catalog_sha256']
 print(json.dumps(dict(order=264,origins={n:bound[n]['origin'] for n in ('263','264')},catalogs={n:bound[n]['catalog_sha256'] for n in ('263','264')},node_sha256=t.stdout.decode(),distinct_sealed_responses=len(descriptors),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),ran_browser=False)))
 sys.exit(0)
before=phase=='before'
d=w/phase;d.mkdir(exist_ok=True);tmp=bank/('profile-'+phase);tmp.mkdir(exist_ok=True)
with socket.socket() as free:
 free.bind(('127.0.0.1',0));port=free.getsockname()[1]
env=dict(os.environ,QA_ANGLE_BACKEND='gl-egl',LIBGL_ALWAYS_SOFTWARE='1',GALLIVM_PERF='no_opt',LP_NATIVE_VECTOR_WIDTH='128',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MALLOC_ARENA_MAX='1',QA_X11_SCANNER='/workspace/shanghai-publisher-preservation/city-264/x11-scanlines',QA_EVIDENCE_VOLUME=str(bank),SHANGHAI_PROJECT_ROOT=str(scratch/'264'),QA_CONTROL_CATALOG=str(scratch/'263/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=bound['263']['catalog_sha256'],QA_CONTROL_CITY_COUNT='298',MODEL_BASE_URL=bound['263'if before else'264']['origin'],QA_CDP_PORT=str(port),QA_OUTPUT_DIR=str(d),TMPDIR=str(tmp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
flags=['before','--control'] if before else [phase]
driver=w/'check-waterworks-measured.cjs';actual=d/'actual-driver.cjs'
if actual.exists():assert actual.read_bytes()==driver.read_bytes()
else:actual.write_bytes(driver.read_bytes())
(d/'actual-debug-port.json').write_text(json.dumps({'port':port,'actual_driver_sha256':hashlib.sha256(actual.read_bytes()).hexdigest()})+'\n')
with (w/(phase+'.log')).open('wb')as out:
 r=subprocess.run(['node',actual,case,*flags],env=env,stdout=out,stderr=subprocess.STDOUT)
(w/(phase+'.exit')).write_text(str(r.returncode)+'\n');raise SystemExit(r.returncode)
