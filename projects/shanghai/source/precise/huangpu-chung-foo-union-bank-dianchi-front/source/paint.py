"""Generate original fine-grained stone and assign 1.52 metre planar UV repeats."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from material_names import MATERIAL,TEXTURE,REPEAT

def create():
    n=192
    grain=np.random.default_rng(1031922).normal(0,1.,(n,n))
    patches=gaussian_filter(grain,6.,mode='wrap')*27
    veins=gaussian_filter(grain,2.,mode='wrap')*5
    colour=np.array([197.,194.,187.])+(grain*3.8+patches+veins)[:,:,None]
    Image.fromarray(np.uint8(colour.clip(0,255))).save(TEXTURE,optimize=True)
def apply_metric_uv(builder):
    for part in builder.parts:
        if part['material']!=MATERIAL:continue
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
