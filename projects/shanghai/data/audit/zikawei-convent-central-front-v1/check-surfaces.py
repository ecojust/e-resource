"""Intersect normal rays independently with the actual three delivered facades."""
from pathlib import Path
import hashlib,json,math,sys,subprocess
from tempfile import TemporaryDirectory
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='xuhui-zikawei-convent-central-front'

def checks():
    front=[]
    def sample(name,x,z,low,high):
        front.append((name,x,z,low,high))
    for x in (-4.86,-1.62,1.62,4.86):
        for z in (6.25,9.66):
            for side in (-1,1):
                sample('two dark shutter leaves',x+side*.34,z+1.05,-.14,-.06)
            if x < 0 and z < 7:
                sample('west porch handrail in front of lower sill',x,z-.11,1.77,1.81)
            else:
                sample('projecting window sill',x,z-.11,.25,.29)
    for x in (-6.54,-3.24,0,3.24,6.54):
        for z in (7.54,10.72):
            sample('rendered vertical pier',x,z,.15,.20)
        sample('modelled pier moulding',x,9.31,.29,.33)
    for x in (-1.95,1.95):
        sample('square ventilation shutter in main gable',x,13.84,-.30,-.23)
    for x,z in ((0,14.12),(0,15.41)):
        sample('dark central attic opening',x,z,-.30,-.23)
    for x,z in [(-4.50,13.28),(-2.15,14.58),(2.15,14.58),(4.50,13.28)]:
        sample('gable plaster face',x,z,-.02,.02)
    for x in (-4.98,-1.88):
        for z in (1.13,3.73):
            sample('visible western glazed porch sash',x+.33,z,1.61,1.68)
    for x in (-6.555,-3.435,-.315):
        sample('porch painted column',x,1.46,1.92,1.95)
    for x in (-8.38,8.38):
        for z in (7.30,10.68):
            sample('recessed flanking shutters',x+.31,z,-.86,-.75)
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
