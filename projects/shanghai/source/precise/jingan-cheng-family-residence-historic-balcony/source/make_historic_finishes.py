"""Draw tileable mineral finishes for the photograph's dark wall and pale window surrounds."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def finish(path,seed,rgb,grain,medium):
    rng=np.random.default_rng(seed)
    n=256
    a=rng.normal(size=(n,n));b=gaussian_filter(rng.normal(size=(n,n)),2.5,mode='wrap')
    b/=b.std();cloud=gaussian_filter(rng.normal(size=(n,n)),15.,mode='wrap');cloud/=cloud.std()
    light=grain*a+medium*b+2.3*cloud
    if grain>4:
        quartz=rng.random((n,n));light+=np.where(quartz>.969,22.,np.where(quartz<.018,-17.,0))
    values=np.uint8(np.clip(np.asarray(rgb)[None,None,:]+light[:,:,None],0,255))
    Image.fromarray(values).save(path,optimize=True)
if __name__=='__main__':
    here=Path(__file__).resolve().parent
    finish(here/'street-roughcast.png',295,(113,111,105),8.7,5.8)
    finish(here/'pale-stone.png',613,(199,196,185),3.4,2.9)
