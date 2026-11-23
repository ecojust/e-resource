"""Generate periodic colour and surface-normal tiles from facade swatches."""
import json,math
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).absolute().parent
STEMS={'pale stucco':'cream-render','warm ochre stucco':'ochre-render','red glazed pantile':'red-glaze','cut stone':'carved-stone'}
REPEATS={'pale stucco':(.43,.43),'warm ochre stucco':(.53,.53),'red glazed pantile':(.66,.84),'cut stone':(.83,.58)}
def generate():
    ref=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())
    n=128;v,u=np.mgrid[:n,:n]/n; rng=np.random.default_rng(200)
    for mat,stem in STEMS.items():
        fine=rng.normal(0,1,(n,n));band=np.cos(2*np.pi*(u*3+v))+np.sin(2*np.pi*(u-v*4))*.65
        c=np.asarray(ref[mat]['median'])
        if mat=='red glazed pantile':
            roll=np.cos(2*np.pi*u*4);seam=(1-np.minimum(1,np.minimum(v*3%1,1-v*3%1)/.05))
            signal=9*roll-15*seam+1.4*fine;h=.0095*roll-.0026*seam+.00009*fine
        elif mat=='cut stone':
            signal=4.8*fine+2.5*band;h=.00065*fine+.00029*band
        else:
            signal=2.7*fine+1.7*band;h=.00038*fine+.00034*band
        base=c+signal[:,:,None]
        sx,sy=REPEATS[mat]
        dx=(np.roll(h,-1,1)-np.roll(h,1,1))/(2*sx/n)
        dy=(np.roll(h,-1,0)-np.roll(h,1,0))/(2*sy/n)
        normal=np.stack((-dx,dy,np.ones_like(dx)),axis=-1);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
        Image.fromarray(np.rint(base).clip(0,255).astype('uint8')).save(HERE/(stem+'.png'))
        Image.fromarray(np.rint((.5*normal+.5)*255).astype('uint8')).save(HERE/(stem+'-normal.png'))
if __name__=='__main__':generate()
