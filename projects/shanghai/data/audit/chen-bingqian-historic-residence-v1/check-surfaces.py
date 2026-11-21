"""Measure projection depths at the eight open arcades and two tower roofs in every delivered mesh."""
from pathlib import Path
import json,sys,hashlib
import numpy as np,trimesh
from tempfile import TemporaryDirectory
import subprocess

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'jingan-chen-bingqian-historic-residence'
B = 3.22
views=[]
for i in range(8):
 x=(i-3.5)*B
 for z,l in [(2.8,'lower'),(8.85,'upper')]:
  for dx in (-.46,.46):views.append((f'bay {i+1} {l} recessed glazing',x+dx,z,-2.4,-1.10))
for i in range(1,8):
 x=(i-4)*B
 for z,l in [(3.25,'lower'),(8.75,'upper')]:views.append((f'cross-gallery pier {i} {l}',x,z,-.10,.34))
for x in [-9.45,-5.63,4.57,8.2]:
 views.extend([(f'string course {x}',x,6.85,.02,.70),(f'continuous roof cap {x}',x,13.42,.02,.45)])
for x in [-15.94,15.94]:
 views.extend([(f'tower face gallery opening {x}',x,3.40,-5.30,-1.70),(f'tower face upper opening {x}',x,9.18,-5.30,-1.70),(f'tower crown at {x}',x,17.0,.18,1.46),(f'tower cap {x}',x,19.74,-.15,-.08)])
views.append(('central garden parapet',0,1.69,.75,1.55))
def probe(path):
 scene=trimesh.load(path,force='mesh',process=False);tri=scene.triangles
 # Intersect front-directed rays with actual decoded GLTF triangles. The first hit is the largest Z.
 q=tri[:,:,:2];a=q[:,0];e1=q[:,1]-a;e2=q[:,2]-a;det=e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0];valid=abs(det)>1e-10;det=np.where(valid,det,1)
 rows=[]
 for label,x,y,low,high in views:
  d=[x,y]-a;u=(d[:,0]*e2[:,1]-d[:,1]*e2[:,0])/det;v=(e1[:,0]*d[:,1]-e1[:,1]*d[:,0])/det;inside=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)
  z=(tri[:,0,2]+u*(tri[:,1,2]-tri[:,0,2])+v*(tri[:,2,2]-tri[:,0,2]))[inside];front=float(z.max())if len(z)else None
  rows.append(dict(label=label,x=x,z=y,measured_gltf_front_z=front,expected_interval=[low,high],ok=front is not None and low<front<high))
 return rows

def verify():
    folder = PROJECT / 'assets/models/candidates' / ID
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    decoder = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    codec = PROJECT / 'vendor/meshopt_decoder.module.js'
    result = {}
    with TemporaryDirectory() as temp:
        for role in ('raw', 'full', 'lod'):
            asset = manifest['assets'][role]
            original = folder / asset['file']
            digest = hashlib.sha256(original.read_bytes()).hexdigest()
            assert digest == asset['sha256'], (role, digest)
            mesh = original
            if role != 'raw':
                mesh = Path(temp) / (role + '.glb')
                subprocess.run(['node', decoder, original, mesh, codec], check=True)
            rows = probe(mesh)
            assert all(point['ok'] for point in rows), (role, [p for p in rows if not p['ok']])
            result[role] = {'sha256': digest, 'samples': rows}
    return {'id': ID, 'checks': sum(len(row['samples']) for row in result.values()),
            'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'variants': result}


if __name__ == '__main__':
    report = verify()
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else AUDIT / 'surface-checks.json'
    output.write_text(json.dumps(report, indent=2) + chr(10))
    print(report['checks'], 'facade, opening and tower depth checks')
