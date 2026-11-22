"""Draw an original grain and rain-worn finish for the two historic gate leaves."""
from pathlib import Path
import numpy as np
from PIL import Image

def field(rng, width, height, grid_width, grid_height):
    sample = rng.uniform(-1., 1., (grid_height, grid_width)).astype('float32')
    return np.asarray(Image.fromarray(sample).resize((width,height),Image.Resampling.BICUBIC))

def make_texture(target):
    rng = np.random.default_rng(746)
    width,height=420,700
    yy,xx=np.mgrid[0:height,0:width]
    curve=3.1*field(rng,width,height,8,7)+1.5*np.sin(yy/130.+xx/41)
    warped=np.clip((xx+curve).astype(int),0,width-1)
    streak=field(rng,width,height,161,9)[yy,warped]
    fibre=field(rng,width,height,315,32)[yy,warped]
    broad=field(rng,width,height,34,9)
    grain=field(rng,width,height,260,270)
    speck=rng.integers(0,150,(height,width))
    # Long exposed fibres and patches of silvering increase towards the threshold.
    wear=np.clip((yy/height-.32)*.74+.33*broad+.19*streak-.07,0,.99)
    wear*=.45+.55*(.5+.5*fibre)
    shadow=np.clip(1.-yy/(height*.17),0.,1.)*.48
    value=34.+7.9*streak+3.7*fibre+3.1*grain+4.1*broad+1.8*(speck%4)-shadow*18
    value+=wear*(62+22*grain)+(speck<3)*(.6+wear)*22.
    colour=np.stack([value+8.3-wear*9.5,value+3.9-wear*4.2,value-.4+wear*3.1],axis=2)
    Image.fromarray(np.uint8(np.clip(colour,8,175))).save(target,optimize=True)

if __name__=='__main__':
    make_texture(Path(__file__).with_name('weathered-planks.png'))
