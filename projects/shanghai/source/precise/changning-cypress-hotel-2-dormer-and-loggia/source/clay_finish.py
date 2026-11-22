"""Project-authored matte ochre clay texture. No pixels from the district photograph are embedded."""
from pathlib import Path
MATERIAL='Ochre roof pans with mineral speckle'
TEXTURE=Path(__file__).with_name('ochre-pan-clay.png')
def generate():
    import numpy as np
    from scipy.ndimage import gaussian_filter
    from PIL import Image
    grain=np.random.default_rng(241902).standard_normal((144,144))
    tones=2.5*grain+9*gaussian_filter(grain,1.35,mode='wrap')+17*gaussian_filter(grain,4.1,mode='wrap')
    rgb=np.array([199.,132.,75.])+tones[:,:,None]*np.array([1.,.92,.78])
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(TEXTURE,optimize=True)
if __name__=='__main__':generate()
