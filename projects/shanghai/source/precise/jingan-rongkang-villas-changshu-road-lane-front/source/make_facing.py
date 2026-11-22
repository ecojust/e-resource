"""Create the original roughcast and aggregate material for Rongkang Villas."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter

def make(destination):
    rng=np.random.default_rng(640061)
    n=208
    broad=np.asarray(Image.fromarray(rng.integers(70,183,(16,16),dtype='uint8')).resize((n,n),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(3)),float)-127
    for name,rgb,spread in [('rongkang-grey-roughcast.jpg',(174,171,153),1.),('rongkang-paved-stone.jpg',(153,150,139),.72)]:
        grains=rng.normal(0,5.8,size=(n,n))+broad*.12
        bright=rng.uniform(size=(n,n));grains[bright>.965]+=12;grains[bright<.035]-=15
        tint=rng.normal(0,.85,(n,n,3))
        col=np.round(np.clip(np.array(rgb)[None,None,:]+grains[:,:,None]*spread+tint,0,255)).astype('uint8')
        Image.fromarray(col).save(destination/name,quality=89,subsampling=0)
    # A neutral variation in the brightness of the glass, independent of every reference photograph.
    ys,xs=np.mgrid[0:n,0:n]/n
    wave=9*np.cos(2*np.pi*(xs+.18*np.sin(2*np.pi*ys)))+6*np.sin(2*np.pi*(ys+.21*xs))
    sheen=219+wave+8*np.maximum(0,np.cos(2*np.pi*(xs*.99+ys*.94)))**6
    glass=np.stack([sheen-1.9,sheen,sheen+1.5],axis=-1)+rng.normal(0,1.,(n,n,3))
    Image.fromarray(np.clip(glass,0,255).astype('uint8')).save(destination/'rongkang-shop-glass.jpg',quality=90,subsampling=0)
if __name__=='__main__':make(Path(__file__).resolve().parent)
