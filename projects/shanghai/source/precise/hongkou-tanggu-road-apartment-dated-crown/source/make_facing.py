"""A seamless procedural grain for the warm ochre exterior."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
rng=np.random.default_rng(1936)
size=320
def noise(sigma):
    field=gaussian_filter(rng.normal(size=(size,size)),sigma,mode='wrap')
    return field/field.std()
speck=noise(.48)*2.75+noise(2.9)*1.65+noise(11.5)*1.5+noise(34)*1.0
base=np.array([173,113,79],float)
colour=base+speck[:,:,None]*np.array([1.0,.94,.72])+rng.normal(0,.58,(size,size,3))
Image.fromarray(np.clip(colour,0,255).astype('uint8')).save(Path(__file__).with_name('ochre-facing.jpg'),quality=89,subsampling=0)
