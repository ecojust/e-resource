"""Draw original periodic render, brick pigmentation and shallow surface normals."""
from pathlib import Path
import importlib.util,json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
common=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('yen_hall_texture_writer',common)
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'Yen Hall | filled grey brick':'yen-hall-grey-brick','Yen Hall | red arch brick':'yen-hall-red-brick'}
NORMAL_FILENAMES={k:v+'-normal.png' for k,v in STEMS.items()}
REPEAT_METRES={'Yen Hall | filled grey brick':(1.008,.592),'Yen Hall | red arch brick':(1.008,.615)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={k:{'color':[1.,1.,1.],'texture':str(HERE/(v+'.png')),'normal':str(HERE/NORMAL_FILENAMES[k]),'roughness':.90}for k,v in STEMS.items()}
def metric_uv(part):
    part['texcoords']=(np.array(part['texcoords'])/(.78*np.asarray(REPEAT_METRES[part['material']]))).tolist()
def generate():
    yy,xx=np.mgrid[:128,:128];book=json.loads((HERE.parent/'measurements/arcade-brick-colour.json').read_bytes())
    for i,(name,stem) in enumerate(STEMS.items()):
        sample=np.array([p['median_srgb']for p in book['samples'][name]]);rgb=np.percentile(sample,60,axis=0)
        # Measurements are shaded. Convert the selected patch to a moderately lit diffuse albedo.
        rgb=np.minimum(241.,rgb*(1.06 if i else 1.01));gen=np.random.default_rng(19041001+i)
        fine=gaussian_filter(gen.normal(size=(128,128)),.42,mode='wrap')
        height=fine*.00035;variation=2.2*fine
        if name in STEMS:
            row=yy//16;offset=16*(row%2);col=((xx+offset)//32)%4
            dx=np.minimum((xx+offset)%32,32-(xx+offset)%32);dz=np.minimum(yy%16,16-yy%16)
            mortar=np.exp(-(np.minimum(dx,dz)/.85)**2);variation+=gen.uniform(-3.,3.,(8,4))[row,col]+(8. if i else 5.)*mortar;height-=.004*mortar
        color=np.clip(rgb+variation[:,:,None],0,255).astype('uint8');u,v=REPEAT_METRES[name]
        dx=(np.roll(height,-1,1)-np.roll(height,1,1))*64/u;dz=(np.roll(height,-1,0)-np.roll(height,1,0))*64/v
        normals=np.stack([-dx,dz,np.ones_like(dx)],axis=-1);normals/=np.linalg.norm(normals,axis=-1,keepdims=True)
        Image.fromarray(color).save(HERE/(stem+'.png'),optimize=True)
        Image.fromarray(np.round(255*(normals*.5+.5)).astype('uint8')).save(HERE/NORMAL_FILENAMES[name],optimize=True)
if __name__=='__main__':generate()
