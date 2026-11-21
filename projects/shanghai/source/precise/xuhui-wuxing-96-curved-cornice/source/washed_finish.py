"""Original, repeatable coloured aggregate for the small window hood."""
from pathlib import Path
import numpy as np
from PIL import Image

TEXTURE=Path(__file__).with_name('window-hood-aggregate.png')
MATERIAL='Washed stone on window hood'
PERIOD=.24

def create(path=TEXTURE):
    size=384
    rng=np.random.default_rng(431930)
    field=rng.normal(0,1.75,(size,size))
    for x,y,spread,amount in zip(rng.uniform(0,size,2600),rng.uniform(0,size,2600),
                                 rng.uniform(.5,2.8,2600),rng.uniform(-22,24,2600)):
        extent=int(np.ceil(2*spread))
        for j in range(-extent,extent+1):
            for i in range(-extent,extent+1):
                xx,yy=int(x)+i,int(y)+j
                r=((xx-x)**2+(yy-y)**2)/(spread*spread)
                if r<3:field[yy%size,xx%size]+=amount*np.exp(-1.8*r)
    base=np.array([166.,155.,136.])
    im=np.rint(np.clip(base+field[:,:,None],0,255)).astype('uint8')
    Image.fromarray(im).save(path,optimize=True)
if __name__=='__main__':create()
