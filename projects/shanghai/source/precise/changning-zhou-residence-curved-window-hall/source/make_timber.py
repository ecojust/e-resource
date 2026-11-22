"""Generate an original vertically grained, warm stained timber map."""
from pathlib import Path
import numpy as np
from PIL import Image
h,w=256,128
rng=np.random.default_rng(1015);y,x=np.mgrid[:h,:w]
grain=3.2*np.cos(.4*x+.14*np.sin(y/78))+2.2*np.sin(x*.1+.22*np.sin(y/51))+rng.normal(0,1.2,(h,w))
mat=np.array([137,84,57])[None,None,:]+grain[:,:,None]
Image.fromarray(np.uint8(np.clip(mat,0,255))).save(Path(__file__).with_name('stained-timber.png'))
