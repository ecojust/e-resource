"""Paint a seamless running-bond surface in two original fired-clay palettes."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parent
PERIOD = (1.47, 0.864)  # six stretchers by twelve measured courses

def make(name, base, seed):
    rng = np.random.default_rng(seed)
    width, height = 768, 480
    row, column = np.indices((height, width))
    course = row // 40
    horizontal = (column + 64 * (course % 2)) % width
    block = horizontal // 128
    u = horizontal % 128
    v = row % 40
    variation = rng.normal(0, 4.0, (12,6))[course, block]
    fine = rng.normal(0, 4.1, (height,width))
    broad = gaussian_filter(rng.normal(0, 1., (height,width)), 7, mode='wrap')
    broad *= 2.6 / broad.std()
    distance = np.minimum(np.minimum(u, 127-u), np.minimum(v, 39-v))
    irregular = gaussian_filter(rng.normal(0, 1, (height,width)), 1.1, mode='wrap')
    brick = np.clip((distance - 1.0 - .8*irregular)/1.15,0,1)
    colour = np.array(base)[None,None,:] + (variation + fine + broad)[:,:,None]
    mortar = np.array([145,141,129])[None,None,:] + (fine*.61 + broad*.45)[:,:,None]
    image = colour*brick[:,:,None] + mortar*(1-brick[:,:,None])
    Image.fromarray(np.rint(np.clip(image,0,255)).astype('uint8')).save(ROOT/name,quality=91,subsampling=0)

if __name__ == '__main__':
    make('guiren-grey-brick.jpg',(111,112,104),63201)
    make('guiren-russet-brick.jpg',(135,68,50),63202)
