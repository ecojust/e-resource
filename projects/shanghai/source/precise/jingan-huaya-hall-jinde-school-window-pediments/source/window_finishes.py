"""Original seamless mineral and painted-timber swatches for Huaya Hall."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def create(directory):
    directory=Path(directory)
    rng=np.random.default_rng(624)
    noise=rng.normal(size=(256,256))
    def normal(a):
        return (a-a.mean())/(a.std()+1e-8)
    grain=normal(gaussian_filter(noise,(.65,11),mode='wrap'))
    phase=normal(gaussian_filter(noise,(7,24),mode='wrap'))
    y,x=np.mgrid[:256,:256]
    ridges=np.sin(2*np.pi*y/13+.94*phase+.3*np.sin(2*np.pi*x/256))
    t=1.8*grain+1.0*ridges+1.7*normal(gaussian_filter(noise,8,mode='wrap'))+.65*noise
    s=2.0*noise+1.8*normal(gaussian_filter(noise,1.2,mode='wrap'))+2.5*normal(gaussian_filter(noise,9,mode='wrap'))
    for name,base,sig in [('huaya-painted-timber.jpg',(143,94,92),t),('huaya-cast-stone.jpg',(190,182,169),s)]:
        Image.fromarray(np.clip(np.array(base)[None,None,:]+sig[:,:,None],0,255).astype('uint8')).save(directory/name,quality=88,subsampling=0)
if __name__=='__main__':
    create(Path(__file__).parent)
