"""Create a seamless 1.32 × 0.64 m original running-bond material."""
from pathlib import Path
from PIL import Image
import numpy as np
rng=np.random.default_rng(235)
width,height=528,256
yy,xx=np.mgrid[:height,:width]
course=yy//32
col=((xx+(course%2)*44)//88)%6
u=(xx+(course%2)*44)%88
v=yy%32
mortar=(u<2)|(v<2)
individual=rng.integers(-13,14,size=(8,6))
pore=rng.normal(0,3.1,(height,width))
rgb=np.array([159,79,62])[None,None,:]+(individual[course,col]+pore)[:,:,None]
rgb[mortar]=np.array([153,128,111])+rng.normal(0,2.3,(mortar.sum(),1))
Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(Path(__file__).with_name('running-bond.png'),optimize=True)
