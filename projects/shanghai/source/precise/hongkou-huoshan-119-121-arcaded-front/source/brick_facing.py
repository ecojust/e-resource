"""Metric masonry for 119–121 Huoshan Road, using eight courses of original brickwork."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
TEXTURE=Path(__file__).with_name('huoshan-grey-brick.png')
CAST='Huoshan variegated grey brickwork'
REPEAT_X,REPEAT_Z=1.08,.60


def create():
    n=256
    rng=np.random.default_rng(1910119121)
    y,x=np.mgrid[:n,:n]
    course=np.floor_divide(y,32)
    vertical_noise=gaussian_filter(rng.normal(size=(n,n)),1.6,mode='wrap')*1.9
    horizontal_noise=gaussian_filter(rng.normal(size=(n,n)),1.3,mode='wrap')*1.7
    xn=(x+horizontal_noise+32*(course%2))%n
    lengths=np.where(course%4==3,32.,64.)
    piece=(xn//lengths).astype(int)
    vx=xn%lengths
    zy=(y+vertical_noise)%32
    edge=np.minimum(np.minimum(vx,lengths-vx)*1.43,np.minimum(zy,32-zy))
    mix=np.clip((edge-1.25)/1.75,0,1)
    tone=rng.uniform(-15.,13.,(8,8))[course,piece]
    chrom=rng.uniform(-4.,5.,(8,8))[course,piece]
    low=gaussian_filter(rng.normal(size=(n,n)),4.8,mode='wrap')
    pocks=rng.random((n,n))
    rough=rng.normal(0,3.5,(n,n))+np.where(pocks<.024,-10,0)+np.where(pocks>.989,10,0)
    body=111.+tone+16*low+rough
    brick=np.stack([body+5.5+chrom,body+3.5,body-.4-chrom*.3],axis=-1)
    mortar=145.+rough*.75+8*low
    joint=np.stack([mortar+5,mortar+1,mortar-6],axis=-1)
    light=np.where((zy<4)&(mix>.1),-4.,np.where((zy>26)&(mix>.1),3.,0.))
    rgb=joint*(1.-mix[:,:,None])+brick*mix[:,:,None]+light[:,:,None]
    Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).save(TEXTURE,optimize=True)


def apply_metric_uv(builder):
    for part in builder.parts:
        if part['material']!=CAST:continue
        source=np.asarray(part['vertices'],dtype=np.float32).astype(float);indices=np.asarray(part['triangles'])
        corners=source[indices];vectors=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0])
        horizontal=np.linalg.norm(vectors[:,:2],axis=1);vertical=horizontal>abs(vectors[:,2])
        tangent=np.column_stack([-vectors[:,1],vectors[:,0]])/np.maximum(horizontal[:,None],1e-16)
        flip=tangent[np.arange(len(vectors)),np.argmax(abs(tangent),axis=1)]<0;tangent[flip]*=-1
        u=np.where(vertical[:,None],np.einsum('nji,ni->nj',corners[:,:,:2],tangent),corners[:,:,0])
        v=np.where(vertical[:,None],corners[:,:,2],corners[:,:,1])
        array=np.stack([u/REPEAT_X,1-v/REPEAT_Z],axis=2)
        part.update(vertices=corners.reshape(-1,3).tolist(),triangles=np.arange(len(indices)*3).reshape(-1,3).tolist(),texcoords=array.reshape(-1,2).tolist())


if __name__=='__main__':create()
