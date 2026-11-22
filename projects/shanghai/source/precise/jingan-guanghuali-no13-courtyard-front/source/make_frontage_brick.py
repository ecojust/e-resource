"""Original running-bond ochre masonry texture, four stretchers by eight courses."""
from pathlib import Path
import numpy as np
from PIL import Image
def draw(outfile):
    rng=np.random.default_rng(604)
    height,width=208,364;y,x=np.mgrid[:height,:width];course=y//26;local=(x+45*(course%2))%width
    brick=local//91;u=local%91;v=y%26
    joint=np.clip((1.85-np.minimum.reduce([u,90-u,v,25-v]))/1.45,0,1)
    grain=rng.normal(0,1.9,(height,width));offset=rng.normal(0,5.5,(8,4))[course,brick]
    pigment=np.array([180.,134.,106.])+(grain+offset)[...,None]
    mortar=np.array([191.,162.,140.])+grain[...,None]*.45
    img=pigment*(1-joint[...,None])+mortar*joint[...,None]
    Image.fromarray(np.clip(img,0,255).astype('uint8')).save(outfile,optimize=True)
if __name__=='__main__':draw(Path(__file__).with_name('guanghua-ochre-brick.png'))
