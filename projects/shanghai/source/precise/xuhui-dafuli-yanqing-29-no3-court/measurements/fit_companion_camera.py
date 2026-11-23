from pathlib import Path
from scipy import ndimage
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from PIL import Image
import json
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('photo',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
im=np.asarray(Image.open(args.photo).convert('L')).astype(float)
h,wd=im.shape
# Orientations at local edges, at an angular tolerance which rejects features off all three architectural axes.
gy,gx=np.gradient(ndimage.gaussian_filter(im,1.))
a,b,d=[ndimage.gaussian_filter(p,2.) for p in [gx*gx,gx*gy,gy*gy]]
disc=np.hypot(a-d,2*b);coherent=(disc>.93*(a+d))&((a+d)>55)
ys,xs=np.nonzero(coherent);keep=np.random.default_rng(59).choice(len(xs),4500,replace=False)
x=xs[keep];y=ys[keep];mids=np.column_stack([x,y]);angle=np.arctan2(2*b,a-d)/2
normals=np.column_stack([np.cos(angle[y,x]),np.sin(angle[y,x])]);weight=np.sqrt(np.minimum(disc[y,x],180))
def matrix(v,f):
    k=np.array([[f,0,wd/2],[0,f,h/2],[0,0,1.]])
    a=Rotation.from_rotvec(v).as_matrix()
    return k,a
def scores(v,f):
    k,r=matrix(v,f);vp=(k@r).T
    ray=vp[None,:,:2]-mids[:,None,:]*vp[None,:,2,None]
    return np.einsum('nai,ni->na',ray,normals)/np.maximum(np.linalg.norm(ray,axis=2),1e-9)
ranks=[]
for equiv in (22,24,27,30,34,38):
    focal=wd*equiv/36
    x=np.r_[(np.array([319.,296.])-[wd/2,h/2])/focal,1];x/=np.linalg.norm(x)
    y=np.cross(x,[-.02,-.99,-.16]);y/=np.linalg.norm(y)
    z=np.cross(x,y)
    v=Rotation.from_matrix(np.stack([x,y,z],axis=1)).as_rotvec()
    for deg in (5.,2.8,1.3,.8,.65):
        grade=scores(v,focal);axis=np.argmin(abs(grade),axis=1)
        ids=np.flatnonzero(abs(grade[np.arange(len(axis)),axis])<np.sin(np.deg2rad(deg)))
        v=least_squares(lambda t:scores(t,focal)[ids,axis[ids]]*weight[ids],v).x
    k,a=matrix(v,focal);vp=(k@a).T;dist=abs(scores(v,focal)).min(1)
    ranks.append(dict(equiv=equiv,accepted=int((dist<.02).sum()),K=k.tolist(),R=(a@np.diag([-1,1,-1])).tolist(),vp=(vp[:,:2]/vp[:,2,None]).tolist()))
args.output.write_text(json.dumps(ranks,indent=2)+'\n')
print([(r['equiv'],r['accepted'],np.round(r['vp'][0],1).tolist()) for r in ranks])
