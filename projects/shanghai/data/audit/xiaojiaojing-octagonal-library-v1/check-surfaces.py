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
    for i in range(8):
        theta=-math.pi/2+i*math.pi/4
        normal=np.array([math.cos(theta),math.sin(theta)])
        tangent=np.array([-normal[1],normal[0]])
        def face(name,u,z,material,lo,hi):
            start=(5.68244+.86)*normal+u*tangent
            add(checks,f'facet {i+1}: {name}',[*start,z],[*-normal,0],[material],(lo,hi))
        for u,z in [(-1.47,5.71),(1.32,7.45)]:
            face('ochre wall beside opening',u,z,'ochre lime render',.845,.875)
        for u,z in [(-.57,5.46),(.16,5.37),(.61,6.15),(.11,6.83)]:
            face('recessed upper glass',u,z,'recessed blue grey glass',1.01,1.055)
        face('upper vertical timber',1.79/6,5.55,'painted dark timber',.92,.97)
        face('upper horizontal timber',.14,5.05+1.94/3,'painted dark timber',.92,.97)
        face('pale window border',.923,5.97,'pale green window surround',.79,.85)
        face('window sill',.21,4.98,'pale green window surround',.72,.78)
        face('transom glass',.12,7.69,'recessed blue grey glass',1.01,1.055)
        face('transom upright',-1.73/6,7.69,'painted dark timber',.92,.97)
        face('ruyi segment',.27*1.83,7.135+.087*1.83,'pale green window surround',.79,.85)
        face('stepped bracket arm',0,3.35,'painted dark timber',.42,.49)
        face('upper bracket',0,3.47,'painted dark timber',.25,.32)
        face('rafter seat',0,3.56,'dark space below eaves',.17,.24)
        face('basal stone course',1.63,.38,'grey stone threshold',.74,.80)
        for r in (2.1,4.0,5.35):
            xy=r*normal+.09*tangent
            add(checks,f'facet {i+1}: pitched green roof',[*xy,12.],[0,0,-1],['deep green glazed roof tiles'],(1.3,4.0))
        xy=(6.39*normal+.15*tangent)
        add(checks,f'facet {i+1}: lower green eave',[*xy,5],[0,0,-1],['deep green glazed roof tiles'],(.50,1.44))
        if i==0:
            face('blue-green door leaf',-.65,1.64,'weathered blue green door',.86,1.0)
            face('ochre door leaf',.65,1.64,'muted light ochre panel',.86,1.0)
            face('door fanlight',.37,3.04,'recessed blue grey glass',.95,1.02)
            face('door fanlight bar',-.6425,3.02,'painted dark timber',.88,.94)
            face('door surround',1.34,1.47,'pale green window surround',.77,.82)
            for j in range(4):
                xy=(5.68244+.99-.26*j)*normal
                add(checks,f'courtyard stone step {j+1}',[*xy,1],[0,0,-1],['grey stone threshold'],(.875-.11*j,.905-.11*j))
        if i in (1,7):face('lower garden glass',.24,1.46,'recessed blue grey glass',1.01,1.055)
    add(checks,'central glazed finial',[.005,0,12.],[0,0,-1],['patinated green tile drip'],(.56,.61))
    return checks

def evaluate(work):
    from surface_data import triangles
    out={}
    for row in json.loads((work/'delivered-decode.json').read_bytes()):
        role=row['variant']
        tri,slots,materials=triangles(Path(row['decoded_glb']))
        names=np.array([m['name']for m in materials])[slots]
        trilow,trihigh=tri.min(axis=1),tri.max(axis=1)
        res=[];errors=[]
        for name,origin,ray,wanted,interval in probes():
            endpoint=origin+ray*(interval[1]+.02)
            take=np.flatnonzero(np.all(trihigh>=np.minimum(origin,endpoint)-1e-7,axis=1)&np.all(trilow<=np.maximum(origin,endpoint)+1e-7,axis=1))
            subset=tri[take];a=subset[:,0];ab=subset[:,1]-a;ac=subset[:,2]-a
            cross=np.cross(ray,ac);det=np.einsum('ij,ij->i',ab,cross)
            valid=abs(det)>1e-10;inv=np.divide(1.,det,out=np.zeros_like(det),where=valid)
            delta=origin-a;u=np.einsum('ij,ij->i',delta,cross)*inv;second=np.cross(delta,ab)
            v=second@ray*inv;distance=np.einsum('ij,ij->i',ac,second)*inv
            valid&=(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(distance>1e-6)
            candidates=np.flatnonzero(valid)
            index=int(candidates[np.argmin(distance[candidates])]) if len(candidates) else None
            hit=str(names[take[index]]) if index is not None else None;d=float(distance[index]) if index is not None else None
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
