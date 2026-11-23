"""Original seamless finishes for the red-brick street houses at Jingxing Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def write_tiles(folder):
    rng=np.random.default_rng(5314)
    n=432
    yy,xx=np.mgrid[:n,:n]
    noise=rng.normal(size=(n,n))
    fine=noise*5+gaussian_filter(noise,1.1,mode='wrap')*12
    patina=gaussian_filter(noise,12,mode='wrap')
    patina=(patina-patina.mean())/patina.std()
    row=yy//24
    # Header courses alternate with longer stretchers. The 1.28 m texture cycle
    # and its 18 mortar beds correspond to the facade's photographed spacing.
    tile_width=np.where(row%2==0,72,36)
    shift=np.where(row%2==0,18,0)
    jj=((xx+shift)//tile_width)%12
    bed=np.minimum(yy%24,24-yy%24)
    vert=(xx+shift)%tile_width
    joint=(bed<=1)|(np.minimum(vert,tile_width-vert)<=.9)
    variation=rng.normal(0,8,size=(18,12))[row,jj]
    body=variation+patina*3+fine*.64
    chalk=np.array([162,153,133])+((fine*.67+patina*9)[:,:,None]*np.array([1.0,.87,.7]))
    Image.fromarray(np.clip(chalk,0,255).astype('uint8')).save(folder/'yiqingli-limewash.png',optimize=True)
    for filename,base,mortar in [
        ('yiqingli-scarlet-brick.png',(143,56,36),(168,139,113)),
        ('yiqingli-gable-wash.png',(144,52,37),(125,50,36)),
        ('yiqingli-base-brick.png',(91,65,54),(122,111,93))]:
        rgb=np.where(joint[:,:,None],np.array(mortar)+fine[:,:,None]*.48,
                     np.array(base)+body[:,:,None])
        Image.fromarray(np.clip(rgb,0,255).astype('uint8')).save(folder/filename,optimize=True)

if __name__=='__main__':
    write_tiles(Path(__file__).parent)
