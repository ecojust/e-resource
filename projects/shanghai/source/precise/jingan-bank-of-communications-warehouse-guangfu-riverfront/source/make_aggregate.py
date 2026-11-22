"""Tileable procedural washed aggregate. No source photograph is sampled."""
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_filter

def make(directory):
    rng = np.random.default_rng(1934195)
    size = 240
    small = rng.normal(0,1,(size,size))
    broad = gaussian_filter(rng.normal(0,1,(size,size)), 9.,mode='wrap')
    broad /= broad.std()
    # Different mineral particles are visible as small flecks in the washed cement.
    grain = 3.8*small + 2.8*broad
    flecks = rng.random((size,size))
    grain += np.where(flecks<.057,-13.,np.where(flecks>.961,12.,0.))
    tint = rng.normal(0,.75,(size,size,3))
    color = np.clip(np.array([171,168,159])+grain[:,:,None]+tint,0,255).astype('uint8')
    Image.fromarray(color).save(directory/'guangfu-washed-aggregate.jpg',quality=91,subsampling=0)

if __name__=='__main__':
    make(Path(__file__).resolve().parent)
