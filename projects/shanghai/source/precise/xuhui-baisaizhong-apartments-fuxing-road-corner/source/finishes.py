"""Small, repeatable plaster, terrazzo and clay materials drawn from component colour observations."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter

HERE=Path(__file__).resolve().parent

def surface(path,base,kind):
    rng=np.random.default_rng({'plaster':1934,'terrazzo':1929,'clay':2019}[kind]);size=384
    coarse=Image.fromarray(np.uint8(rng.integers(63,190,(48,48)))).resize((size,size),Image.Resampling.BICUBIC)
    tone=(np.asarray(coarse,dtype=float)-128)*.055+rng.normal(0,1.7,(size,size))
    if kind=='terrazzo':
        tone=rng.normal(0,6,(size,size))
        for shade,threshold in [(-22,.066),(24,.079)]:
            mask=rng.random((size,size))<threshold
            tone+=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)),float)/255*shade
    if kind=='clay':
        y,x=np.indices((size,size))
        pitch=48
        tube=(x+24*(y//64%2))%pitch
        tone+=4.5*np.cos(2*np.pi*tube/pitch)-7*np.exp(-((tube-3)/3.5)**2)
        tone-=11*np.exp(-((y%64-2)/2.)**2)
    a=np.asarray(base)[None,None,:]+tone[:,:,None]
    Image.fromarray(np.clip(a,0,255).astype('uint8')).save(path,optimize=True)

def make():
    for filename,rgb,kind in [('original-stucco.png',(199,190,165),'plaster'),('stair-terrazzo.png',(126,125,117),'terrazzo'),('aged-red-roof.png',(111,96,83),'clay')]:
        surface(HERE/filename,rgb,kind)

if __name__=='__main__':make()
