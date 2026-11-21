"""Original limewashed masonry with shallow bed joints and restrained street weathering."""
from pathlib import Path
from random import Random
from math import sin,pi
CARVED='Jinling warm lime finish'
IMAGE=Path(__file__).with_name('limewashed-masonry.png')
WEST=-1.
WALL_SPAN=30.
WALL_HEIGHT=26.

def uv(point):
    x,y,z=point
    return ((x+y-WEST)/WALL_SPAN,1.-(z+.15)/WALL_HEIGHT)

def generate():
    from PIL import Image,ImageFilter
    import numpy as np
    rng=Random(19120608)
    w,h=960,768
    coarse=np.array([rng.randrange(68,181)for _ in range(24*20)],dtype=np.uint8).reshape(20,24)
    low=Image.fromarray(coarse).resize((w,h),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    grain=np.random.default_rng(6081912).normal(0,.80,(h,w))
    xx=(np.arange(w)+.5)/w*WALL_SPAN+WEST
    zz=(1.-(np.arange(h)+.5)/h)*WALL_HEIGHT-.15
    mottled=(np.asarray(low,dtype=float)-124)/15.+grain
    # Thin joints in the pale stone facing; street pictures show longer
    # horizontal courses, with joints staggered and sometimes limewashed out.
    row=np.floor(zz/.56).astype(int)
    at_edge=np.minimum((zz%.56),.56-(zz%.56))<.016
    xoffset=xx[None,:]+(row[:,None]%2)*.61
    short=np.minimum(xoffset%1.22,1.22-(xoffset%1.22))<.011
    variation=mottled-7.8*at_edge[:,None]-3.5*short
    rgb=np.stack([c+variation for c in (205,201,188)],axis=-1).clip(0,255).astype('uint8')
    Image.fromarray(rgb).save(IMAGE,optimize=True)

def apply(builder):
    if not IMAGE.exists():generate()
    builder.palette[CARVED]={'color':[1.,1.,1.],'metallic':0.,'roughness':.90,'texture':str(IMAGE)}
    for part in builder.parts:
        if part['material']!=CARVED:continue
        part['texcoords']=[uv(v)for v in part['vertices']]
        assert all(0<=u<=1 and 0<=v<=1 for u,v in part['texcoords']),part['label']

if __name__=='__main__':generate()
