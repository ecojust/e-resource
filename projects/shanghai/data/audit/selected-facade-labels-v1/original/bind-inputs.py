from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import json,hashlib,subprocess,runpy,numpy as np
p=Path('/workspace/e-resource/projects/shanghai');w=Path('/tmp/hamilton-focus-experiment/real-93');new=json.load(open(w.parent/'receipts/files.json'));prod=json.load(open('/tmp/shanghai-city-groups/scenes/93-production.json'));root=Path('/tmp/cishu-group-stage-93/projects/shanghai');sha=lambda b:hashlib.sha256(b).hexdigest()
# The original working tree already carries exact streamed and directory data. Check all local
# frozen identities and actual HTTP responses for both changed modules plus primary route files.
for n,d in prod['files'].items():assert sha((root/n).read_bytes())==d,n
names=['index.html','landmarks.html','src/app.js','src/map-scene.js','src/building-beacons.js','src/building-beacon-groups.js','data/candidate-city-integrations.json']
def get(k):
 url='http://127.0.0.1:20093/'+k;r=urlopen(url,timeout=30);d=r.read();expected=new.get(k,{}).get('after',prod['files'][k]);assert sha(d)==expected,k;return k,dict(url=r.url,status=r.status,bytes=len(d),sha256=expected)
with ThreadPoolExecutor(4)as e:receipts=dict(e.map(get,names))
base=dict(verified_at='2026-11-20',count=135,frozen_files=len(prod['files']),changed_files=new,remaining_frozen_inputs=len(prod['files'])-len(new),http=receipts)
m=root/'assets/models/candidates/huangpu-hamilton-house/manifest.json';f=json.load(m.open())['assets']['full'];web=m.parent/f['file'];assert sha(web.read_bytes())==f['sha256'];decoded=w/'mesh-decoded.glb'
subprocess.run(['node',p/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',web,decoded,p/'vendor/meshopt_decoder.module.js'],check=True)
reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
tri,*_=reader['load_triangles'](decoded);assert len(tri)==f['triangles']==39472
xyz,indices=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True)
np.save(w/'indices.npy',indices.reshape(-1,3).astype(np.int32));(w/'points.json').write_text(json.dumps(xyz.round(6).tolist(),separators=(',',':')))
base['mesh']=dict(input_sha256=f['sha256'],triangles=len(tri),vertices=len(xyz),source='independently decoded delivered EXT_meshopt_compression GLB',coordinate_convention='x positive local right, y inward, z up',points_sha256=sha((w/'points.json').read_bytes()),indices_sha256=sha((w/'indices.npy').read_bytes()))
(w/'bindings.json').write_text(json.dumps(base,indent=2)+'\n');print(len(prod['files']),len(xyz),len(tri),len(new))
