"""Original mineral-grain finish for the street wall in the WQL photograph."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from material_names import MATERIAL,TEXTURE,REPEAT_X,REPEAT_Z

def create():
    rng=np.random.default_rng(1952018)
    size=448
    grain=rng.normal(0,7.5,(size,size))
    clusters=gaussian_filter(rng.normal(size=(size,size)),1.1,mode='wrap')*18.
    broad=gaussian_filter(rng.normal(size=(size,size)),9.,mode='wrap')*26.
    flecks=rng.uniform(size=(size,size))
    tone=grain+clusters+broad+np.where(flecks<.045,-23.,np.where(flecks>.95,15.,0.))
    rgb=np.array([158.,145.,122.])+tone[:,:,None]
    Image.fromarray(rgb.clip(0,255).astype('uint8')).save(TEXTURE,optimize=True)

def apply_metric_uv(builder):
    for part in builder.parts:
        if part['material']!=MATERIAL:continue
        verts=np.asarray(part['vertices'],dtype=np.float32).astype(float)
        corners=verts[np.asarray(part['triangles'])]
        normal=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0])
        length=np.linalg.norm(normal[:,:2],axis=1)
        vertical=length>np.abs(normal[:,2])
        tangent=np.column_stack((-normal[:,1],normal[:,0]))/np.maximum(length[:,None],1.e-20)
        tangent[tangent[np.arange(len(tangent)),np.argmax(abs(tangent),axis=1)]<0]*=-1
        u=np.where(vertical[:,None],np.einsum('nvi,ni->nv',corners[:,:,:2],tangent),corners[:,:,0])
        v=np.where(vertical[:,None],corners[:,:,2],corners[:,:,1])
        part.update(vertices=corners.reshape(-1,3).tolist(),triangles=np.arange(len(corners)*3).reshape(-1,3).tolist(),
                    texcoords=np.stack((u/REPEAT_X,1-v/REPEAT_Z),axis=2).reshape(-1,2).tolist())
if __name__=='__main__':create()
