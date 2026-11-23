"""Seeded material patches for the lime, banded base, castings, red tile and green enamel at No. 4."""
from pathlib import Path
import importlib.util,json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
p=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('embedded_metric_finishes',p);writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'aged warm lime render':'garden-lime','banded grey base':'grey-base','light ochre cast stone':'cast-bands','weathered red roof tile':'pitched-red-tile','green enamel number plate':'green-enamel'}
REPEAT_METRES=dict(zip(STEMS,[(.75,.75),(.83,.66),(.60,.54),(1.15,.85),(.22,.18)]))
NORMAL_FILENAMES={k:v+'-normal.png'for k,v in STEMS.items()}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES;writer.REPEAT_METRES=REPEAT_METRES
PALETTE={k:dict(color=[1,1,1],texture=str(HERE/(v+'.png')),normal=str(HERE/NORMAL_FILENAMES[k]),roughness=r)for (k,v),r in zip(STEMS.items(),[.94,.89,.83,.84,.44])}
def metric_uv(part):
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT_METRES[part['material']]))).tolist()

def generate():
    readings=json.loads((HERE.parent/'measurements/surface-colours.json').read_bytes())['readings']
    n=192;y,x=np.indices((n,n))/n
    for j,(key,stem)in enumerate(STEMS.items()):
        rng=np.random.default_rng(19281112+j)
        noise=rng.normal(size=(n,n));grain=gaussian_filter(noise,.43,mode='wrap')
        cloud=gaussian_filter(noise,5.7,mode='wrap');cloud/=cloud.std()
        height=np.zeros((n,n));colour=np.array(readings[key]['median_srgb'])+np.zeros((n,n,3))
        if stem=='pitched-red-tile':
            row=np.floor(y*4).astype(int);u=(x*5+(row%2)*.5)%1;v=(y*4)%1
            joint=np.exp(-(np.minimum(u,1-u)/.033)**2)+.68*np.exp(-(np.minimum(v,1-v)/.037)**2)
            roll=np.cos((u-.16)*np.pi*2)
            colour+=((5.4*grain+2.7*cloud+4.5*roll)[:,:,None])*[1,.82,.72]-15*joint[:,:,None]
            height=.0045*roll-.0031*joint+.00050*grain
        elif stem=='green-enamel':
            speck=(gaussian_filter(noise,.6,mode='wrap')>1.07).astype(float)
            colour+=(1.7*grain+1.15*cloud+7*speck)[:,:,None]
            height=.000027*grain+.00008*speck
        else:
            amplitude={'garden-lime':9.7,'grey-base':6.1,'cast-bands':4.7}[stem]
            scratch=gaussian_filter(noise,(3.2,.72),mode='wrap') if stem=='garden-lime' else 0
            agg=gaussian_filter((noise>1.0).astype(float),.55,mode='wrap')
            colour+=(grain*amplitude+cloud*2.7+9*(agg-.16)+2.3*scratch)[:,:,None]
            height=.00055*grain+.00063*agg+.00020*cloud
        dx=(np.roll(height,-1,1)-np.roll(height,1,1))*n/(2*REPEAT_METRES[key][0])
        dy=(np.roll(height,-1,0)-np.roll(height,1,0))*n/(2*REPEAT_METRES[key][1])
        normal=np.stack([-dx,dy,np.ones_like(dx)],axis=-1);normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        Image.fromarray(np.uint8(np.clip(np.rint(colour),0,255))).save(HERE/(stem+'.png'),optimize=True)
        Image.fromarray(np.uint8(np.rint((normal*.5+.5)*255))).save(HERE/NORMAL_FILENAMES[key],optimize=True)
if __name__=='__main__':generate()
