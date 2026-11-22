"""Generate an original seamless fine-grained granite from measured tonal statistics."""
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image

def make(filename):
    n=192
    rng=np.random.default_rng(310021)
    def field(sigma):
        f=gaussian_filter(rng.standard_normal((n,n)),sigma,mode='wrap')
        return (f-f.mean())/f.std()
    fines=field(.32)
    grains=field(1.05)
    clusters=field(1.8)
    mica=np.clip((-grains-.61)*13.1,0,26)
    quartz=np.clip((grains-.60)*9.2,0,17)
    colors=np.array([155.,161.,160.])
    v=3.9*field(4.1)+3.5*clusters+4.9*fines+quartz-mica
    rock=colors[None,None,:]+v[:,:,None]
    warm=np.clip(field(1.12)-1.23,0,1.9)
    rock+=warm[:,:,None]*np.array([2.3,.2,-1.8])
    Image.fromarray(np.uint8(np.clip(np.rint(rock),0,255))).save(filename,optimize=True)

if __name__=='__main__':make(Path(__file__).with_name('changde-porch-granite.png'))
