"""Generate metric running-bond masonry and overlapping plain tiles from original procedural fields."""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from service_materials import BRICK,TILE

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
shared=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('eves_texture_io',shared)
writer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
STEMS={BRICK:'courtyard-brick',TILE:'clay-roofing'}
REPEAT={BRICK:(.96,.66),TILE:(1.05,1.16)}
writer.HERE=HERE
writer.STEMS=STEMS
writer.NORMAL_FILENAMES={k:v+'-normal.png' for k,v in STEMS.items()}
writer.REPEAT_METRES=REPEAT
PALETTE={m:{'color':[1,1,1],'roughness':.90,'texture':str(HERE/(name+'.png')),'normal':str(HERE/(name+'-normal.png'))} for m,name in STEMS.items()}

def metric_uv(part):
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT[part['material']]))).tolist()

def generate():
    readings=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['readings']
    n=256;y,x=np.indices((n,n));u=(x+.5)/n;v=(y+.5)/n
    for i,(m,name) in enumerate(STEMS.items()):
        rng=np.random.default_rng(193752+i)
        cols,rows=(4,9) if m==BRICK else (7,8)
        bx=u*cols+.5*(np.floor(v*rows)%2);by=v*rows
        irow=np.floor(by).astype(int)%rows
        icol=np.floor(bx).astype(int)%cols
        sx=bx%1;sy=by%1
        grain=gaussian_filter(rng.normal(0,1,(n,n)),.63,mode='wrap')
        different=rng.normal(0,7,(rows,cols))[irow,icol]
        surface=writer.field(u,v,18,15,rng)
        base=np.median([f['median_srgb'] for f in readings['walls' if m==BRICK else 'roof']],axis=0)
        if m==BRICK:
            seam=np.minimum(np.minimum(sx,1-sx)*.24,np.minimum(sy,1-sy)*.073)
            mix=np.clip((.0042-seam+.0008*surface)/.0022,0,1)
            rgb=base+(different+grain*7+surface*5)[:,:,None]
            rgb=rgb*(1-mix[:,:,None])+mix[:,:,None]*(base*.59+45)
            relief=.0036*(1-mix)+grain*.00065
        else:
            gap=np.clip((.052-np.minimum(sx,1-sx))/.035,0,1)
            lip=np.clip((.103-sy)/.045,0,1)
            rgb=base+(different*.95+grain*6+surface*8+sy*3-gap*22-lip*18)[:,:,None]
            relief=.010*(1-sy)-gap*.0018-lip*.0035+grain*.00052
        dx=(np.roll(relief,-1,1)-np.roll(relief,1,1))/(2*REPEAT[m][0]/n)
        dy=(np.roll(relief,-1,0)-np.roll(relief,1,0))/(2*REPEAT[m][1]/n)
        normal=np.stack([-dx,dy,np.ones_like(dx)],axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255))).save(HERE/(name+'.png'))
        Image.fromarray(np.uint8(np.rint(127.5*(1+normal)))).save(HERE/(name+'-normal.png'))
if __name__=='__main__':generate()
