"""Intersect normal rays independently with the actual three delivered facades."""
from pathlib import Path
import hashlib,json,math,sys,subprocess
from tempfile import TemporaryDirectory
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='huangpu-abraham-building-beijing-front'

def checks():
    result={'front':[],'corner':[]}
    def sample(label,u,height,lower,upper,face='front'):
        result[face].append((label,u,height,lower,upper))
    for i,u in enumerate((-8.39,-4.89,-1.53,2.10,5.87),1):
        for z in (1.0,2.55):
            sample(f'arch {i} recessed shop glazing',u+.14,z,-.35,-.26)
        sample(f'arch {i} pale keystone',u,4.00,.095,.15)
    for i,u in enumerate((-5.21,-3.69,-2.18,.63,3.91,7.15),1):
        for storey,z in enumerate((5.78,9.16,12.48),2):
            sample(f'upper opening {i}, storey {storey}',u+.14,z,-.35,-.25)
        for storey,z in ((2,7.31),(3,10.72)):
            sample(f'upper curved brick head {i}, key on storey {storey}',u,z,.105,.14)
        sample(f'upper opening flat head {i}',u,13.885,.064,.10)
    for j,u in enumerate((-7.1,-3.29,.14,3.76),1):
        sample(f'ground brick pier {j}',u,1.69,-.035,.04)
    for u in (-5.62,-1.82,2.67,6.12):
        sample('stone band above ground storefront',u,4.41,.12,.20)
        sample('mid-storey band',u,7.57,.10,.185)
    for z in (5.29,8.39,9.72):
        sample('shallow projected bay glazing',-8.09,z,.02,.103)
    for z in (4.15,7.73,9.15,11.02):sample('projecting stone band on canted bay',-8.13,z,.40,.57)
    for cx,z in ((-7.45,15.24),(-1.94,15.23),(3.70,15.20)):
        sample('dormer glazed opening',cx+.12,z,-.42,-.30)
    # The flat facade and the chamfer meet at (+8.50,0) in the local model.
    flat_eyelet=(8.50-3.12/2)+.55
    for side,u in [('front',flat_eyelet),('corner',-.12)]:
        sample('recessed oculus',u,16.,-.16,-.125,side)
        sample('ring stone',u+.37,16.,.07,.105,side)
    for z in (5.78,9.16,12.48):sample('chamfered corner glazing',.14,z,-.35,-.26,'corner')
    sample('pale corner door reveal',.755,1.66,.105,.17,'corner')
    return result


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
