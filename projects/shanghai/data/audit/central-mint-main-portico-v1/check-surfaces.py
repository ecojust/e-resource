"""Intersect normal rays independently with the actual three delivered facades."""
from pathlib import Path
import hashlib,json,math,sys,subprocess
from tempfile import TemporaryDirectory
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='putuo-central-mint-main-portico'

def checks():
    front=[]
    def sample(name,x,z,low,high):front.append((name,x,z,low,high))
    for n,cx in enumerate((-7.4,-3.43,-2.05,2.05,3.43,7.4),1):
        for z in (1.52,3.72,6.22,8.74):sample(f'Ionic shaft {n}',cx,z,2.57,2.68)
        sample(f'Shaft {n} profiles toward centre',cx+.29,5.76,2.43,2.57)
        sample(f'Column {n} moulded base',cx,.96,2.70,2.80)
        sample(f'Column {n} abacus',cx+.47,9.78,2.68,2.72)
    for cx in (-2.74,2.74):
        for z in (2.28,4.69,7.78):sample('light between paired columns',cx,z,-.28,.27)
    for cx in (-5.51,.20,5.91):
        for z in (2.41,7.91):sample('deep set portal or window',cx,z,-.22,-.14)
    for side in (-1,1):
        cx=side*10.42
        for z in (1.58,2.86,7.36,8.29,12.57,13.08):
            sample('flanking mullioned glazing',cx+.25,z,.11,.19)
        for z in (6.45,12.02):sample('flanking dressed stone sill',cx+.25,z,.37,.52)
        sample('tall pilaster beside window',cx+side*1.93,7.91,.47,.54)
        sample('projecting cap of stepped attic',cx,17.10,.46,.63)
    for x,z in ((0,13.03),(-3.48,12.12),(3.48,12.12),(-6.33,11.57),(6.33,11.57)):
        sample('stone tympanum',x,z,2.87,3.05)
    for z,d in ((.072,4.48),(.24,4.175),(.57,3.26),(.74,2.955)):
        for x in (-4.55,.24,4.55):sample('graduated granite stair fronts',x,z,d-.02,d+.02)
    for x in (-7.8,-3.7,.25,3.7,7.8):sample('projecting portico cornice',x,11.12,2.88,2.99)
    return {'front':front}


def probe(path):
    mesh=trimesh.load(path,force='mesh',process=False)
    all_triangles=mesh.triangles[:,:,[0,2,1]]*[1,-1,1]
    result=[]
    for plane,entries in checks().items():
        corner=plane=='corner'
        origin=np.array([9.50,1.04])if corner else np.zeros(2)
        direction=np.array([2.,2.08])if corner else np.array([1.,0.])
        direction/=np.linalg.norm(direction)
        outward=np.array([direction[1],-direction[0]])
        local=all_triangles[:,:,:2]-origin
        projected=np.stack((local@direction,all_triangles[:,:,2]),axis=2)
        depth=local@outward
        a=projected[:,0];b=projected[:,1]-a;c=projected[:,2]-a
        det=b[:,0]*c[:,1]-b[:,1]*c[:,0];valid=abs(det)>1e-9;det=np.where(valid,det,1.)
        for label,u,z,lo,hi in entries:
            d=[u,z]-a;s=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/det;t=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/det
            hit=valid&(s>=-1e-8)&(t>=-1e-8)&(s+t<=1+1e-8)
            dist=depth[:,0]+s*(depth[:,1]-depth[:,0])+t*(depth[:,2]-depth[:,0])
            first=float(max(dist[hit]))if hit.any()else None
            result.append({'part':label,'plane':plane,'horizontal_m':u,'height_m':z,'required_front_depth_m':[lo,hi],'front_depth_m':None if first is None else round(first,6),'ok':first is not None and lo<=first<=hi})
    return result


def main():
    folder=PROJECT/'assets/models/candidates'/ID
    manifest=json.loads((folder/'manifest.json').read_bytes())
    decoder=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    codec=PROJECT/'vendor/meshopt_decoder.module.js'
    result={}
    with TemporaryDirectory() as temp:
        for role in ('raw','full','lod'):
            x=manifest['assets'][role];f=folder/x['file'];h=hashlib.sha256(f.read_bytes()).hexdigest()
            assert h==x['sha256'];actual=f
            if role!='raw':
                actual=Path(temp)/(role+'.glb')
                subprocess.run(['node',decoder,f,actual,codec],check=True)
            rows=probe(actual)
            failures=[v for v in rows if not v['ok']]
            assert not failures,(role,failures)
            result[role]={'sha256':h,'triangles':x['triangles'],'samples':rows}
    (HERE/'surface-checks.json').write_text(json.dumps({'id':ID,'checks':sum(len(a['samples'])for a in result.values()),'variants':result},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
