"""Trace the free side of five open casements from the street to their deep shaded backing."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from check_upper_windows import load_triangles,openings,shots

def check(path,material,ymin=1.79,ymax=2.01):
    tri,mats,doc,sha=load_triangles(path);names=[v["name"] for v in doc["materials"]]
    rows=[];xx,zz=tri[:,:,0],tri[:,:,2]
    lo_x,hi_x,lo_z,hi_z=xx.min(1),xx.max(1),zz.min(1),zz.max(1)
    for r in openings():
        for role,x,z,expected,depth in shots(r):
            if not role.endswith("clear swing"):continue
            ids=np.flatnonzero((lo_x<=x)&(hi_x>=x)&(lo_z<=z)&(hi_z>=z))
            t=tri[ids];a=t[:,0];b=t[:,1]-a;c=t[:,2]-a
            determinant=b[:,0]*c[:,2]-b[:,2]*c[:,0];hits=abs(determinant)>1e-10
            den=np.where(hits,determinant,1.);dx=x-a[:,0];dz=z-a[:,2]
            u=(dx*c[:,2]-dz*c[:,0])/den;v=(b[:,0]*dz-b[:,2]*dx)/den
            hits&=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
            y=a[:,1]+u*b[:,1]+v*c[:,1]
            front=ids[hits&(y<ymin)]
            low=np.where(hits&(y>=ymin)&(y<=ymax),y,np.inf)
            hit=int(np.argmin(low)) if np.isfinite(low).any() else None
            mat=names[mats[ids[hit]]] if hit is not None else None
            rows.append(dict(window=r['label'],probe=role,x=x,z=z,front_limit_y=ymin,
                             front_intersections=len(front),back_limit_y=ymax,
                             back_first_y=float(low[hit]) if hit is not None else None,
                             back_first_material=mat,expected_back_material=material,
                             passed=not len(front) and mat==material))
    return dict(asset_sha256=sha,physical_triangles=len(tri),checks=rows,passed=len(rows)==5 and all(s['passed'] for s in rows))
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument('model',type=Path);a.add_argument('output',type=Path)
    a.add_argument('--material',default='Unlit recess beyond photographed open casements')
    args=a.parse_args();result=check(args.model,args.material);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(args.model.name,result['passed'],[(x['window'],x['back_first_material'],x['back_first_y']) for x in result['checks']])
    raise SystemExit(int(not result['passed']))
