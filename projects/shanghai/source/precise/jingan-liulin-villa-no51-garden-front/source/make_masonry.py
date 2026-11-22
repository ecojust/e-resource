"""Generate the blue-grey stretcher bond and weathered red pantiles in local metre-based UVs."""
from pathlib import Path
import numpy as np
from PIL import Image

def make(path):
    rng=np.random.default_rng(608)
    y,x=np.mgrid[:256,:384];row=y//32;pos=(x+48*(row%2))%384;s=pos%96;t=y%32
    joint=np.clip((2.20-np.minimum.reduce([s,95-s,t,31-t]))/1.45,0,1)
    grain=rng.normal(0,3.2,x.shape);vary=rng.normal(0,5.,(8,4))[row,pos//96]
    bluegrey=np.array([111.,111.,107.])+(grain+vary)[...,None]
    mortar=np.array([189.,187.,176.])+grain[...,None]*.4
    Image.fromarray(np.uint8(np.clip(bluegrey*(1-joint[...,None])+mortar*joint[...,None],0,255))).save(path/'garden-grey-bricks.png')
    x1=x/48.;ridge=np.sin(2*np.pi*x1)*5.2;end=np.exp(-((y%64-61)/2.9)**2)*24
    texture=np.array([145.,91.,72.])+((rng.normal(0,3.,x.shape)+ridge-end+rng.normal(0,6.,(4,8))[y//64,x//48])[...,None])
    Image.fromarray(np.uint8(np.clip(texture,0,255))).save(path/'garden-red-tiles.png')
if __name__=='__main__':make(Path(__file__).parent)
