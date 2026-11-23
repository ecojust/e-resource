"""Generate two periodic original tile and chimney patterns using no photo pixels."""
from pathlib import Path
import numpy as np
from PIL import Image

def create(directory):
    size=192
    y,x=np.mgrid[:size,:size]
    rng=np.random.default_rng(236)
    for name,tile in [('salmon-plain-roof-tiles.png',True),('clinker-chimney-running-bond.png',False)]:
        h,w=(16,24) if tile else (12,48)
        row=y//h;col=((x+(row%2)*w//2)%size)//w
        a=(x+(row%2)*w//2)%w;b=y%h
        random_color=rng.normal(0,6,(size//h,size//w))[row,col]+rng.normal(0,2.8,(size,size))
        if tile:
            pigment=np.array([179,116,79]);shape=-20*(b<2)+4*(b==3)-9*(a<1)+3*np.sin(2*np.pi*a/w)
            val=pigment+(random_color+shape)[:,:,None]*[1,.82,.69]
        else:
            val=np.array([150,85,66])+random_color[:,:,None]*[1,.85,.72]
            mortar=(b<2)|(a<2);val[mortar]=np.array([158,144,119])+rng.normal(0,2.5,(mortar.sum(),1))
        Image.fromarray(val.clip(0,255).astype('uint8')).save(directory/name)
if __name__=='__main__':create(Path(__file__).parent)
