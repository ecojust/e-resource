"""Original procedural grey finish for the broad fields of the National Music School."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

TEXTURE=Path(__file__).with_name('historic-portico-plaster.png')
CAST='Music School archival plaster'
REPEAT=1.12

def create():
    noise=np.random.default_rng(19360117).standard_normal((160,160))
    grain=1.8*noise+9.5*gaussian_filter(noise,1.7,mode='wrap')+38*gaussian_filter(noise,8.,mode='wrap')
    rgb=np.array([202.,201.,197.])+grain[:,:,None]*np.array([1.,.99,.97])
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(TEXTURE,optimize=True)

def apply_metric_uv(builder):
    for part in builder.parts:
        if part['material']!=CAST:continue
        vertices=np.asarray(part['vertices'],dtype=np.float32).astype(float)
        corners=vertices[np.asarray(part['triangles'])]
        normals=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0])
        h=np.linalg.norm(normals[:,:2],axis=1)
        vertical=h>abs(normals[:,2])
        tangent=np.column_stack([-normals[:,1],normals[:,0]])/np.maximum(h[:,None],1.e-20)
        tangent[tangent[np.arange(len(tangent)),np.argmax(abs(tangent),axis=1)]<0]*=-1
        u=np.where(vertical[:,None],np.einsum('nvi,ni->nv',corners[:,:,:2],tangent),corners[:,:,0])
        v=np.where(vertical[:,None],corners[:,:,2],corners[:,:,1])
        part.update(vertices=corners.reshape(-1,3).tolist(),triangles=np.arange(len(corners)*3).reshape(-1,3).tolist(),
                    texcoords=np.stack((u/REPEAT,1-v/REPEAT),axis=2).reshape(-1,2).tolist())

if __name__=='__main__':create()
