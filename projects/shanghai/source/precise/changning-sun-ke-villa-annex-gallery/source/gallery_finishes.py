"""Generate original fish-scale roughcast and lapped clay barrel-tile finishes."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
shared=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('gallery_finish_io',shared)
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
WALL,TILE='scalloped warm render','fired barrel tile'
STEMS={WALL:'fish-scale-roughcast',TILE:'lapped-barrel-tiles'}
REPEAT={WALL:(.80,.68),TILE:(.84,1.24)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES={m:q+'-normal.png' for m,q in STEMS.items()};writer.REPEAT_METRES=REPEAT
PALETTE={m:dict(color=[1,1,1],roughness=.88,texture=str(HERE/(name+'.png')),normal=str(HERE/(name+'-normal.png')))for m,name in STEMS.items()}
def metric_uv(part):part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT[part['material']]))).tolist()
def roughcast(u,v,grain,rng):
    slow=writer.field(u,v,9,9,rng)
    drag=writer.field(u,v,5,6,rng)
    # Individually swept scallops overlap and interlock along staggered rows.
    tx=u*5+.06*slow;ty=v*7+.09*drag
    row=np.floor(ty).astype(int)
    ridge=np.zeros_like(u)
    for offset in [-1,0,1]:
        i=row+offset
        local=(tx+.5*(i%2))%1-.5
        line=i+.16+.58*(1-np.clip(np.abs(2*local),0,1)**1.72)
        distance=(ty-line)*.097
        ridge+=np.exp(-.5*(distance/.0038)**2)
    ridge=np.clip(ridge,0,1.1)
    relief=ridge*.0046+slow*.0010+grain*.00080
    variation=grain*5+slow*3+drag*2-ridge*4
    return variation,relief
def barrel(u,v,grain,rng):
    # Relief on top of the modelled rolls picks out unequal lap joints and the clay lips.
    rows,cols=5,4
    i=np.floor(u*cols).astype(int);phase=.45*(i%2)
    vv=v*rows+phase
    ii=np.floor(vv).astype(int)%rows
    seams=vv%1
    low=np.exp(-.5*((seams-.05)/.04)**2)
    lip=np.exp(-.5*((seams-.13)/.055)**2)
    different=rng.normal(0,5,(rows,cols))[ii,i]
    slow=writer.field(u,v,14,20,rng)
    return different+grain*5+slow*5-low*14+lip*6, .0064*(1-seams)-low*.0035+lip*.0024+grain*.00044
def generate():
    samples=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['samples']
    n=256;y,x=np.indices((n,n));u=(x+.5)/n;v=(y+.5)/n
    for k,(m,name)in enumerate(STEMS.items()):
        rng=np.random.default_rng(1931003+k);grain=gaussian_filter(rng.normal(0,1,(n,n)),.66,mode='wrap')
        base=np.median([p['median_srgb']for p in samples['fish-scale render'if m==WALL else'clay tiles']],axis=0)
        shade,height=(roughcast if m==WALL else barrel)(u,v,grain,rng)
        rgb=base+shade[:,:,None]
        step_x,step_y=np.array(REPEAT[m])/n
        dx=(np.roll(height,-1,1)-np.roll(height,1,1))/(2*step_x)
        dy=(np.roll(height,-1,0)-np.roll(height,1,0))/(2*step_y)
        normal=np.stack((-dx,dy,np.ones_like(dx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255))).save(HERE/(name+'.png'))
        Image.fromarray(np.uint8(np.rint(127.5*(1+normal)))).save(HERE/(name+'-normal.png'))
if __name__=='__main__':generate()
