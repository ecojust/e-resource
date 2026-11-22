"""Generate tileable running bond at four brick lengths and twelve courses per 0.88-metre repeat."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from material_names import MATERIAL,TEXTURE,REPEAT

def create():
    n=192;v,u=np.indices((n,n));row=v//16;col=((u+24*(row%2))//48)%4
    rand=np.random.default_rng(1925105)
    grain=rand.normal(0.,4.,(n,n))
    warm=rand.normal(0.,5.,(12,4))[row,col]
    brick=np.array([153.,86.,67.])+(warm+grain+10*gaussian_filter(grain,2.,mode='wrap'))[:,:,None]*np.array([1,.78,.63])
    edge=(v%16<2)|((u+24*(row%2))%48<2)
    mortar=np.array([148.,126.,111.])+grain[:,:,None]*.7
    rgb=np.where(edge[:,:,None],mortar,brick)
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(TEXTURE,optimize=True)
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
