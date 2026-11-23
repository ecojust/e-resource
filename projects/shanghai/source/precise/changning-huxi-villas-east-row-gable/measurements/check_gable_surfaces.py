"""Compare new native-pixel reads from the courtyard photograph against an actual exported GLB."""
from pathlib import Path
import argparse, json, hashlib, runpy
import numpy as np

HERE = Path(__file__).absolute().parent
MATERIALS = {
    'wall': ['light mineral render'],
    'equipment': ['condenser casing', 'dark soffit', 'shadow'],
    'metal': ['dark soffit', 'shadow'],
    'window': ['grey-green glazing', 'green steel'],
    'shade': ['shadow'], 'pipe': ['white rainwater pipe'],
    'brick': ['red facing brick'], 'panel': ['light spandrel'], 'coping': ['grey cement'],
}

def evaluate(mesh):
    loader = HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    scene = runpy.run_path(str(loader))['SerialScene'](mesh)
    source = json.loads((HERE/'native-surface-controls.json').read_bytes())
    camera = json.loads((HERE/'courtyard-camera.json').read_bytes())
    origin = np.asarray(camera['camera_xyz'])
    ray = np.asarray(camera['R']).T @ np.linalg.inv(camera['K'])
    records = []
    for label, u, v, material in source['points']:
        result = scene.ray(origin,ray@[u,v,1],100)
        matches = bool(result and any(result['material'].endswith(name) for name in MATERIALS[material]))
        records.append(dict(label=label,native_pixel=[u,v],expected=material,first_surface=result,matches=matches))
    return dict(mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),direct=sum(r['matches'] for r in records),
                total=len(records),results=records,road_limit=source['road_limit'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    r=evaluate(a.mesh);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['direct'],r['total'])
