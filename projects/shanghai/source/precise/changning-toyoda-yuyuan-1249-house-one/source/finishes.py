"""Create original repeatable masonry and fired-tile finishes from course dimensions."""
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).parent

def generate(directory):
    rng=np.random.default_rng(124901)
    yy,xx=np.indices((384,384))
    courses=24
    row=yy//(384//courses)
    offset=(row%2)*28
    joint=((xx+offset)%56<2)|(yy%(384//courses)<2)
    noise=rng.normal(0,3,xx.shape)
    shade=((row*7+((xx+offset)//56)*13)%13-6)+noise
    brick=np.array([103,100,99])[None,None,:]+shade[:,:,None]*[1.0,.84,.81]
    brick[joint]=np.stack([150+noise[joint],145+noise[joint],134+noise[joint]],axis=-1)
    Image.fromarray(np.uint8(np.clip(brick,0,255))).save(directory/'blue-grey-brick.png',optimize=True)
    rib=12*(1+np.cos(2*np.pi*(xx+.7*np.cos(yy/28))/32))
    lap=-17*((yy%60)<4)
    uneven=((xx//32*7+yy//60*11)%9)-4
    red=np.array([134,74,56])[None,None,:]+(rib+lap+uneven+noise)[:,:,None]*[.7,.53,.41]
    Image.fromarray(np.uint8(np.clip(red,0,255))).save(directory/'interlocking-roof-tiles.png',optimize=True)
if __name__=='__main__':generate(HERE)
