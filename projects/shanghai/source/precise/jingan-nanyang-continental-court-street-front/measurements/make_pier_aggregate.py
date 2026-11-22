"""Create an original, seamless material for the visible water-washed surface."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from pathlib import Path

def run(out):
    rng=np.random.default_rng(620)
    noise=rng.normal(size=(240,240))
    coarse=gaussian_filter(noise,2.6,mode='wrap')
    grain=gaussian_filter(noise,.42,mode='wrap')
    matrix=234+13*grain+11*coarse
    seeds=rng.uniform(size=noise.shape)
    matrix+=np.where(seeds>.925,7.,np.where(seeds<.078,-10.,0.))
    # The tile represents about 0.32 m, with distinct sub-centimetre grains in a pale matrix.
    rgb=np.uint8(np.clip(np.stack([matrix+1,matrix,matrix-1.1],axis=2),0,255))
    Image.fromarray(rgb).save(out,quality=94,subsampling=0,optimize=True)
if __name__=='__main__':run(Path(__file__).resolve().parents[1]/'source/pier-aggregate.jpg')
