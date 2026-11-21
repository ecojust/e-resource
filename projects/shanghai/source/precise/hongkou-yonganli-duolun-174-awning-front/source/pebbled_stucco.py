"""Original mottled cement matrix and small exposed grains. The sample repeats in physical metres."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
TEXTURE=Path(__file__).with_name('yonganli-grey-stucco.png')
CAST='Yonganli pebbled stucco'
REPEAT=1.29


def create():
    n=256;rng=np.random.default_rng(19250174)
    def noise(sigma):
        v=gaussian_filter(rng.standard_normal((n,n)),sigma=sigma,mode='wrap')
        return (v-v.mean())/(v.std()+1.e-12)
    base=151.+2.0*noise(17)+1.8*noise(4.7)+3.1*noise(1.1)+4.6*rng.standard_normal((n,n))
    grit=rng.random((n,n))
    base+=np.where(grit<.018,-rng.uniform(5,30,(n,n)),np.where(grit>.974,rng.uniform(5,25,(n,n)),0.))
    c=np.stack([base+4.0,base+1.9,base-1.3],axis=-1)
    Image.fromarray(np.clip(c,0,255).astype('uint8')).save(TEXTURE,optimize=True)


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
