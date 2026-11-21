"""Procedural mottling for the polished brown stone seen below the Society emblem."""
from pathlib import Path
import numpy as np

PERIOD=.71
SHAFT='Warm stone shaft'


def uv(x,y,z,axis):
    return (y if axis==0 else x)/PERIOD,(y if axis==2 else z)/PERIOD


def shaft(b,cx,half,top,name):
    x0,x1=cx-half,cx+half
    y0,y1=-half,half
    corners=[(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0),
             (x0,y0,top),(x1,y0,top),(x1,y1,top),(x0,y1,top)]
    for axis,ids in [(2,[0,3,2,1]),(2,[4,5,6,7]),(1,[0,1,5,4]),(0,[1,2,6,5]),(1,[2,3,7,6]),(0,[3,0,4,7])]:
        verts=[corners[i]for i in ids]
        b.add(verts,[(0,1,2,3)],SHAFT,name+' square stone shaft')
        # The embedded PNG uses glTF's top-left origin. Blender uses its lower-left origin.
        native_uvs = [uv(*point, axis) for point in verts]
        b.parts[-1]['texcoords'] = [(u, 1 - v) for u, v in native_uvs]


def create():
    from PIL import Image
    rng=np.random.default_rng(19310101)
    size=256
    y,x=np.mgrid[:size,:size]*2*np.pi/size
    warm=np.array([187,158,130],float)
    cloud=.9*np.sin(2*x+y)+1.6*np.cos(x-2*y+.45*np.cos(3*x))+1.4*np.sin(3*x+4*y)
    cracks=np.abs(np.sin(x-2*y+.46*np.sin(2*x+y)+.24*np.sin(5*x-4*y)))
    thin=np.exp(-cracks*62)*.53
    dust=rng.normal(0,2.8,(size,size))
    chip=rng.uniform(size=(size,size));dust+=np.where(chip<.075,-10,0)+np.where(chip>.96,11,0)
    rgb=warm+cloud[...,None]+dust[...,None]-thin[...,None]*np.array([21,18,13])
    Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).save(Path(__file__).with_name('hall-stone.png'),optimize=True)


if __name__=='__main__':create()
