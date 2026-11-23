"""Produce repeatable wall finishes. Rear-joint scale is set against the registered upper wall."""
from pathlib import Path
import numpy as np
from PIL import Image
def make():
    here=Path(__file__).resolve().parent;rng=np.random.default_rng(196)
    grain=rng.normal(0,2.2,(192,192,1))
    Image.fromarray(np.uint8(np.clip(np.asarray([167,169,152])+grain,0,255))).save(here/'street-grey-plaster.png',optimize=True)
    y,x=np.indices((384,384));row=y//96
    seam=np.minimum(y%96,96-y%96);end=(x+(row%2)*96)%192
    joints=(seam<1.65)|(end<2)
    soft=(seam<3)|(end<3)
    noise=rng.normal(0,2.5,(384,384,1))
    field=np.asarray([198,198,182])+noise-6*soft[:,:,None]-14*joints[:,:,None]
    Image.fromarray(np.uint8(np.clip(field,0,255))).save(here/'rear-ruled-plaster.png',optimize=True)
if __name__=='__main__':make()
