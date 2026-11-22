"""Original granular facing for the rough-faced radial masonry; uses no photographs."""
from pathlib import Path
from PIL import Image
import numpy as np
r=np.random.default_rng(449);n=256
def band(d):
    a=r.normal(128,23,(d,d)).clip(0,255).astype('uint8')
    return (np.asarray(Image.fromarray(a).resize((n,n),Image.Resampling.BICUBIC),dtype=float)-128.)/23.
grain=band(5)*6+band(25)*4+band(100)*9+r.normal(0,10,(n,n))
xx,yy=np.meshgrid(np.arange(n),np.arange(n));seams=(np.abs(np.sin(xx*.049+yy*.079+band(10)*.28))<.047)*-17
light=(r.random((n,n))<.04)*18
rgb=np.array([114,85,63])+((grain+seams+light)[:,:,None]*[1,.92,.78])
Image.fromarray(np.clip(rgb,0,255).astype('uint8')).save(Path(__file__).with_name('rough-stone.png'),optimize=True)
