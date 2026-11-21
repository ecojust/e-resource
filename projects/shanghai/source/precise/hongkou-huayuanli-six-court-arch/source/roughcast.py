"""Original, tileable grey roughcast material made for the Huayuanli court wall."""
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
TEXTURE=Path(__file__).with_name('huayuanli-grey-roughcast.png')
CAST='Huayuanli grey roughcast'
REPEAT=.88


def create():
    n=256
    rng=np.random.default_rng(192714506)
    relief=np.zeros((n,n))
    y,x=np.mgrid[:n,:n]
    for _ in range(1210):
        cx,cy=rng.uniform(0,n,2)
        dx=(x-cx+n/2)%n-n/2
        dy=(y-cy+n/2)%n-n/2
        radius=rng.uniform(.7,3.0)
        footprint=(dx*dx+dy*dy)/(radius*radius)
        relief+=np.maximum(0.,1-footprint)**.85*rng.uniform(.55,1.1)
    body=gaussian_filter(rng.normal(0,1,(n,n)),4.8,mode='wrap')
    fine=rng.normal(0,1.9,(n,n))
    diffuse=182+11*body+1.55*fine+6.6*relief+42*(relief-np.roll(relief,1,axis=0))-33*(relief-np.roll(relief,1,axis=1))
    rgb=np.stack([diffuse+.2,diffuse+1.4,diffuse-5.4],axis=-1)
    Image.fromarray(np.clip(rgb,0,255).astype('uint8')).save(TEXTURE,optimize=True)


def apply_metric_uv(builder):
    for part in builder.parts:
        if part['material']!=CAST:continue
        # Use the actual FLOAT32 export coordinates when choosing the mapping
        # plane. A 45-degree bevel must select the same UV projection after decoding.
        source=np.asarray(part['vertices'],dtype=np.float32).astype(float)
        indices=np.asarray(part['triangles'])
        corners=source[indices];vec=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0])
        horiz=np.linalg.norm(vec[:,:2],axis=1);vertical=horiz>abs(vec[:,2])
        tangent=np.column_stack([-vec[:,1],vec[:,0]])/np.maximum(horiz[:,None],1e-16)
        sign=tangent[np.arange(len(vec)),np.argmax(abs(tangent),axis=1)]<0;tangent[sign]*=-1
        u=np.where(vertical[:,None],np.einsum('nji,ni->nj',corners[:,:,:2],tangent),corners[:,:,0])
        v=np.where(vertical[:,None],corners[:,:,2],corners[:,:,1])
        uv=np.stack([u/REPEAT,1-v/REPEAT],axis=2)
        part.update(vertices=corners.reshape(-1,3).tolist(),triangles=np.arange(len(indices)*3).reshape(-1,3).tolist(),texcoords=uv.reshape(-1,2).tolist())


if __name__=='__main__':create()
