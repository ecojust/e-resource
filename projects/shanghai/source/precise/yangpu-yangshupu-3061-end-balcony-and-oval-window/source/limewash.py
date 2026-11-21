"""Seamless, fine-grained ivory limewash created for the lane-house facade."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

TEXTURE=Path(__file__).with_name('yangshupu-3061-limewash.png')
CAST='Lane 3061 ivory limewash'
REPEAT=1.16


def create():
    rng=np.random.default_rng(30611913)
    n=192
    noise=rng.normal(0,1,(n,n))
    wide=gaussian_filter(noise,7.8,mode='wrap')
    medium=gaussian_filter(noise,1.35,mode='wrap')
    relief=gaussian_filter(rng.random((n,n)),.62,mode='wrap')
    tint=42*wide+7*medium+1.4*noise+6*(relief-np.roll(relief,1,axis=0))
    rgb=np.array([220.,216.,193.])+tint[:,:,None]*np.array([1.,.89,.76])
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(TEXTURE,optimize=True)


def apply_metric_uv(builder):
    for part in builder.parts:
        if part['material']!=CAST:continue
        vertices=np.asarray(part['vertices'],dtype=np.float32).astype(float)
        faces=vertices[np.asarray(part['triangles'])]
        n=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
        h=np.linalg.norm(n[:,:2],axis=1)
        vertical=h>abs(n[:,2])
        along=np.column_stack([-n[:,1],n[:,0]])/np.maximum(h[:,None],1e-16)
        flip=along[np.arange(len(n)),np.argmax(abs(along),axis=1)]<0
        along[flip]*=-1
        u=np.where(vertical[:,None],np.einsum('nvi,ni->nv',faces[:,:,:2],along),faces[:,:,0])
        v=np.where(vertical[:,None],faces[:,:,2],faces[:,:,1])
        part.update(vertices=faces.reshape(-1,3).tolist(),triangles=np.arange(len(n)*3).reshape(-1,3).tolist(),
                    texcoords=np.stack((u/REPEAT,1-v/REPEAT),axis=2).reshape(-1,2).tolist())


if __name__=='__main__':create()
