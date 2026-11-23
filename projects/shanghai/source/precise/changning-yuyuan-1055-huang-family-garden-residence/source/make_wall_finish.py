"""Generate the repeating roughcast from grains and low-frequency scatter."""
from pathlib import Path
from PIL import Image
import numpy as np
def write(out):
    r=np.random.default_rng(1055);grain=r.normal(0,1,(256,256));medium=r.normal(0,1,(64,64))
    image=Image.fromarray((np.clip(medium,-3,3)*35+126).astype('uint8')).resize((256,256),Image.Resampling.BICUBIC)
    color=(np.array([204,196,168])[None,None,:]+(grain*6.1+(np.asarray(image).astype(float)-126)*.095)[:,:,None]).clip(0,255).astype('uint8')
    Image.fromarray(color).save(out,optimize=True)
if __name__=='__main__':write(Path(__file__).with_name('garden-ochre-roughcast.png'))
