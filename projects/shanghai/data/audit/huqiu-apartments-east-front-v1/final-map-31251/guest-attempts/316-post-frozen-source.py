"""Replay the actual delivered files and their two signed city blocks after the native save."""
from pathlib import Path
import sys,os,subprocess
sys.path.insert(0,'/tmp/kangding759-316/mapping/handoff')
from receipts import ASSETS,AUDIT,WORK,digest,read,write
sys.path.insert(0,str(AUDIT))
mapping=Path('/dev/shm/kangding759-316/mapping')
mf=ASSETS/'manifest.json';parent=read('/tmp/eye-residence315/raw-315-confirmed.json')
cat=Path(parent['root'])/'projects/shanghai/data/candidate-city-integrations.json'
assert digest(cat)==parent['catalog_sha256']
commands=[['verify-placement.py','--manifest',mf,'--work',mapping,'--out',AUDIT,'--previous',cat],
          ['check-surfaces.py','--work',mapping,'--out',AUDIT/'visible-surfaces.json'],
          ['check-aggregate.py','--manifest',mf,'--out',AUDIT/'effective-uv.json'],
          ['check-camera.py','--contract',AUDIT/'final-placement-contract.json','--work',mapping,'--surfaces',AUDIT/'visible-surfaces.json','--out',AUDIT/'camera-sightlines.json']]
for program,*args in commands:
    subprocess.run([sys.executable,'-Bu',WORK/'array-run.py',sys.executable,'-Bu',(Path('/run/codex-docker/user/316-post-geometry/frozen-geometry/data/audit/zhu-douwen-side-porch-v1') if program=='check-camera.py' else AUDIT)/program,*args],env={**os.environ,'OPENBLAS_NUM_THREADS':'1'},check=True)
for f in ('final-placement-contract.json','visible-surfaces.json','effective-uv.json','camera-sightlines.json'):
    assert read(AUDIT/f)==read(AUDIT/'preflight'/f),f
geom=read(AUDIT/'placement-geometry.json')
assert geom['manifest_sha256']==digest(mf)
prior=read(AUDIT/'preflight/placement-geometry.json')
assert {k:v for k,v in geom.items()if k!='manifest_sha256'}=={k:v for k,v in prior.items()if k!='manifest_sha256'}
write(WORK/'post-geometry.json',dict(passed=True,manifest_sha256=digest(mf),parent_catalog_sha256=parent['catalog_sha256'],proofs={k:digest(AUDIT/k)for k in ('final-placement-contract.json','visible-surfaces.json','effective-uv.json','camera-sightlines.json','placement-geometry.json','map-case.json')}))
