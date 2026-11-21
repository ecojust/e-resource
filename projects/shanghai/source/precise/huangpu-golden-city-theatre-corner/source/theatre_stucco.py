"""Original warm mineral finish for the documented curved masonry."""
from math import atan2
from pathlib import Path
from hashlib import sha256
import json

HERE=Path(__file__).parent
IMAGE=HERE/'cream-mineral-finish.png'
MATERIAL='Theatre warm cream stucco'
SIZE=(816,896)
SPAN=21.
HEIGHT=26.


def uv(point):
    x,y,z=point
    return (.5+atan2(x,y)*8./SPAN,1.-(z+.12)/HEIGHT)


def generate():
    import numpy as np
    from PIL import Image,ImageFilter
    rng=np.random.default_rng(19340201)
    w,h=SIZE
    low=Image.fromarray(rng.integers(60,171,(33,31),dtype=np.uint8)).resize(SIZE,Image.Resampling.BICUBIC)
    broad=(np.asarray(low.filter(ImageFilter.GaussianBlur(3))).astype(float)-113.)*.039
    fleck=rng.normal(.0,.93,(h,w))
    z=(1.-(np.arange(h)+.5)/h)*HEIGHT-.12
    # In the published December 2024 view the long horizontal tooling joints
    # remain visible across the curved wall even where there is no window.
    phase=np.mod(z-.36,1.215)
    joint=np.maximum(0,1-np.minimum(phase,1.215-phase)/.030)[:,None]
    weather=broad+fleck-12.7*joint
    rgb=np.stack([c+weather for c in (210,202,181)],axis=-1).clip(0,255).astype(np.uint8)
    Image.fromarray(rgb).save(IMAGE,optimize=True)


def apply(builder):
    if not IMAGE.exists():generate()
    builder.palette[MATERIAL]=dict(color=[1.,1.,1.],roughness=.86,metallic=0.,texture=str(IMAGE))
    for part in builder.parts:
        if part['material']!=MATERIAL:continue
        part['texcoords']=[uv(v)for v in part['vertices']]
        assert all(0<=u<=1 and 0<=v<=1 for u,v in part['texcoords'])


if __name__=='__main__':
    generate()
