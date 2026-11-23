"""Generate the three periodic finishes from House 15 photograph colour readings."""
import importlib.util,json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
common=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('gallery_material_writer',common);writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'coarse grey-brown pebble dash':'pebble-dash','warm red facing brick':'facing-brick','terracotta roof':'clay-tile'}
NORMAL_FILENAMES={k:v+'-normal.png'for k,v in STEMS.items()}
REPEAT_METRES=dict(zip(STEMS,[(.42,.42),(.91,.593),(.80,.88)]))
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES;writer.REPEAT_METRES=REPEAT_METRES
PALETTE={k:{'color':[1,1,1],'texture':str(HERE/(v+'.png')),'normal':str(HERE/NORMAL_FILENAMES[k]),'roughness':r}for (k,v),r in zip(STEMS.items(),[.91,.87,.82])}
def metric_uv(part):
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT_METRES[part['material']]))).tolist()
def generate():
    sample=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['materials'];N=192;v,u=np.meshgrid(np.arange(N)/N,np.arange(N)/N,indexing='ij')
    for i,(key,name)in enumerate(STEMS.items()):
        rng=np.random.default_rng(87015+i);fine=gaussian_filter(rng.normal(size=(N,N)),.61,mode='wrap');middle=gaussian_filter(rng.normal(size=(N,N)),3.1,mode='wrap');middle/=middle.std();base=np.asarray(sample[key]['median_srgb'])
        if name=='pebble-dash':
            chips=gaussian_filter((rng.random((N,N))>.850).astype(float),.58,mode='wrap');chips-=chips.mean()
            intensity=25*fine+2.8*middle+58*chips;height=.00115*(.65*fine+2.4*chips+.13*middle)
            rgb=base+intensity[:,:,None]*[1.06,1.,.87]
        elif name=='facing-brick':
            row=np.floor(v*8).astype(int);a=(u*4+.5*(row%2))%1.;b=(v*8)%1.
            edge=np.minimum(np.minimum(a,1-a)*.228,np.minimum(b,1-b)*.074);mortar=np.clip((.0058-edge)/.0028,0,1)
            cols=np.floor(u*4+.5*(row%2)).astype(int)%4;variation=rng.uniform(-12,13,(8,4))[row,cols]
            rgb=base+variation[:,:,None]*[1,.74,.52]+(9*fine+2*middle)[:,:,None]
            rgb=rgb*(1-mortar[:,:,None])+np.array([142,119,100])*mortar[:,:,None];height=.00042*fine-.0028*mortar
        elif name=='clay-tile':
            x=(u*4)%1.;y=(v*3)%1.;roll=np.cos(2*np.pi*x);joint=np.clip((.036-np.minimum(y,1-y))/.025,0,1)
            intensity=12*roll-16*joint+4*middle+6*fine;rgb=base+intensity[:,:,None]*[1,.83,.72];height=.0043*roll-.0022*joint+.00032*fine
        else:
            intensity=8.5*fine+3.4*middle;rgb=base+intensity[:,:,None];height=.00040*fine+.00013*middle
        size=REPEAT_METRES[key]
        dx=(np.roll(height,-1,1)-np.roll(height,1,1))/(2*size[0]/N);dy=(np.roll(height,-1,0)-np.roll(height,1,0))/(2*size[1]/N)
        normals=np.stack([-dx,dy,np.ones_like(dx)],axis=-1);normals/=np.linalg.norm(normals,axis=-1,keepdims=True)
        Image.fromarray(np.round(np.clip(rgb,0,255)).astype('uint8')).save(HERE/(name+'.png'),optimize=True)
        Image.fromarray(np.rint((normals*.5+.5)*255).astype('uint8')).save(HERE/NORMAL_FILENAMES[key],optimize=True)
if __name__=='__main__':generate()
