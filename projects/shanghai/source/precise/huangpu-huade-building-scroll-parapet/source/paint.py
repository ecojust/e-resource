"""Lightly washed street-facing limestone; original procedural mineral grain, repeating at .51 metre."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

from material_names import CREAM as CAST, REPEAT, TEXTURE
def create():
    noise=np.random.default_rng(6200720).standard_normal((160,160))
    grain=2.6*noise+7.2*gaussian_filter(noise,1.7,mode='wrap')+36*gaussian_filter(noise,8.,mode='wrap')
    rgb=np.array([209.,201.,183.])+grain[:,:,None]*np.array([1.,.98,.94])
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
