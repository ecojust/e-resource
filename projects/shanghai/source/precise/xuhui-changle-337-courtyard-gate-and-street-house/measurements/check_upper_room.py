"""Photographic first intersections with the upper room, in the unaltered station frame."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from register_street import Camera

D = Path(__file__).resolve().parent
TRACER = D.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/glb_triangles.py'
Scene = runpy.run_path(str(TRACER))['SerialScene']
def camera_data(view):
    if view == '2017':
        c=Camera(view)
        return c.c,c.K,c.R
    c=json.loads((D/'upper-room-stations.json').read_bytes())['cameras'][view]
    return np.array(c['eye']),np.array(c['K']),np.array(c['R'])

def check(mesh):
    record=json.loads((D/'upper-room-first-hit-pixels.json').read_text());scene=Scene(mesh)
    rows=[]
    for pick in record['picks']:
        c,K,R=camera_data(pick['view']);u,v=pick['uv'];d=R.T@np.linalg.solve(K,[u,v,1]);d/=np.linalg.norm(d)
        hit=scene.ray(c,d,80)
        ok=bool(hit and any(k in hit['material'].lower() for k in pick['materials']) and hit['point_enu_m'][2]>6.75)
        rows.append(dict(**pick,hit=hit,exact=ok))
    return dict(asset=scene.asset,matched=sum(r['exact']for r in rows),total=len(rows),rows=rows)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path);a=cli.parse_args()
    result=check(a.mesh);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result['matched'],result['total'])
