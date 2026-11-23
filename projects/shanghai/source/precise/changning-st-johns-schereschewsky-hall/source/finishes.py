"""Periodic fired brick, overlapping butterfly tiles and painted timber based on source-image readings."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
spec=importlib.util.spec_from_file_location('wanping_finish_io',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
GREY='blue-grey facing brick';RED='warm red brick dressings';TILE='grey butterfly tile';WOOD='painted red-brown timber'
STEMS={GREY:'blue-grey-brickwork',RED:'red-brick-dressings',TILE:'grey-butterfly-tiles',WOOD:'painted-gallery-wood'}
# Five bricks in a 1.25 m horizontal repeat and eight courses in 0.60 m. These are nominal modules.
REPEAT={GREY:(1.25,.60),RED:(1.25,.60),TILE:(.96,1.04),WOOD:(.68,1.65)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES={key:stem+'-normal.png' for key,stem in STEMS.items()};writer.REPEAT_METRES=REPEAT
PALETTE={k:dict(color=[1.,1.,1.],roughness={GREY:.88,RED:.86,TILE:.76,WOOD:.63}[k],texture=str(HERE/(v+'.png')),normal=str(HERE/(v+'-normal.png'))) for k,v in STEMS.items()}
def metric_uv(part):
 part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT[part['material']]))).tolist()
def generate():
 data=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['materials']
 n=192;y,x=np.indices((n,n));u=(x+.5)/n;v=(y+.5)/n
 for i,(key,stem) in enumerate(STEMS.items()):
    rng=np.random.default_rng(189512+i)
    broad=writer.field(u,v,7,8,rng);grain=gaussian_filter(rng.normal(0,1,(n,n)),.50,mode='wrap')
    samples=data[key]
    base=np.mean([np.median([j['median_srgb']for j in p],axis=0)for p in samples.values()],axis=0)
    if key in [GREY,RED]:
        cy=np.floor(8*v).astype(int);cx=np.floor(5*u+.5*(cy%2)).astype(int)%5
        tx=(5*u+.5*(cy%2))%1;ty=(8*v)%1
        d=np.minimum(np.minimum(tx,1-tx)*.25,np.minimum(ty,1-ty)*.075)
        mortar=np.exp(-np.square(d/.0058));piece=rng.normal(0,6.5,(8,5))[cy,cx]
        rgb=base+(piece+6*grain+2.0*broad)[:,:,None]+mortar[:,:,None]*(np.array([18,17,15]) if key==GREY else np.array([10,9,6]))
        height=-.0024*mortar+.00047*grain+.0003*broad
    elif key==TILE:
        tube=np.cos(2*np.pi*6*u);tile_end=(v*4+.12*tube)%1
        overlap=np.exp(-np.square(tile_end/.10));hue=9*tube-8*overlap+2.7*broad+2.4*grain
        rgb=base+hue[:,:,None];height=.021*(1+tube)/2+.0042*(1-tile_end)-.0013*overlap
    else:
        g=writer.field(u,v,41,3,rng);waves=np.cos(2*np.pi*(u*18+.28*broad+.07*g))
        rgb=base+(2.8*g+2.4*waves+grain)[:,:,None];height=.00021*g+.00012*waves
    dx,dy=np.asarray(REPEAT[key])/n
    sx=(np.roll(height,-1,1)-np.roll(height,1,1))/(2*dx);sy=(np.roll(height,-1,0)-np.roll(height,1,0))/(2*dy)
    normal=np.stack([-sx,sy,np.ones_like(height)],axis=2);normal/=np.linalg.norm(normal,axis=2)[:,:,None]
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(HERE/(stem+'.png'),optimize=True)
    Image.fromarray(np.uint8(np.clip((normal*.5+.5)*255+.5,0,255))).save(HERE/(stem+'-normal.png'),optimize=True)
if __name__=='__main__':generate()
