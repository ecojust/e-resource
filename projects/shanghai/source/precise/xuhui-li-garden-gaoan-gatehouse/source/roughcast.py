"""Periodic mineral render used only on the photographed plaster walls."""
from pathlib import Path
import numpy as np

PLASTER='Ivory roughcast stucco'
PERIOD=.42

def dominant_axis(normal):
    v=np.abs(normal)
    return int(np.flatnonzero(v>=v.max()*(1-1e-5))[0])

def uv(x,y,z,axis):
    return ((y if axis==0 else x)/PERIOD,(y if axis==2 else z)/PERIOD)

def texture_coordinates(b):
    for part in b.parts:
        if part['material']!=PLASTER:
            continue
        vertices=[];coords=[];faces=[];aliases={}
        for face in part['triangles']:
            a,c,d=[np.array(part['vertices'][i])for i in face]
            axis=dominant_axis(np.cross(c-a,d-a))
            new=[]
            for i in face:
                key=(axis,i)
                if key not in aliases:
                    xyz=part['vertices'][i];u,v=uv(*xyz,axis)
                    aliases[key]=len(vertices);vertices.append(xyz);coords.append((u,1-v))
                new.append(aliases[key])
            faces.append(new)
        part.update(vertices=vertices,triangles=faces,texcoords=coords)

def create():
    from PIL import Image
    rng=np.random.default_rng(631930)
    n=256
    sand=rng.normal(0.,2.,(n,n))
    chips=rng.random((n,n)) < .055
    for dx,dy,a in ((0,0,11),(0,1,5),(1,1,3),(0,-1,-10),(1,-1,-5),(-1,0,-3)):
        sand+=np.roll(chips,(dy,dx),(0,1))*a
    tone=np.array([222,217,203],float)+sand[:,:,None]
    Image.fromarray(tone.clip(0,255).astype('uint8')).save(Path(__file__).with_name('ivory-roughcast.png'),optimize=True)

if __name__=='__main__':
    create()
