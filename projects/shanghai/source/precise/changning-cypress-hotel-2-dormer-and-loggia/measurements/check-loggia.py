"""Test each arch and the balcony's open spaces on both actual helper meshes."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

w = Path(__file__).resolve().parents[1]
helper = next(p for p in (w/'source/cypress_loggia.py', w/'work/cypress_loggia.py') if p.is_file())
sys.path[:0] = [str(helper.parent), str(w/'source')]
project=next((q for q in Path(__file__).absolute().parents if (q/'tools/package_architectural_model.py').is_file()),None)
if project is not None:sys.path.insert(0,str(project/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from cypress_loggia import add_loggia, PALETTE, FRONT, REAR, PIER, RIM, BOARD
from lawn import plane_world, project, EYE, DATA

def sha(p):
    return sha256(p.read_bytes()).hexdigest()

def intersect(triangles, ray):
    e1, e2 = triangles[:,1]-triangles[:,0], triangles[:,2]-triangles[:,0]
    h = np.cross(ray,e2)
    det = np.einsum('ij,ij->i',e1,h)
    inv = np.divide(1., det, where=abs(det)>1e-10, out=np.zeros_like(det))
    e = EYE-triangles[:,0]
    u = np.einsum('ij,ij->i',e,h)*inv
    q = np.cross(e,e1)
    v = (q@ray)*inv
    t = np.einsum('ij,ij->i',e2,q)*inv
    ids = np.flatnonzero((t>0)&(abs(det)>1e-10)&(u>=0)&(v>=0)&(u+v<=1))
    return ids[np.argmin(t[ids])] if ids.size else None

survey = json.loads((DATA/'loggia-arch-and-railing-pixels.json').read_bytes())
results = []
for lod in (False,True):
    mesh=Builder(PALETTE)
    add_loggia(mesh,lod)
    tris=[];materials=[]
    for part in mesh.parts:
        tri=np.asarray(part['vertices'])[np.asarray(part['triangles'])]
        if tri[:,:,1].min() > 0:continue
        tris.extend(tri);materials.extend([part['material']]*len(tri))
    tri=np.asarray(tris);probes=[]
    def check(pixel,allowed):
        target,=plane_world([pixel],1,FRONT)
        assert np.max(abs(project([target])[0]-pixel)) < 1e-7
        hit=intersect(tri,target-EYE)
        material=materials[hit] if hit is not None else None
        assert material in allowed,(pixel,material,allowed)
        probes.append(dict(pixel=pixel,foreground_material=material))
    for arc in survey['inner_arch_edges']:
        for x,y in arc['trace_left_to_right'][2:-2:2]:
            check([x,y+3.2],[None]);check([x,y-2.9],[PIER,RIM])
    for x,y in [(570,323),(633,322),(575,348),(633,349),(579,294),(618.4,294),(626.6,294)]:
        check([x,y],[None])
    for x,y in [(542,330),(600,329),(600,360),(661,325)]:
        check([x,y],[PIER])
    for x in [585,594,607.5,614.5,622.5,630.5]:
        check([x,294],[BOARD])
    for x,y in [(548,286.7),(630,282.8)]:
        check([x,y],[RIM])
    results.append(dict(level='far' if lod else 'full',parts=len(mesh.parts),triangles=sum(len(p['triangles']) for p in mesh.parts),probes=probes))
out=DATA/'loggia-geometry-checked.json'
out.write_text(json.dumps(dict(helper_sha256=sha(helper),observation_sha256=sha(DATA/'loggia-arch-and-railing-pixels.json'),camera_sha256=sha(DATA/'lawn-camera.json'),facade_y=FRONT,rear_y=REAR,both_depths_estimated=True,results=results),indent=2)+'\n')
print(sha(out),[(r['triangles'],len(r['probes'])) for r in results])
