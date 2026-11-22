"""Generate photographic-pixel-free wood and weathered stoop material swatches for No.51."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).resolve().parent

def write_finishes():
    rng=np.random.default_rng(510608)
    size=384
    y,x=np.mgrid[:size,:size]/size
    fine=rng.normal(0,1,(size,size))
    cloud=gaussian_filter(rng.normal(0,1,(size,size)),6,mode='wrap')*24
    ripple=np.sin(2*np.pi*(31*x+.22*np.sin(2*np.pi*y)+.12*np.cos(2*np.pi*(2*x+y))))
    veins=2*np.sin(2*np.pi*(13*x+.24*np.sin(2*np.pi*y)))+1.8*ripple+.9*fine+cloud
    timber=np.array([78,51,38])+veins[:,:,None]*np.array([1,.83,.68])
    stone=139.+7*gaussian_filter(fine,1.2,mode='wrap')+3.*fine+3.*cloud
    stone+=np.where(fine>1.72,9.,0.)-np.where(fine < -1.45,11.,0.)
    for name,texture in [('entrance-dark-timber.jpg',timber),('entrance-step-stone.jpg',stone[:,:,None]+[0,-9,-22])]:
        Image.fromarray(np.uint8(np.clip(texture,0,255))).save(HERE/name,quality=91,subsampling=0,optimize=True)

if __name__=='__main__':
    write_finishes()
