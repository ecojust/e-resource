"""Check roof junctions with the wall and measure the two panes' physical recess."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import first_hit,load_triangles


def check(path):
    tri,ids,mats,meta=load_triangles(path)
    lower=tri.min(axis=1)
    upper=tri.max(axis=1)
    tests=[]
    def probe(key,origin,direction,axis,expected,high=None):
        # For these cardinal rays choose each triangle whose two fixed
        # coordinate intervals contain the sample. All scene materials remain.
        mask=np.ones(len(tri),dtype=bool)
        for j in range(3):
            if j!=axis:mask&=(lower[:,j]<=origin[j]+1.e-9)&(upper[:,j]>=origin[j]-1.e-9)
        candidate=np.flatnonzero(mask)
        index,distance,point=first_hit(tri[candidate],origin,direction)
        material=mats[ids[candidate[index]]] if np.isfinite(distance) else None
        passed=bool(material and any(t in material for t in expected) and (high is None or point[axis]<=high))
        tests.append(dict(test=key,origin=origin,direction=direction,first_material=material,
                          hit=None if material is None else np.round(point,5).tolist(),passed=passed))
    for x,group in [(3.34,'pale dormer panels'),(3.51,'pale dormer panels'),(3.77,'shaded glass'),
                    (3.99,'shaded glass'),(4.155,'casement timber'),(4.30,'light glass'),
                    (4.57,'light glass'),(4.84,'pale dormer panels'),(5.00,'pale dormer panels')]:
        for z in [8.83,9.12,9.40,9.62]:
            probe('shed dormer two lights and solid cheeks',[x,-3.,z],[0,1,0],1,[group],.39)
    # The tapering hole does not extend into either adjacent roof face.
    for x in [2.67,2.82,5.51,5.67]:
        for y in [.31,.63,1.01,1.45]:
            probe('solid clay on both sides of actual dormer cut',[x,y,15.],[0.,0.,-1.],2,
                  ['scalloped red clay tiles','weathered clay laps','ridge terracotta'])
    for x in [3.30,3.86,4.32,4.86]:
        probe('weather cap above measured sash',[x,.20,15.],[0,0,-1],2,['shed cover'])
        probe('tilted apron beneath sill from the courtyard',[x,-3.,8.46],[0,1,0],1,['scalloped red clay tiles'],.28)
    return dict(sha256=meta['sha256'],sample_count=len(tests),
                matched=sum(row['passed'] for row in tests),rows=tests)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('roles',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    out={n:check(args.roles/(n+'.glb')) for n in ('raw','decoded-full','decoded-lod')}
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print({n:f"{r['matched']}/{r['sample_count']}" for n,r in out.items()})
