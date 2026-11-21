"""Make the original ochre lime roughcast used across the cut street facade."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
rng=np.random.default_rng(441)
size=512
def cloud(n):
    noise=rng.normal(128,31,(n,n)).clip(0,255).astype('uint8')
    return (np.asarray(Image.fromarray(noise).resize((size,size),Image.Resampling.BICUBIC),dtype=float)-128)/30
yy,xx=np.mgrid[:size,:size]
grit=rng.normal(0,3.0,(size,size))
weather=2.3*cloud(8)+1.0*cloud(50)+grit+1.5*np.sin(yy*.015+xx*.004)
# Sparse lime grains and darker aggregate keep the plaster tactile in close view.
weather+=np.where(rng.uniform(size=(size,size))>.977,-7,0)
rgb=np.array((201,170,126))[None,None,:]+weather[:,:,None]
Image.fromarray(np.clip(rgb,0,255).astype('uint8')).save(Path(__file__).with_name('ochre-roughcast.png'),optimize=True)
