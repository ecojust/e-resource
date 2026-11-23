"""Procedural cypress grain and grey fired-clay patina of the reconstructed campus gate."""
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('gate_texture_writer',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
WOOD='Fudan | weathered cypress'
TILE='Fudan | dark grey clay'
STEMS={WOOD:'gate-cypress',TILE:'gate-grey-clay'}
REPEAT_METRES={WOOD:(.41,1.32),TILE:(.62,.69)}
NORMAL_FILENAMES={k:s+'-normal.png'for k,s in STEMS.items()}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={k:{'color':[1.,1.,1.],'texture':str(HERE/(s+'.png')),'normal':str(HERE/NORMAL_FILENAMES[k]),'roughness':.85}for k,s in STEMS.items()}
def generate():
    rng=np.random.default_rng(200410);size=128
    y,x=np.mgrid[:size,:size]
    for material,stem in STEMS.items():
        noise=rng.standard_normal((size,size))
        fine=gaussian_filter(noise,.48,mode='wrap')
        if material==WOOD:
            fibres=gaussian_filter(noise,(11,.57),mode='wrap')
            wave=np.cos(2*np.pi*(x*13/size+.31*np.sin(2*np.pi*y/size)))
            colour=np.array([133,87,61])+(fibres*39+wave*2.4+fine*1.3)[:,:,None]
            height=.00115*fibres+.00033*wave
        else:
            pores=gaussian_filter(noise,.73,mode='wrap')
            colour=np.array([68,70,72])+(pores*9+fine*2.0)[:,:,None]
            height=.0019*pores
        u,v=REPEAT_METRES[material]
        nx=-(np.roll(height,-1,1)-np.roll(height,1,1))*size/(2*u)
        ny=(np.roll(height,-1,0)-np.roll(height,1,0))*size/(2*v)
        vec=np.stack([nx,ny,np.ones_like(nx)],axis=2);vec/=np.linalg.norm(vec,axis=2,keepdims=True)
        Image.fromarray(np.clip(colour,0,255).astype('uint8')).save(HERE/(stem+'.png'),optimize=True)
        Image.fromarray(np.rint(127.5*(1+vec)).clip(0,255).astype('uint8')).save(HERE/NORMAL_FILENAMES[material],optimize=True)
if __name__=='__main__':generate()
