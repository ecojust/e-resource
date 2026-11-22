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
    corners=[(-3.011,2.955),(-1.482,0),(1.482,0),(4.102,2.060)]
    for i,(left,right) in enumerate(zip(corners,corners[1:])):
        p=np.array(left);q=np.array(right);length=np.linalg.norm(q-p);t=(q-p)/length;n=np.array([t[1],-t[0]]);center=(p+q)/2
        def face(label,u,z,materials,limits):
            start=center+u*t+.86*n
            add(checks,str(i+1)+' '+label,[*start,z],[*(-n),0],materials,limits)
        for z,h in [(0.72,2.60),(4.77,2.70),(9.64,2.60),(13.65,1.69)]:
            for u in [-.33,.24]:
                face('recessed window pane',u,z+h*.31,['cool recessed glass'],(1.09,1.16))
            face('vertical steel division',0 if z<13 else -.184*(2.10 if i==1 else 1.62),z+h*.40,['charcoal steel sash'],(.98,1.06)) if z<13 else None
            if z<13:face('horizontal transom',.13,z+h*.54,['charcoal steel sash'],(.98,1.06))
            else:
                spring=z+h-.54
                for frac in (.22,.72):
                    face('attic slender horizontal sash',.07,spring-(1-frac)*(spring-z),['charcoal steel sash'],(.98,1.06))
            face('projecting stone sill',.16,z-.052,['weathered projecting cornice'],(.68,.78))
        for z in [1.89,5.6,10.78]:
            face('terminal stone pier',length/2-.10,z,['carved pale stone'],(.765,.81))
        for z in [12.86,13.14,15.90]:
            face('moulded cornice at measured level',.12,z,['carved pale stone','weathered projecting cornice'],(.45,.80))
        face('spandrel inside border',-.71,8.38,['grey bush-hammered render'],(.81,.85))
        if i==1:
            for angle in (-2.73,-2.23,-1.76,-1.22,-.67,-.25,.29,.69):
                face('wreath above central first-storey sash',.47*math.cos(angle),8.48+.50*math.sin(angle),['carved pale stone'],(.62,.78))
            face('centre of open foliate wreath',0,8.49,['grey bush-hammered render'],(.81,.85))
            face('ribbon fastening',0,8.97,['carved pale stone'],(.64,.72))
    for x,y in [(-1.5,2.4),(-1.0,1.65),(.4,.65),(1.83,1.84),(2.61,3.5),(-1.79,4.02),(.39,4.3),(.3,2.64)]:
        add(checks,'red tiled cap',[x,y,18.2],[0,0,-1],['weathered red tile','red hip tiles'],(.75,2.23))
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
