"""Recheck the local author handoff and a real city stage without writing to its signed production tree."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
w=Path(__file__).resolve().parent;stage=int(sys.argv[1]) if len(sys.argv)>1 else 259
p=w.parent/'pilot';contract=w/'final-placement-contract.json';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
for name in ['compare-vector.py','school-ground.py','clip-real-meshes.py']:
 subprocess.run([sys.executable,'-B',w/name],env=env,check=True)
saved=json.loads(contract.read_bytes());frag=json.loads((w/'ground-placement-fragment.json').read_bytes());assert all(saved.get(k)==v for k,v in frag.items())
subprocess.run(['node',w/'check-runtime.mjs',str(stage),contract,p,w/f'final-runtime-31{stage}.json'],env=env,check=True)
subprocess.run([sys.executable,'-B',w/'physical-camera-groups.py'],env=env,check=True)
subprocess.run(['node',w/'trace-city-camera.mjs'],env=env,check=True)
subprocess.run([sys.executable,'-B',w/'model-sightline-clearance.py',str(stage)],env=env,check=True)
assert all(r['city_mesh_sight_clear']for r in json.loads((w/'actual-camera-city-triangles.json').read_bytes())['results']);print('Verified',stage,sha(contract))
