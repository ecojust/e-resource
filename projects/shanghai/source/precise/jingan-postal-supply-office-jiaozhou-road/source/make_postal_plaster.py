"""Paint repeatable lime render and a harder sand-finished plinth from original periodic noise."""
from pathlib import Path
import numpy as np
from PIL import Image

def surface(seed, size, warm, dark, grain):
    gen=np.random.default_rng(seed)
    wave=np.zeros((size,size),float)
    ky,kx=np.meshgrid(np.fft.fftfreq(size),np.fft.rfftfreq(size),indexing='ij')
    for scale,amplitude in ((.013,2.1),(.048,1.1),(.17,1.7)):
        fine=gen.normal(size=(size,size))
        filtered=np.fft.irfft2(np.fft.rfft2(fine)*np.exp(-(kx*kx+ky*ky)/(2*scale*scale)),s=(size,size))
        wave+=amplitude*filtered/filtered.std()
    wave+=gen.normal(0,grain,size=(size,size))
    pores=gen.random((size,size))>.985
    wave[pores]-=gen.uniform(4,13,int(pores.sum()))
    rgb=warm+wave[...,None]*dark
    return Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8'))
def draw(directory):
    surface(19410253,256,np.array([216,214,204]),np.array([1,.98,.93]),1.6).save(directory/'postal-lime-render.jpg',quality=88,subsampling=0)
    surface(19420227,256,np.array([163,158,145]),np.array([1,.98,.86]),3.1).save(directory/'postal-sand-stone.jpg',quality=89,subsampling=0)
if __name__=='__main__':draw(Path(__file__).resolve().parent)
