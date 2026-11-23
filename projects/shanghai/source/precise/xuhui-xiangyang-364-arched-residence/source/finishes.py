"""Generate mineral aggregate and plaster from a seeded random field."""
from PIL import Image
from pathlib import Path
import numpy as np
def make():
    dest=Path(__file__).resolve().parent
    rng=np.random.default_rng(364)
    for name,base,variation in [('street-plaster',[210,198,173],3.1),('granite-chips',[143,139,127],9.8)]:
        grains=rng.normal(0,variation,(192,192,1))
        if name=='granite-chips':
            chips=rng.random((192,192,1));grains+=np.where(chips<.065,-31,np.where(chips>.945,23,0))
        arr=np.clip(np.asarray(base)+grains,0,255)
        Image.fromarray(np.uint8(arr)).save(dest/(name+'.png'),optimize=True)
if __name__=='__main__':make()
