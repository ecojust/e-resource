"""Procedural lime-aggregate render, cement, enamelled iron and the speckled plaque stone."""
import importlib.util,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).absolute().parent;PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
common=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py';spec=importlib.util.spec_from_file_location('zhaofeng_material_writer',common);writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'grey-pink aggregate plaster':'grey-plaster','worn pale cement':'weathered-cement','black enamel gate iron':'gate-enamel','heritage plaque stone':'plaque-granite'}
NORMAL_FILENAMES={k:v+'-normal.png'for k,v in STEMS.items()};REPEAT_METRES={k:(v,v)for k,v in zip(STEMS,[.36,.53,.26,.29])};writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES;writer.REPEAT_METRES=REPEAT_METRES
PALETTE={k:{'color':[1.,1.,1.],'texture':str(HERE/(stem+'.png')),'normal':str(HERE/NORMAL_FILENAMES[k]),'roughness':r}for (k,stem),r in zip(STEMS.items(),[.87,.91,.52,.77])}
def metric_uv(part):
 part['texcoords']=(np.array(part['texcoords'])/(.78*np.asarray(REPEAT_METRES[part['material']]))).tolist()
def generate():
 data=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['materials'];side=192
 for i,(k,v)in enumerate(STEMS.items()):
  rng=np.random.default_rng(86501+i);noise=rng.standard_normal((side,side));grain=gaussian_filter(noise,.65,mode='wrap');cloud=gaussian_filter(noise,7.,mode='wrap');cloud/=max(1e-9,cloud.std())
  grains=gaussian_filter((rng.random((side,side))>.967).astype(float),.62,mode='wrap');grains-=grains.mean()
  base=np.array(data[k]['median_srgb']);brightness=[8.2*grain+2.2*cloud-9*grains,10*grain+3.6*cloud-25*grains,2.6*grain+1.1*cloud,9.4*grain+1.4*cloud-35*grains][i]
  rgb=np.clip(base+brightness[:,:,None],0,255).round().astype('uint8');z=[.00038,.00064,.000068,.00017][i]*(grain+2.1*grains+cloud*.08)
  step=REPEAT_METRES[k][0]/side;dx=(np.roll(z,-1,1)-np.roll(z,1,1))/(2*step);dy=(np.roll(z,-1,0)-np.roll(z,1,0))/(2*step)
  n=np.stack([-dx,dy,np.ones_like(z)],axis=-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
  Image.fromarray(rgb).save(HERE/(v+'.png'),optimize=True);Image.fromarray(np.rint((n*.5+.5)*255).astype('uint8')).save(HERE/NORMAL_FILENAMES[k],optimize=True)
if __name__=='__main__':generate()
