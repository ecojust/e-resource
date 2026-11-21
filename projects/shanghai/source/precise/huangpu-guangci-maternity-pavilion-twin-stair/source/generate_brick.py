"""Draw a seamless original running bond from rows, headers and fine aggregate."""
from pathlib import Path
import numpy as np
from PIL import Image

def make():
    rng=np.random.default_rng(192225)
    w,h=384,224
    y,x=np.mgrid[0:h,0:w]
    course=y//28
    # The corner joints wrap exactly in adjacent repeats.
    shifted=(x+(course%2)*48)%w
    index=course*4+shifted//96
    shift=rng.normal(0,7,(32,1))[index]
    grain=rng.normal(0,3.4,(h,w,1))
    red=np.array([165,96,76])[None,None,:]+shift+grain
    distance=np.minimum.reduce((y%28,27-y%28,shifted%96,95-shifted%96))
    alpha=np.clip((distance-.80)/2.15,0,1)[...,None]
    mortar=np.array([164,141,117])[None,None,:]+.50*grain
    brick=mortar*(1-alpha)+red*alpha
    img=Image.fromarray(np.clip(brick,0,255).astype('uint8'))
    img.save(Path(__file__).with_name('brick-facing.png'),optimize=True)

if __name__=='__main__':make()
