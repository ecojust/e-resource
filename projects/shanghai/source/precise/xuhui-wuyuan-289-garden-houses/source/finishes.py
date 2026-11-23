"""Generate periodic mortar, roof tile and limewash textures without photographic content."""
from pathlib import Path
import numpy as np
from PIL import Image
def make(where=Path(__file__).resolve().parent):
    rng=np.random.default_rng(289);y,x=np.mgrid[:256,:256];grain=rng.normal(0,3.3,(256,256,1))
    row=y//16;shift=(x+(row%2)*25)%256
    col=(shift//51.2).astype(int);face=rng.normal(0,6,(16,5))[row,col]
    fade=(y%16<2)|(shift%51.2<2.1)
    brick=np.array([159,93,73])+face[:,:,None]*[1,.80,.64]+grain
    brick[fade]=np.array([169,141,120])+grain[fade]*.73
    tile_row=y//32;tile_x=(x+((tile_row%2)*15))%32
    ridge=4*np.cos(tile_x/32*np.pi*2)+2*np.cos(x/8*np.pi)
    value=rng.normal(0,3.7,(8,8))[tile_row,((x+(tile_row%2)*15)%256)//32]+ridge
    tile=np.array([86,64,52])+value[:,:,None]*[1,.8,.7]+grain*.7
    tile[y%32<2]-=12;tile[tile_x<2]-=8
    wash=np.array([216,201,174])+grain*.5
    for name,a in [('red-facing-brick',brick),('clay-roof',tile),('lime-plaster',wash)]:
        Image.fromarray(np.uint8(np.clip(a,0,255))).save(where/(name+'.png'),optimize=True)
if __name__=='__main__':make()
