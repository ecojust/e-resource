"""Generate original mineral grain and irregular blue-grey/brown stone variation."""
from pathlib import Path
import numpy as np
from PIL import Image
rng=np.random.default_rng(185517)
width,height=768,1024
def field(w,h):
    coarse=Image.fromarray(np.clip(126.+rng.normal(0,33,(h,w)),0,255).astype("uint8"))
    return (np.asarray(coarse.resize((width,height),Image.Resampling.BICUBIC),float)-126.)/33.
low=field(28,38);mid=field(118,162);grain=rng.normal(0,1,(height,width))
gray=low*3.8+mid*2.4+grain*3.4
flecks=rng.random((height,width));gray+=np.where(flecks>.984,19.,np.where(flecks<.011,-15.,0.))
image=np.stack([94.+gray,82.+gray,74.+gray+.8*mid],axis=2)
Image.fromarray(np.clip(image,0,255).astype("uint8")).save(Path(__file__).with_name("russell-weathered-stone.png"),optimize=True)
