"""First intersections on the independently decoded raw, near, and distant geometry."""
import argparse
import json
import math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
def add(checks,name,start,direction,materials,limits):
    checks.append((name,np.array(start,dtype=float),np.array(direction,dtype=float),materials,limits))

def probes():
    checks=[]
    for x in (-2.92,2.92):
        for z in (1.46,1.82,2.24,2.65,3.08,3.48):
            add(checks,'turned column', [x,-1,z], [0,1,0],['ivory rendered column'],(.67,.91))
        add(checks,'square pink plinth',[x,-1,.72],[0,1,0],['dusty rose brick'],(.66,.79))
        for z in (4.12,4.7,5.28,5.91):
            add(checks,'upper timber post',[x,-1,z],[0,1,0],['weathered dark timber'],(.68,.97))
    for x in (-2.5,-1.66,-.76,.31,1.38,2.46):
        for z in (4.04,4.93,6.51):
            add(checks,'sill handrail or lintel',[x,-1,z],[0,1,0],['weathered dark timber'],(.49,.97))
    for x in (-1.82,-.86,.12,.86,1.82):
        add(checks,'open upper baluster interval',[x,-.62,4.56],[0,1,0],['warm pebble dash','weathered dark timber','shaded window glass'],(2.1,3.05))
    for x in (-2.05,-1.12,0,1.12,2.05):
        for z in (6.91,7.24):
            add(checks,'gable timber stud',[x,-1.3,z],[0,1,0],['weathered dark timber'],(.82,1.04))
    for x in (-1.65,-.70,.68,1.86):
        add(checks,'gable ochre infill',[x,-1.3,7.23],[0,1,0],['warm pebble dash'],(.86,1.09))
    for x in (-2.64,-1.88,0,1.89,2.65):
        if abs(x)<.03:continue
        for y in (.53,2.82,5.96):
            z=9.63-(9.63-6.61)*abs(x)/3.59
            add(checks,'pitched roof',[x,y,z+.98],[0,0,-1],['grey ribbed roof','raised roof seam'],(.9,1.10))
    edges=[((-3.13,1.75),(-1.78,.83)),((-1.78,.83),(1.78,.83)),((1.78,.83),(3.13,1.75)),
           ((-4.39,7.40),(-5.49,6.35)),((-5.49,6.35),(-5.49,4.57)),((-5.49,4.57),(-4.37,3.49))]
    for i,(a,b) in enumerate(edges):
        a=np.array(a);b=np.array(b);t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]])
        for u in (-.18,.16):
            center=(a+b)/2+t*u+.68*n
            for z in (1.66,2.02,2.37,2.86,3.15):
                add(checks,'shutter leaf '+str(i+1),[*center,z],[*(-n),0],['green black shutter','louvre leading edge'],(.67,.84))
        for z in (.37,.65,.96):
            center=(a+b)/2+.51*n
            add(checks,'brick plinth '+str(i+1),[*center,z],[*(-n),0],['dusty rose brick','warm lime joint'],(.45,.54))
    for x in (.60,.88,1.14):
        add(checks,'chimney cap',[x,6.48,11],[0,0,-1],['cream chimney stack','pale window sill'],(.72,1.15))
    for y in (5.02,5.64,5.89):
        add(checks,'garden dormer closed leaves',[-5.9,y,5.72],[1,0,0],['green black shutter','louvre leading edge'],(.90,1.12))
    return checks

def evaluate(work):
    out={}
    for row in json.loads((work/'delivered-decode.json').read_bytes()):
        role=row['variant'];tri=np.fromfile(row['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        names=np.array(row['material_names'])[np.fromfile(row['triangle_material_ids_file'],np.uint16)]
        a=tri[:,0];ab=tri[:,1]-a;ac=tri[:,2]-a;res=[];errors=[]
        for name,origin,ray,wanted,interval in probes():
            cross=np.cross(ray,ac);det=np.einsum('ij,ij->i',ab,cross)
            valid=abs(det)>1e-10;inv=np.divide(1.,det,out=np.zeros_like(det),where=valid)
            delta=origin-a;u=np.einsum('ij,ij->i',delta,cross)*inv;second=np.cross(delta,ab)
            v=second@ray*inv;distance=np.einsum('ij,ij->i',ac,second)*inv
            valid&=(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(distance>1e-6)
            candidates=np.flatnonzero(valid)
            index=int(candidates[np.argmin(distance[candidates])]) if len(candidates) else None
            hit=str(names[index]) if index is not None else None;d=float(distance[index]) if index is not None else None
            good=hit in wanted and interval[0]<=d<=interval[1]
            res.append(dict(name=name,origin=origin.tolist(),direction=ray.tolist(),material=hit,distance_m=d,passed=good))
            if not good:errors.append(res[-1])
        out[role]=dict(sha256=row['sha256'],triangles=len(tri),checks=res,passed=not errors)
        if errors:
            print(role,len(errors),errors[:12],flush=True)
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();result=evaluate(args.work);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert all(v['passed'] for v in result.values())
    print({k:len(v['checks'])for k,v in result.items()})
