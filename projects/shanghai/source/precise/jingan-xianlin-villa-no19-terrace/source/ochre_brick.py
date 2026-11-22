"""Original ochre running bond on the exposed end and side of the corner."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from material_names import TEXTURE

def make_texture(path=TEXTURE):
    if path.is_file():
        return
    rng=np.random.default_rng(47919)
    w,h=384,384
    im=Image.new('RGB',(w,h),(108,92,72))
    painter=ImageDraw.Draw(im)
    for row in range(24):
        y=row*16
        for col in range(-1,9):
            x=col*48+(row%2)*24
            level=rng.normal(0,8)
            rgb=np.round(np.array([153,116,82])+level*np.array([1,.82,.65])+rng.normal(0,2.2,3)).astype('uint8')
            painter.rectangle((x+1,y+1,x+46,y+14),fill=tuple(rgb))
    rgb=np.asarray(im,dtype=float)+rng.normal(0,3.2,(h,w,1))
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).quantize(144).save(path)
def apply_uv(part):
    xyz=np.asarray(part['vertices'])
    vertices=[]; uv=[]; triangles=[]; lookup={}
    for tri in part['triangles']:
        p=xyz[list(tri)]
        normal=np.abs(np.cross(p[1]-p[0],p[2]-p[0]))
        axis=int(normal.argmax())
        uvw=np.column_stack((p[:,1 if axis==0 else 0]/1.81,-
                             p[:,1 if axis==2 else 2]/(1.81 if axis==2 else 1.668)))
        indices=[]
        for idx,coord in zip(tri,uvw):
            key=(idx,*np.round(coord,7))
            if key not in lookup:
                lookup[key]=len(vertices);vertices.append(tuple(xyz[idx]));uv.append(tuple(coord))
            indices.append(lookup[key])
        triangles.append(indices)
    part.update(vertices=vertices,texcoords=uv,triangles=triangles)
