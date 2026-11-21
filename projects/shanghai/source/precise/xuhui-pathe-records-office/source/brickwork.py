"""Original seamless red-brick courses for the Pathe office, with metric UV coordinates."""
from pathlib import Path
import numpy as np

BRICK='Pathe red stretchers'
REPEAT_X=1.02
REPEAT_Z=.52
def dominant_axis(normal):
    components=np.abs(normal)
    return int(np.flatnonzero(components>=max(components)*(1-1e-5))[0])
def uv(x,y,z,axis):
    return ((y if axis==0 else x)/REPEAT_X,(y if axis==2 else z)/REPEAT_Z)
def texture_coordinates(builder):
    for part in builder.parts:
        if part['material']!=BRICK:continue
        vertex=[];coords=[];indices=[];lookup={}
        for tri in part['triangles']:
            a,b,c=[np.array(part['vertices'][i])for i in tri];axis=dominant_axis(np.cross(b-a,c-a));face=[]
            for index in tri:
                key=(index,axis)
                if key not in lookup:
                    pos=part['vertices'][index];u,v=uv(*pos,axis)
                    lookup[key]=len(vertex);vertex.append(pos);coords.append([u,1-v])
                face.append(lookup[key])
            indices.append(face)
        part.update(vertices=vertex,texcoords=coords,triangles=indices)
def create():
    from PIL import Image,ImageDraw
    # Eight courses, four stretchers per course, with a few paired headers.
    rng=np.random.default_rng(1921811)
    width,height=512,256
    image=Image.new('RGB',(width,height),(131,115,102));d=ImageDraw.Draw(image)
    for row in range(8):
        offset=64*(row%2);left=offset;y=32*row
        for col in range(4):
            split=(row,col) in ((1,1),(2,3),(4,1),(7,2))
            for segment in ((64,64)if split else(128,)):
                tone=rng.integers(-10,11);color=tuple(int(t+tone)for t in (161,87,61))
                for shift in (-width,0,width):
                    x=left+shift
                    d.rectangle((x+1,y+1,x+segment-2,y+29),fill=color)
                    d.line((x+1,y+29,x+segment-2,y+29),fill=tuple(max(0,t-10)for t in color))
                left+=segment
    rgb=np.asarray(image).astype(float)
    rgb+=rng.normal(0,2.5,(height,width,1))
    Image.fromarray(rgb.clip(0,255).astype('uint8')).save(Path(__file__).with_name('pathe-red-brick.png'),optimize=True)
if __name__=='__main__':create()
