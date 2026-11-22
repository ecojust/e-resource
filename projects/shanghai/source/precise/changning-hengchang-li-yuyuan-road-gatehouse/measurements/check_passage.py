"""Run the original 114 exhibit photograph observations against an ordinary decoded GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles

MATERIAL_FAMILIES={
    'cream board':('display backing','line of print'),
    'pale arch':('pale arch','moulding light','moulding shadow'),
    'grey brick':('facing brick','worn brick','grey mortar','red brick'),
    'plinth':('riven plinth','dark plinth stone'),
    'paving':('grey paving',),
    'wood or glass recess':('inset shaded glass','reddish window','red box'),
    'ceiling':('warm ceiling',),
}

def audit_mesh(tri,matids,materials):
    points=json.loads((HERE/'passage-independent-photo-points.json').read_bytes())
    a=tri[:,0]
    ab,ac=tri[:,1]-a,tri[:,2]-a
    result={}
    for name,cam in points['cameras'].items():
        P=np.asarray(cam['P'])
        inverse=np.linalg.inv(P[:,:3])
        eye=-inverse@P[:,3]
        delta=eye-a
        cross_delta=np.cross(delta,ab)
        numerator=np.einsum('ij,ij->i',cross_delta,ac)
        projected=tri@P[:,:3].T+P[:,3]
        depth=projected[:,:,2]
        uv=projected[:,:,:2]/np.where(abs(depth)<1e-10,1e-10,depth)[:,:,None]
        low,high=uv.min(axis=1),uv.max(axis=1)
        crossing=depth.min(axis=1)<=0
        visible=depth.max(axis=1)>0
        def first(pixel):
            use=np.flatnonzero(visible&(crossing|((low<=pixel).all(axis=1)&(high>=pixel).all(axis=1))))
            if not len(use):return None
            d=inverse@[*pixel,1.]
            d/=np.linalg.norm(d)
            side=np.cross(d,ac[use])
            det=np.einsum('ij,ij->i',ab[use],side)
            valid=abs(det)>1.e-12
            divisor=np.where(valid,det,1.)
            u=np.einsum('ij,ij->i',delta[use],side)/divisor
            v=cross_delta[use]@d/divisor
            dist=numerator[use]/divisor
            hits=np.flatnonzero(valid&(u>=0)&(v>=0)&(u+v<=1)&(dist>1.e-7))
            if not len(hits):return None
            face=use[hits[dist[hits].argmin()]]
            return materials[matids[face]]
        rows=[]
        for point in (p for p in points['probes'] if p['photo']==name):
            pixel=np.asarray(point['uv'])
            surface=first(pixel)
            def matches(mat):
                return any(token in (mat or '').lower() for token in MATERIAL_FAMILIES[point['expected']])
            radius=0 if matches(surface) else None
            if radius is None:
                for distance in (1,2,3):
                    if any(matches(first(pixel+distance*np.array([np.cos(theta),np.sin(theta)]))) for theta in np.arange(8)*np.pi/4):
                        radius=distance
                        break
            rows.append({**point,'material':surface,'nearest_radius_px':radius})
        result[name]={'tested':len(rows),'direct':sum(p['nearest_radius_px']==0 for p in rows),
                      'within_3px':sum(p['nearest_radius_px'] is not None for p in rows),'samples':rows}
    return result

def check(path):
    tri,ids,mats,asset=load_triangles(path)
    return {'asset':asset,'triangles':len(tri),'observations':audit_mesh(tri,ids,mats)}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('meshes',type=Path,nargs='+')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result={p.name:check(p) for p in args.meshes}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
