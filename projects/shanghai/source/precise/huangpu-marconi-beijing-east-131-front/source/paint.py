"""Running-bond grey brickwork drawn from the course proportions beside the 131 entrance."""
import numpy as np
from PIL import Image
from material_names import MATERIAL,TEXTURE,REPEAT_X,REPEAT_Z
def create():
    rng=np.random.default_rng(131072)
    tile=448
    y,x=np.indices((tile,tile));height=tile/32.;width=tile/8.
    row=np.floor(y/height).astype(int)
    shifted=(x+.5*width*(row%2))%tile
    u=shifted%width;v=y%height
    bricks=np.floor(shifted/width).astype(int)
    variance=rng.normal(0,3.0,(32,8))[row,bricks]
    grain=rng.normal(0,2.65,(tile,tile))
    joint=np.minimum(np.minimum(u,width-u)*REPEAT_X/tile,np.minimum(v,height-v)*REPEAT_Z/tile)
    coverage=np.clip((joint-.0033)/.0038,0,1)
    face=np.array([138,131,123])+variance[:,:,None]+grain[:,:,None]
    mortar=np.array([156,151,139])+grain[:,:,None]*.61
    im=mortar+(face-mortar)*coverage[:,:,None]
    Image.fromarray(im.clip(0,255).astype(np.uint8)).save(TEXTURE,optimize=True)
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
