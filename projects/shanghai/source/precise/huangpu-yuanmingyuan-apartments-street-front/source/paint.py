"""Original wrapping brick texture with eight stretchers and 28 courses per tile."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from material_names import MATERIAL,TEXTURE,REPEAT_X,REPEAT_Z

def create():
    size=448
    rng=np.random.default_rng(2014115)
    y,x=np.mgrid[:size,:size]
    row=y//16
    offset=(row%2)*28
    column=((x+offset)//56)%8
    phase_x=(x+offset)%56
    phase_y=y%16
    stain=gaussian_filter(rng.normal(size=(size,size)),4,mode='wrap')*18
    grain=rng.normal(0,2.1,(size,size))
    variation=rng.uniform(-9,9,(28,8))[row,column]
    body=np.array([161.,89.,74.])+(variation+stain+grain)[:,:,None]
    shadow=(phase_y==2)|(phase_x==2)
    body[shadow]*=.93
    bed=(phase_y<2)|(phase_x<2)
    body[bed]=np.array([141.,108.,96.])+grain[bed,None]
    Image.fromarray(body.clip(0,255).astype('uint8')).save(TEXTURE,optimize=True)

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
