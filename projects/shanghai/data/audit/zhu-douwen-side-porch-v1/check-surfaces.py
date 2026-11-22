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
    def normal(label,x,y,z,materials,distance,tol=.055):
        add(checks,label,[x,y,z],[0,1,0],materials,[distance-tol,distance+tol])
    for n,(x,y) in enumerate([(-3.16,-1.43),(2.91,-2.10)],1):
        for z,width in [(.08,.67),(.20,.61),(.31,.56),(.39,.51),(.90,.45),(1.98,.45),(3.21,.45),(3.49,.56),(3.63,.60)]:
            normal(f'column {n} cross section {z:.2f}',x+.04,y-1,z,['grey stone plinth','pale moulded stone','weathered limestone'],1-width/2,.046)
        normal(f'column {n} vertical arris',x+.148,y-.75,1.99,['weathered limestone'],.75-.225-.023,.012)
        normal(f'column {n} capitol square',x+.05,y-.90,3.62,['pale moulded stone'],.60,.06)
    for u in [-.86,-.49,-.14,.23,.53,.83]:
        x=-1.05+.715*u
        normal('arched door dark glass '+str(u),x,-.7,1.88,['smoked glass'],.858,.022) if abs(u)>.09 else None
    normal('arched door centre meeting stile',-1.05,-.7,1.85,['reddish brown joinery'],.779,.015)
    for fai in [.12,.34,.65,.98]:
        x=-1.05+.78*math.cos(fai*math.pi);z=2.27+.78*math.sin(fai*math.pi)
        normal('actual curved entry surround '+str(fai),x,-.55,z,['pale moulded stone'],.464,.028)
    for x,z in [(-4.92,1.58),(-4.37,1.68),(-4.87,5.55),(-4.38,5.96),(-7.51,5.87),(-7.94,6.77),(-.58,5.68),(2.67,5.63)]:
        normal('recessed side window '+str((x,z)),x,-1,z,['smoked glass'],1.158,.025)
    for x,z in [(-4.6,1.61),(-4.6,5.99),(-7.8,5.78),(-.85,5.81),(2.45,5.68)]:
        normal('window timber meeting bar '+str((x,z)),x,-.6,z,['reddish brown joinery'],.679,.015)
    for j in range(5):
        a=-.825+1.65*(j+.5)/5; vec=np.array([math.sin(a),-math.cos(a)])
        radius=2.22*math.cos(.165)
        origin=np.array([-7.8,1.46])+(radius+.75)*vec
        for z,mat,dist in [(1.14,'reddish brown joinery',.703),(2.04,'smoked glass',.81),(2.98,'reddish brown joinery',.703)]:
            add(checks,f'oriel light {j+1} {z}',[*origin,z],[*(-vec),0],[mat],(dist-.025,dist+.025))
    for x,z in [(-5.66,3.64),(-5.66+.433,3.64),(-5.66,3.64+.429)]:
        normal('stone flower or moulding '+str((x,z)),x,-.52,z,['pale moulded stone','weathered limestone'],.462,.063)
    for i in range(8):
        t=math.tau*i/8
        normal('eight independent rosette petals '+str(i),-5.66+.224*math.cos(t),-.5,3.64+.224*math.sin(t),['weathered limestone'],.403,.015)
    for x in [-6.05,-5.57]:
        normal('long rectangular panel '+str(x),x,-.6,1.9,['pale moulded stone'],.571,.01)
    for x,y in [(-2.4,-1.29),(-.4,-1.4),(1.65,-1.76)]:
        add(checks,'clear ground under porch '+str(x),[x,y,3.42],[0,0,-1],['grey stone plinth'],(3.28,3.33))
        add(checks,'covered porch soffit '+str(x),[x,y,2.90],[0,0,1],['weathered limestone'],(.84,.92))
    for i in [0,2,5,8,10]:
        px=-3.52+(3.14+3.52)*(i+.5)/11
        py=-1.61+(-2.36+1.61)*(i+.5)/11+.055
        normal('front terrace bottle '+str(i),px,py-.6,4.71,['pale moulded stone'],.495,.045)
    for z,depth in [(8.29,.093),(8.52,.14),(8.90,.255),(9.06,.29)]:
        normal('stepped cornice '+str(z),-2.62,-.81,z,['pale moulded stone','weathered limestone'],.81-depth,.026)
    for j in (1,3,5,7,9,11,13):
        normal('corner alternating stone '+str(j),-9.53,-.50,.54+j*.53+.19,['pale moulded stone'],.416,.018)
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
