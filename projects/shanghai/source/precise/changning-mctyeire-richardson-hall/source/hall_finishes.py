"""Periodic cement-render courses, fish-scale red roof rows and the hall's panelled oak."""
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
spec=importlib.util.spec_from_file_location('hall_finish_io',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
WALL='grey ashlar';CLAY='rust red pantile';WOOD='dark oak'
STEMS={WALL:'mortar-scored-grey-render',CLAY:'overlapping-clay-roof',WOOD:'varnished-panel-oak'}
REPEAT={WALL:(2.48,1.04),CLAY:(1.32,1.08),WOOD:(.92,2.12)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES={m:s+'-normal.png' for m,s in STEMS.items()};writer.REPEAT_METRES=REPEAT
PALETTE={m:dict(color=[1,1,1],roughness={WALL:.87,CLAY:.82,WOOD:.47}[m],texture=str(HERE/(s+'.png')),normal=str(HERE/(s+'-normal.png')))for m,s in STEMS.items()}
def metric_uv(part):part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT[part['material']]))).tolist()
def generate():
    samples=json.loads((HERE.parent/'measurements/finish-readings.json').read_text())['materials']
    n=192;y,x=np.indices((n,n));u=(x+.5)/n;v=(y+.5)/n
    for i,(material,stem) in enumerate(STEMS.items()):
        rng=np.random.default_rng(193510+i);grain=gaussian_filter(rng.normal(size=(n,n)),.58,mode='wrap')
        broad=writer.field(u,v,5,9,rng);fine=writer.field(u,v,24,31,rng)
        if material==WALL:
            # The district's material description identifies scored cement render imitating dressed stone.
            row=np.floor(v*2).astype(int);uu=(u*2+row*.5)%1;vv=(v*2)%1
            distance=np.minimum(np.minimum(uu,1-uu)*REPEAT[material][0]/2,np.minimum(vv,1-vv)*REPEAT[material][1]/2)
            groove=np.exp(-np.square(distance/.011));tone=3.2*broad+1.8*fine+3.4*grain-11.*groove
            h=.00055*grain+.00055*broad-.0027*groove
        elif material==CLAY:
            row=np.floor(v*4).astype(int);uu=(u*6+.5*(row%2))%1-.5;vv=(v*4)%1
            lower=((vv+.093*(2*uu)**2+.025*fine)%1)
            seam=np.exp(-np.square((abs(uu)-.5)/.047))*.43
            shadow=np.exp(-np.square(lower/.125));tone=4*broad+3*fine+6.3*np.cos(uu*math_tau)-14*(shadow+seam)
            h=.0045*(1-lower)+.0025*np.cos(uu*math_tau)-.0014*seam+.0006*grain
        else:
            long=writer.field(u,v,49,3,rng);warp=writer.field(u,v,6,2,rng)
            grainline=np.cos(math_tau*(u*23+.52*warp+.13*broad));tone=2.5*long+2.3*broad+2.3*grainline+grain
            h=.00038*long+.00014*grainline+.0001*grain
        base=np.median([s['median_srgb'] for s in samples[material]['samples']],axis=0)
        if material==WOOD:base=np.clip(base*1.30+14,0,255)  # backlit oak under the gallery, lit by the lawn doors
        rgb=base+tone[:,:,None];dx,dy=np.asarray(REPEAT[material])/n
        slope_x=(np.roll(h,-1,1)-np.roll(h,1,1))/(2*dx);slope_y=(np.roll(h,-1,0)-np.roll(h,1,0))/(2*dy)
        normal=np.stack([-slope_x,slope_y,np.ones_like(h)],axis=-1);normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255))).save(HERE/(stem+'.png'))
        Image.fromarray(np.uint8(np.rint((normal+1)*127.5))).save(HERE/(stem+'-normal.png'))
math_tau=2*np.pi
if __name__=='__main__':generate()
