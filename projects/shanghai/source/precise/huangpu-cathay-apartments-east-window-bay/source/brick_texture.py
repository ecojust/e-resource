"""Draw an original running-bond material in the proportions seen on the east window bay."""
from pathlib import Path
import numpy as np
from PIL import Image

def create(path):
    rng=np.random.default_rng(4093)
    h,w=1280,640
    y,x=np.mgrid[:h,:w]
    xm=(x+.5)*5.60/w
    zm=(h-y-.5)*11.30/h
    course=np.floor(zm/.082).astype(int)
    xm=xm+(course%2)*.113
    block=np.floor(xm/.226).astype(int)
    tx=xm%.226
    tz=zm%.082
    variability=rng.normal(0,8,(140,27))[course,block]
    grain=rng.normal(0,4,(h,w))
    rim=np.minimum.reduce([tx/.005,(.226-tx)/.005,tz/.005,(.082-tz)/.005]).clip(0,1)
    surface=np.stack([91+variability+grain,57+.67*variability+grain,48+.57*variability+grain],axis=-1)
    joint=np.stack([150+grain,133+grain,113+grain],axis=-1)
    Image.fromarray(np.clip(surface*rim[...,None]+joint*(1-rim[...,None]),0,255).astype('uint8')).save(path,quality=84,subsampling=0,optimize=True)
if __name__=='__main__':create(Path(__file__).with_name('brown-facing-brick.jpg'))
