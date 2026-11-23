"""Create the courtyard concrete and plain bond in a periodic tile."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def finishes(folder):
    directory=Path(folder)
    rng=np.random.default_rng(362)
    n=192
    small=rng.normal(0,1,(n,n))
    fine=small*9+gaussian_filter(small,3,mode='wrap')*21
    coarse=gaussian_filter(small,9,mode='wrap')
    coarse=(coarse-coarse.mean())/coarse.std()
    noise=fine+coarse*5
    concrete=np.clip(np.array([155,149,137])+noise[:,:,None],0,255).astype('uint8')
    Image.fromarray(concrete).save(directory/'courtyard-aggregate.png',optimize=True)
    yy,xx=np.mgrid[0:n,0:n];row=yy//12
    mort=((xx+row%2*19)%38<=1) | (yy%12<=1)
    # Eight staggered brick courses cover half the image.
    xxst=(xx+row%2*16)%32
    mort=(xxst<=1)|(yy%12<=1)
    brick=rng.normal(size=(n//12,n//32))*5
    tone=brick[row,((xx+row%2*16)//32)%(n//32)]+fine*.47
    color=np.where(mort[:,:,None],np.array([105,95,80])+fine[:,:,None]*.23,np.array([128,71,49])+tone[:,:,None])
    Image.fromarray(np.clip(color,0,255).astype('uint8')).save(directory/'gallery-red-brick.png',optimize=True)
if __name__=='__main__':
    finishes(Path(__file__).parent)
