"""Build lime render and stretcher-bond brick finishes. One metre equals one model unit."""
from pathlib import Path
import numpy as np
from PIL import Image
def generate():
    here=Path(__file__).resolve().parent;rng=np.random.default_rng(77)
    grain=rng.normal(0,2.2,(192,192,1));warm=np.asarray([219,212,190])+grain
    Image.fromarray(np.uint8(np.clip(warm,0,255))).save(here/'cream-lime.png',optimize=True)
    iy,ix=np.indices((480,480));row=iy//24;vjoint=(ix+(row%2)*48)%96
    mortar=(iy%24<2)|(vjoint<2)
    colour=np.asarray([162,102,70])+rng.normal(0,4.2,(480,480,1))
    change=rng.normal(0,5,(20,6))[row,((ix+(row%2)*48)//96)%5]
    colour+=change[:,:,None];colour[mortar]=[180,159,130]
    Image.fromarray(np.uint8(np.clip(colour,0,255))).save(here/'warm-russet-brick.png',optimize=True)
if __name__=='__main__':generate()
