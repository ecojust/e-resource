"""Generate an original mineral-aggregate swatch from measured tonal ranges."""
from pathlib import Path
import argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy.ndimage import gaussian_filter


def render(out):
    n=448
    rng=np.random.default_rng(19220627)
    noise=rng.normal(size=(n,n))
    field=gaussian_filter(noise,10.,mode='wrap');field=field/field.std()*2.8
    fine=gaussian_filter(noise,.57,mode='wrap');fine=fine/fine.std()*7.5
    base=np.array([151,152,141])+np.expand_dims(fine+field,-1)
    im=Image.fromarray(np.uint8(np.clip(base,0,255)),'RGB')
    # Irregular mineral chips. This is a new swatch with no sampled source pixels.
    draw=ImageDraw.Draw(im,'RGBA')
    for _ in range(3700):
        x,y=rng.uniform(0,n,2);r=rng.uniform(.48,2.65)
        angles=np.sort(rng.uniform(0,2*np.pi,5));radii=r*rng.uniform(.62,1.2,5)
        xy=list(zip(x+radii*np.cos(angles),y+radii*np.sin(angles)))
        light=rng.random()<.75
        c=rng.integers(173,218) if light else rng.integers(83,128)
        draw.polygon(xy,fill=(int(c+1),int(c),int(c-8),int(rng.integers(105,201))))
    im.filter(ImageFilter.GaussianBlur(.23)).save(out,quality=88,optimize=True)

def render_hood(out):
    # Independent fine stone grain and low-contrast runoff, without copying a photograph.
    h,w=176,512
    rng=np.random.default_rng(612188)
    fine=gaussian_filter(rng.normal(size=(h,w)),(.52,.5))
    streaks=gaussian_filter(rng.normal(size=(h,w)),(25.,1.25))
    tones=4.2*fine/fine.std()+3.1*streaks/streaks.std()
    face=np.array([150.,157.,159.])+tones[:,:,None]
    Image.fromarray(np.uint8(np.clip(face,0,255))).save(out,quality=88,optimize=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--hood',action='store_true')
    a=p.parse_args();(render_hood if a.hood else render)(a.output)
