"""Generate an original repeat of staggered fired tiles without photographic pixels."""
from pathlib import Path
from PIL import Image
import numpy as np

def make(path):
    y,x=np.mgrid[:192,:192]
    row=y//24
    col=((x+12*(row%2))%192)//24
    phase=(x+12*(row%2))%24
    bed=y%24
    rng=np.random.default_rng(231)
    weather=rng.normal(0,3.1,(192,192)) + 3.7*np.sin(2*np.pi*x/192)*np.cos(4*np.pi*y/192)
    glaze=np.cos(phase/24*2*np.pi)*3.8
    variation=rng.normal(0,7,(8,8))[row,col]
    seam=np.where((phase<1)|(bed<1),-32,np.where(bed<3,5,0))
    colors=np.array([144.,77.,54.])+((weather+glaze+variation+seam)[:,:,None]*[1,.82,.64])
    Image.fromarray(np.clip(colors,0,255).astype('uint8')).save(path)
if __name__=='__main__':make(Path(__file__).with_name('garden-roof-tiles.png'))
