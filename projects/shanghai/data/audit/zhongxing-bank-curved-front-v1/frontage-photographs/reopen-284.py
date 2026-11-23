"""Verify the registered material and UVs in the published Zhongxing Blender scene."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os,shutil,subprocess
out=Path(__file__).resolve().parent
project=out.parents[3]
source=project/'data/audit/zhongxing-bank-curved-front-v1/check-native-uv.py'
assets=project/'assets/models/candidates/huangpu-zhongxing-bank-curved-front'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads((assets/'manifest.json').read_bytes())
for role,row in doc['assets'].items():
    path=assets/row['file']
    assert path.stat().st_size==row['bytes'] and digest(path)==row['sha256']
blend=assets/doc['assets']['native']['file']
proof=out/'native-uv-reopened.json'
stamp=lambda:datetime.now(timezone.utc).isoformat()
start=stamp()
with (out/'native-reopen.log').open('wb') as log:
    proc=subprocess.Popen([shutil.which('blender'),'-b',blend,'-t','1','--python-exit-code','1','-P',source,'--',proof],env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),stdout=log,stderr=subprocess.STDOUT)
    status=proc.wait()
if status: raise SystemExit(status)
result=json.loads(proof.read_bytes())
assert result['native_sha256']==digest(blend) and result['loop_checks']>0
(out/'native-reopen-process.json').write_text(json.dumps(dict(program_sha256=digest(source),replay_sha256=digest(Path(__file__)),opened_model=blend.name,assets={r:v['sha256']for r,v in doc['assets'].items()},pid=proc.pid,exit=status,start=start,finish=stamp(),report_sha256=digest(proof),active_uv_corners=result['loop_checks'],texture_size=[128,128]),indent=2)+'\n')
