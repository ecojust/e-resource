"""Original, independently generated plaster-grain texture for the historic balcony."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def generate(path):
    rng=np.random.default_rng(19221927)
    size=(256,512)
    field=rng.standard_normal(size)
    fine=gaussian_filter(rng.standard_normal(size),.8)
    broad=gaussian_filter(rng.standard_normal(size),6)
    fine/=np.std(fine)
    broad/=np.std(broad)
    shade=field*2.0 + fine*2.0 + broad*1.7
    # Tiny exposed grains, scattered independently of the reference images.
    grains=rng.random(size)
    shade-=6.5*(grains<.037)
    shade+=5.*(grains>.973)
    rgb=np.array([183.,183.,170.])+shade[:,:,None]*[1.,.94,.87]
    Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8')).save(path,quality=90,optimize=True)

if __name__=='__main__':
    generate(Path(__file__).parent/'historic-balcony-plaster.jpg')
