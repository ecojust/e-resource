"""Original procedural mineral finishes for the repaired Kempton Apartments."""
from pathlib import Path
import numpy as np
from PIL import Image

SOURCE = Path(__file__).resolve().parent
RENDER='Kempton | pale cement render'
BASE='Kempton | washed mineral aggregate'
TOE='Kempton | tooled stone plinth'
CAP='Kempton | pale stone nose and reveals'
METAL='Kempton | painted steel'
GLASS='Kempton | cool grey glass'
LIGHT='Kempton | pale window reflection'
ROOF='Kempton | flat roof finish'
SEAM='Kempton | zinc drip edge'

def colour(rgb,r=.85):
    channels=[v/255 for v in rgb]
    return {'color':[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels],'roughness':r}

def material(file):return {'color':[1.,1.,1.],'roughness':.9,'texture':str(SOURCE/file)}
PALETTE={RENDER:material('original-cement.png'),BASE:material('original-washed-aggregate.png'),
         TOE:colour((123,121,113)),CAP:colour((195,193,176)),METAL:colour((64,74,69),.48),
         GLASS:colour((111,132,141),.32),LIGHT:colour((123,141,145),.3),ROOF:colour((141,137,127)),SEAM:colour((143,137,120),.68)}

def draw_finishes():
    rng=np.random.default_rng(12401940)
    for name,base in [('original-cement.png',(191,190,174)),('original-washed-aggregate.png',(147,149,141))]:
        n=256
        field=Image.fromarray(rng.integers(0,255,(32,32),dtype=np.uint8)).resize((n,n), Image.Resampling.BICUBIC)
        tone=(np.asarray(field,dtype=float)-128)*.048+rng.normal(0,2.,(n,n))
        if name.endswith('aggregate.png'):
            grain=rng.random((n,n));tone+=np.where(grain<.09,-22,np.where(grain>.93,22,0))
        Image.fromarray(np.uint8(np.clip(np.array(base)[None,None,:]+tone[:,:,None],0,255))).save(SOURCE/name)
if __name__=='__main__':draw_finishes()
