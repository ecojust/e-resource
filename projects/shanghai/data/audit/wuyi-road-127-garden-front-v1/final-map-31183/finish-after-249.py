"""Resume the two public-map devices after the closed 249 native interval and the transient 502."""
from datetime import datetime,timezone
from hashlib import file_digest,sha256
from pathlib import Path
from urllib.request import Request,urlopen
import fcntl,json,os,subprocess,sys,time
w=Path(__file__).parent
read=lambda f:json.loads(f.read_bytes());h=lambda f:sha256(f.read_bytes()).hexdigest()
with (w/'current-run.lock').open('a')as gate:
 fcntl.flock(gate,fcntl.LOCK_EX|fcntl.LOCK_NB)
 new=Path('/tmp/yuanfang249/native-slot-released.json')
 while not new.is_file():time.sleep(1)
 receipt=read(new);assert receipt['order']==249 and receipt['exit']==0 and not receipt['remaining'] and receipt['wrapper_closed']
 model=Path('/tmp/yuanfang249')
 with (model/'viewer.log').open('wb')as vout:
  vr=subprocess.run(['bash',model/'viewer.sh'],stdout=vout,stderr=vout)
 (model/'viewer.exit').write_text(str(vr.returncode)+'\n')
 # The city check resumes after the small viewer exits even if its own test failed.
 assert receipt['prior_exit_sha256']==h(Path('/tmp/yeetsoong248/native-slot-released.json'))
 before=read(w/'before/before.json');assert before['passed'] and before['browser_closed'] and len(before['captures'])==1
 pin=read(w/'31k-live-inputs.json');assert h(w/'check-historical-map.cjs')==pin['runner_sha256']
 f=w/'second-after-desktop-bootstrap-failure/current-boot-error.json';assert read(f)['failed'][0]['status']==502
 routes={}
 for port in (31182,31183):
  for method,span in [('GET',None),('HEAD',None),('GET','bytes=9-63')]:
   u=f'http://127.0.0.1:{port}/data/districts-display.geojson';req=Request(u,method=method,headers={'Range':span}if span else {})
   with urlopen(req,timeout=60)as r:body=r.read();status=r.status;declared=r.headers.get('X-Audit-SHA256')
   assert status==(206 if span else 200)
   if method=='GET' and not span:assert sha256(body).hexdigest()=='f5e0e34ea04b30c312d534fb3894362f83afe33f61052764213a45a102028c50' and len(body)==434379
   if span:assert len(body)==55
   routes[f'{port}-{method}-{span}']={'url':u,'status':status,'bytes':len(body),'sha256':sha256(body).hexdigest(),'asset_sha256':declared}
 (w/'resume-after-249.json').write_text(json.dumps(dict(time=datetime.now(timezone.utc).isoformat(),native_249=h(new),prior_control=h(w/'before/before.json'),driver=pin['runner_sha256'],recovered_http=routes),indent=2)+'\n')
 env={**os.environ,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','TMPDIR':str(w/'browser-work')}
 for phase in ('after-desktop','after-mobile','viewer'):
  if (w/(phase+'.exit')).is_file():
   assert (w/(phase+'.exit')).read_text().strip()=='0';continue
  cmd=['node',w/'check-historical-map.cjs',phase,w/'bound-inputs.json',w/phase,w/'before/before.json']
  if phase=='viewer':
   project=Path('/workspace/e-resource/projects/shanghai')
   cmd=['node','-r',project/'data/audit/brunner-mond-v1/viewer-timeout.cjs',project/'tools/check-candidate-viewer.cjs','changning-wuyi-road-127-garden-front',w/'viewer']
   env.update(SHANGHAI_PROJECT_ROOT=str(project),MODEL_BASE_URL='http://127.0.0.1:31183/')
  with (w/(phase+'.log')).open('wb')as output:
   result=subprocess.run(cmd,stdout=output,stderr=output,env=env)
  (w/(phase+'.exit')).write_text(str(result.returncode)+'\n')
  if result.returncode:sys.exit(result.returncode)
