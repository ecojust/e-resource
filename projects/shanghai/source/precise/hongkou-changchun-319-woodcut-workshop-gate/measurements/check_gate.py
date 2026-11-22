"""Check nearest physical GLB intersections against points read from both published photographs."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles

def check(path):
    tris,mi,names,_=load_triangles(path)
    a=tris[:,0];e=tris[:,1]-a;f=tris[:,2]-a
    fit=json.loads((HERE/'gate-camera-fit.json').read_text());obs=json.loads((HERE/'gate-pixel-tests.json').read_text())
    groups={'cap':['cap'],'base':['plinth'],'brick':['fired brick','mortar'],'white':['pale enamel','dark finish'],'brown':['brown stone','engraved lettering'],'leaf':['angled faces','painted finish'],'panel':['painted finish','dark finish'],'threshold':['dark frame edges']}
    rows=[]
    for epoch,cam in zip(('2023','2021'),fit['views']):
        mat=np.asarray(cam['P']);inv=np.linalg.inv(mat[:,:3]);eye=-inv@mat[:,3]
        qo=eye-a;s=np.cross(qo,e);ef=np.einsum('ij,ij->i',s,f)
        for expected,points in obs[epoch].items():
            for pixel in points:
                ray=inv@[*pixel,1];ray/=np.linalg.norm(ray);h=np.cross(ray,f);det=np.einsum('ij,ij->i',e,h)
                valid=np.abs(det)>1e-10;safe=np.where(valid,det,1)
                u=np.einsum('ij,ij->i',qo,h)/safe;v=s@ray/safe;t=ef/safe
                ok=valid&(u>=0)&(v>=0)&(u+v<=1)&(t>0);hit=None;xyz=None
                if ok.any():
                    k=int(np.argmin(np.where(ok,t,np.inf)));hit=names[mi[k]];xyz=(eye+t[k]*ray).round(4).tolist()
                good=hit is None if expected=='air' else hit is not None and any(label in hit for label in groups[expected])
                rows.append(dict(photo=epoch,pixel=pixel,expected=expected,first=hit,xyz=xyz,passed=bool(good)))
    counts={epoch:{'tested':sum(i['photo']==epoch for i in rows),'passed':sum(i['photo']==epoch and i['passed']for i in rows)}for epoch in ('2021','2023')}
    return dict(asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(tris),counts=counts,points=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('asset',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    r=check(a.asset);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r['counts'],[(v['photo'],v['pixel'],v['expected'],v['first'])for v in r['points']if not v['passed']])
