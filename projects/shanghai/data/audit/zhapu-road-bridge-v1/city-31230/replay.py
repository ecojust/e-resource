from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json,hashlib,subprocess,sys,os,tempfile,shutil
w=Path(__file__).parent
a=Path('/workspace/e-resource/projects/shanghai/data/audit/zhapu-road-bridge-v1/signed-stations')
j=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
p=j(w/'presentation-inputs.json')
assert p['passed'] and p['rows']['230']['count']==267
old=j(a/'summary.json')
assert old['catalog_sha256']==p['rows']['230']['catalog_sha256']
started=datetime.now(timezone.utc).isoformat()
with tempfile.TemporaryDirectory(prefix='zhapu-230-',dir=max(['/tmp','/dev/shm'],key=lambda v:shutil.disk_usage(v).free))as work:
 result=subprocess.run([sys.executable,'-B',a/'replay.py','http://127.0.0.1:31230/'],capture_output=True,text=True,env=dict(os.environ,TMPDIR=work,OPENBLAS_NUM_THREADS='1'))
 assert result.returncode==0,(result.stdout,result.stderr)
 finished=datetime.now(timezone.utc).isoformat()
walk=j(a/'walk.json');ids={v['id'] for v in walk['reports']};expected={'huangpu-waibaidu-bridge','huangpu-sichuan-road-bridge','huangpu-zhapu-road-bridge'}
assert ids==expected
c=sum(len(v['traversals']) for v in walk['reports'])
r=sum(t['rays'] for v in walk['reports'] for t in v['groups'])
assert c==36 and r==162
doc=dict(order=230,passed=True,exit=0,base='http://127.0.0.1:31230/',started=started,finished=finished,production_sha256=p['rows']['230']['production_sha256'],catalog_sha256=old['catalog_sha256'],checked_bridge_ids=sorted(ids),variant_traversals=c,surface_samples=r,reference_reports_sha256=sha(a/'walk.json'),shared_sidewalk_checks_sha256=sha(a/'shared-sidewalk-id.json'),verified_scripts={f:sha(a/f)for f in ['replay.py','real-walk.mjs','shared-segments.mjs']},actual_stdout=result.stdout.splitlines()[-1])
(w/'replayed-signed-navigation.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
print(c,r,doc['actual_stdout'],flush=True)
