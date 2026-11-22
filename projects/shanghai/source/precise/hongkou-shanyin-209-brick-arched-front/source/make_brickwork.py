"""Make repeatable running-bond facing aligned with the courses in the photograph."""
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_filter
from material_names import TEXTURES,PLASTER,RED
W,H=768,384
rows=16;columns=8
y,x=np.indices((H,W),dtype=float)
row=np.floor(y/(H/rows)).astype(int)
xx=(x+((row%2)*.5)*W/columns)/(W/columns)
col=np.floor(xx).astype(int)%columns
vx=(xx%1.)*W/columns;vy=(y%(H/rows))
rng=np.random.default_rng(209)
def noise(scale):
    v=gaussian_filter(rng.normal(size=(H,W)),scale,mode='wrap');return v/v.std()
grain=noise(.48)*2.6+noise(2.1)*1.4
for material,base,mortar in [(PLASTER,[91,93,92],[167,161,147]),(RED,[158,77,52],[177,150,125])]:
    shifts=rng.normal(0,5,(rows,columns,1))+rng.normal(0,1.8,(rows,columns,3))
    surface=np.array(base)+shifts[row,col]+(grain+noise(6)*1.35)[:,:,None]
    dist=np.minimum.reduce([vx,W/columns-vx,vy,H/rows-vy])+noise(.8)*.29
    transition=np.clip((dist-.63)/1.3,0.,1.)[:,:,None]
    grout=np.array(mortar)+(grain*.75+noise(5)*2.1)[:,:,None]
    arr=grout*(1.-transition)+surface*transition
    Image.fromarray(np.clip(arr,0,255).astype('uint8')).save(TEXTURES[material],quality=90,subsampling=0)
