"""Original running-bond grey brickwork and metric UVs on the two street fronts."""
from pathlib import Path
import numpy as np
from PIL import Image

TEXTURE=Path(__file__).with_name('young-allen-grey-brick.png')
BRICK='Young Allen grey facing brick'
REPEAT_W=1.77
REPEAT_H=.61


def create():
    rng=np.random.default_rng(192304007)
    w,h=384,144
    yy,xx=np.indices((h,w));field=np.empty((h,w,3))
    for j in range(8):
        for c in range(8):
            tile=(np.arange(48)+c*48-(j%2)*24)%w
            # Grey-buff faces and pale joints visible in Fayhoo’s street photograph.
            value=rng.normal(0,7)+(-12 if rng.random()<.21 else 0)
            field[j*18:(j+1)*18,tile,:]=np.array([127,124,111])+value+rng.normal(0,1.9,3)
    bx=(xx+(yy//18%2)*24)%48;by=yy%18
    field[(bx<=1)|(by<=1)]=[170,162,146]
    field[(bx==2)|(by==2)]*=.90
    field+=rng.normal(0,3.0,(h,w,1))+np.sin(yy*1.6)[:,:,None]*1.1
    Image.fromarray(np.clip(field,0,255).astype('uint8')).save(TEXTURE,optimize=True)


def apply_metric_uv(builder):
    for part in builder.parts:
        if part['material']!=BRICK:continue
        pts=np.asarray(part['vertices']);verts=[];uv=[];tris=[]
        for idx in part['triangles']:
            corners=pts[np.array(idx)]
            norm=np.cross(corners[1]-corners[0],corners[2]-corners[0])
            horiz=np.hypot(norm[0],norm[1])
            if horiz>abs(norm[2]):
                # All vertical street orientations retain the same brick size.
                tangent=np.array([-norm[1],norm[0]])/horiz
                if tangent[np.argmax(abs(tangent))]<0:tangent*=-1
                u=corners[:,:2]@tangent;v=corners[:,2]
            else:u=corners[:,0];v=corners[:,1]
            start=len(verts);verts.extend(corners.tolist())
            uv.extend(zip((u/REPEAT_W).tolist(),(1-v/REPEAT_H).tolist()));tris.append((start,start+1,start+2))
        part.update(vertices=verts,triangles=tris,texcoords=uv)


if __name__=='__main__':create()
