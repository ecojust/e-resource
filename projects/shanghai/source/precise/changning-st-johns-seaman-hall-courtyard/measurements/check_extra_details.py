"""Check the through passage independently of viewpoint, and photograph-specific material hits."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import numpy as np

HERE=Path(__file__).resolve().parent
TOOL=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'

def check(mesh):
    reg=json.loads((HERE/'seaman-registration.json').read_bytes())
    scene=runpy.run_path(str(TOOL))['SerialScene'](mesh)
    centre=reg['parameters']['entrance axis']
    through=[]
    for dx in [-.70,0.,.70]:
        first=scene.ray([centre+dx,-1.0,1.58],np.array([0.,1.,0.]),15.)
        through.append({'start':[centre+dx,-1.,1.58],'segment_to_y_m':14.,'first_hit':first})
    samples={'court-colonnade':[(60,77),(225,124),(528,129),(521,149)],'east-wind-entrance':[(106,160),(106,168),(203,160),(203,174),(208,222),(112,93),(112,99)],'school-aerial':[(116,271),(274,271),(430,272)]}
    views={}
    for station,points in samples.items():
        s=reg['stations'][station]
        rot=np.asarray(s['R']).T
        out=[]
        for uv in points:
            ray=rot@np.linalg.solve(s['K'],[*uv,1])
            hit=scene.ray(s['eye'],ray/np.linalg.norm(ray),1000)
            out.append({'pixel':uv,'material':hit['material'] if hit else None,'world':list(hit['point']) if hit and 'point' in hit else None})
        views[station]=out
    return dict(mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),all_three_passage_segments_clear=all(r['first_hit'] is None for r in through),passage=through,photo_materials=views)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    a.output.write_text(json.dumps(check(a.mesh),ensure_ascii=False,indent=2,default=lambda o:o.tolist())+'\n')
