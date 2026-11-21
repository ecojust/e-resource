"""Periodic mineral render used only on the photographed plaster walls."""
from pathlib import Path
import numpy as np

PLASTER='Pale ochre cement render'
PERIOD=.36
from stone_finish import STONE, PERIOD as GRANITE_PERIOD
FINISHES = {
    PLASTER: ('ochre-dragged-render.png', PERIOD, 'Jianguo mineral render', 'Jianguo render, 0.36 m'),
    STONE: ('dressed-grey-granite.png', GRANITE_PERIOD, 'Jianguo grey granite', 'Jianguo granite, 0.32 m'),
}

def dominant_axis(normal):
    v=np.abs(normal)
    return int(np.flatnonzero(v>=v.max()*(1-1e-5))[0])

def uv(x,y,z,axis,period=PERIOD):
    return ((y if axis==0 else x)/period,(y if axis==2 else z)/period)

def texture_coordinates(b):
    for part in b.parts:
        if part['material'] not in FINISHES:
            continue
        vertices=[];coords=[];faces=[];aliases={}
        for face in part['triangles']:
            a,c,d=[np.array(part['vertices'][i])for i in face]
            axis=dominant_axis(np.cross(c-a,d-a))
            new=[]
            for i in face:
                key=(axis,i)
                if key not in aliases:
                    xyz=part['vertices'][i];u,v=uv(*xyz,axis,FINISHES[part['material']][1])
                    aliases[key]=len(vertices);vertices.append(xyz);coords.append((u,1-v))
                new.append(aliases[key])
            faces.append(new)
        part.update(vertices=vertices,triangles=faces,texcoords=coords)

def create():
    from PIL import Image
    rng=np.random.default_rng(6021930)
    n=256;dust=rng.normal(0,1.7,(n,n))
    # The tiny dragged grains seen in the close view run down the cement face.
    grain=rng.random((n,n))<.075
    for d,shade in ((0,-5.0),(1,-2.2),(2,2.8)):
        dust+=np.roll(grain,d,axis=0)*shade
    tone=np.array([217,208,186],float)+dust[:,:,None]
    Image.fromarray(tone.clip(0,255).astype('uint8')).save(Path(__file__).with_name('ochre-dragged-render.png'),optimize=True)

if __name__=='__main__':
    create()
