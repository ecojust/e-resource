"""Generate the belfry's trowelled ochre finish and mottled aperture stone."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
shared=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('belfry_finish_io',shared)
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
WALL='ochre stippled roughcast';STONE='brown dressed masonry'
STEMS={WALL:'trowelled-ochre-render',STONE:'brown-lancet-stone'}
REPEAT={WALL:(1.32,.92),STONE:(.77,.70)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES={m:s+'-normal.png'for m,s in STEMS.items()};writer.REPEAT_METRES=REPEAT
PALETTE={m:dict(color=[1,1,1],roughness=.92 if m==WALL else .82,texture=str(HERE/(s+'.png')),normal=str(HERE/(s+'-normal.png')))for m,s in STEMS.items()}
def metric_uv(part):
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT[part['material']]))).tolist()
def generate():
    samples=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['samples']
    n=192;y,x=np.indices((n,n));u=(x+.5)/n;v=(y+.5)/n
    for i,(m,stem)in enumerate(STEMS.items()):
        rng=np.random.default_rng(20080405+i)
        grain=gaussian_filter(rng.standard_normal((n,n)),.54,mode='wrap')
        cloud=writer.field(u,v,8,11,rng);warp=writer.field(u,v,4,5,rng)
        if m==WALL:
            # The courtyard photographs show short rough horizontal lips, overlapping in irregular rows.
            yy=v*7+.085*cloud;row=np.floor(yy).astype(int)
            ridges=np.zeros_like(u)
            for shift in (-1,0,1):
                k=row+shift
                run=(u*5+.46*(k%2)+.07*warp)%1-.5
                path=k+.29+.29*(1-(2*run)**2)+.067*cloud
                lip=np.exp(-.5*((yy-path)/.055)**2)
                ridges+=lip*np.clip(1.26-np.abs(2*run)**4,.03,1)
            tone=grain*5.0+cloud*3.3+warp*3.0-ridges*4.6
            relief=.0038*ridges+.00085*grain+.0013*cloud
        else:
            fine=writer.field(u,v,41,37,rng)
            tone=grain*8.5+cloud*5.6+warp*3.2+fine*3.3
            relief=.0008*grain+.00048*fine+.0009*cloud
        base=np.median([r['median_srgb']for r in samples[m]],axis=0)
        rgb=base+tone[:,:,None]
        dx,dy=np.array(REPEAT[m])/n
        gx=(np.roll(relief,-1,1)-np.roll(relief,1,1))/(2*dx);gy=(np.roll(relief,-1,0)-np.roll(relief,1,0))/(2*dy)
        normal=np.stack((-gx,gy,np.ones_like(gx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255))).save(HERE/(stem+'.png'))
        Image.fromarray(np.uint8(np.rint(127.5*(normal+1)))).save(HERE/(stem+'-normal.png'))
if __name__=='__main__':generate()
