"""Create an original roughcast chip texture. The street photographs supply no pixels."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
rng=np.random.default_rng(227429)
size=256
cloud=Image.fromarray(rng.integers(0,255,(24,24),dtype=np.uint8)).resize((size,size),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(2))
tone=110+.105*(np.asarray(cloud).astype(float)-128)+rng.normal(0,8,(size,size))
chips=rng.random((size,size))
tone+=np.where(chips<.14,22,np.where(chips>.93,-21,0))
colour=np.stack((tone*1.018,tone*1.023,tone*.96),axis=-1)
Image.fromarray(np.uint8(np.clip(colour,0,255))).quantize(colors=64).save(Path(__file__).with_name('pebble-finish.png'),optimize=True)
