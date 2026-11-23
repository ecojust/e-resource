from pathlib import Path
from hashlib import sha256
import json,os,subprocess,datetime,fcntl
p=Path('/workspace/e-resource/projects/shanghai');src=p/'source/precise/huangpu-russell-company-fuzhou-three-bay-front/source'
u=Path('/dev/shm/russell283-live');out=u/'verified-audit/photo-recheck';asset=p/'assets/models/candidates/huangpu-russell-company-fuzhou-three-bay-front';m=json.loads((asset/'manifest.json').read_bytes())
blend=asset/m['assets']['native']['file'];raw=asset/m['assets']['raw']['file'];sig=lambda path:sha256(path.read_bytes()).hexdigest()
assert sig(blend)==m['assets']['native']['sha256'] and sig(raw)==m['assets']['raw']['sha256']
report=out/'native-geometry-reopened.json';programs=[p/'tools/verify_editable_model.py',src/'verify_native_stone.py']
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as l:
 fcntl.flock(l,fcntl.LOCK_EX)
 start=now()
 with (u/'work/native-blender.log').open('wb')as lg:
  proc=subprocess.Popen(['/usr/bin/blender','--background',blend,'--threads','1','--python-exit-code','31','--python',programs[0],'--python',programs[1],'--',blend,raw,report],stdout=lg,stderr=lg,env={**os.environ,'TMPDIR':str(u/'work'),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
  code=proc.wait()
 entry=dict(start=start,finished=now(),pid=proc.pid,exit=code,editable_sha256=sig(blend),raw_sha256=sig(raw),programs={str(f.relative_to(p)):sig(f) for f in programs})
 assert code==0 and not Path(f'/proc/{proc.pid}').exists() and entry['editable_sha256']==m['assets']['native']['sha256']
 d=json.loads(report.read_bytes());assert d['match_raw'] and d['mesh_count']==94 and d['triangles']==19988 and d['packed_images_and_uvs']['Weathered dark granite ashlar']['checked_corner_uvs']==11472;entry['sha256']=sig(report)
 (out/'native-process.json').write_text(json.dumps(entry,indent=2)+'\n')
