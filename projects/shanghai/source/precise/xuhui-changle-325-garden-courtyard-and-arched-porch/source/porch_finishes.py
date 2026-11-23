"""Generate metre-scaled garden roughcast and two grades of weathered stone."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
spec=importlib.util.spec_from_file_location('changle_pbr_writer',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
READINGS=json.loads((HERE.parent/'measurements/surface-observations.json').read_bytes())['readings']
STEMS={'325 garden | pale ochre pebble finish':'roughcast','325 porch | mottled grey stair stone':'stair-stone','325 porch | sandy carved balustrade stone':'rail-stone'}
REPEAT={'roughcast':.66,'stair-stone':.71,'rail-stone':.61}
PALETTE={m:{'color':[1.,1.,1.],'roughness':.91,'texture':str(HERE/(name+'.png')),'normal':str(HERE/(name+'-normal.png'))} for m,name in STEMS.items()}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES={m:n+'-normal.png'for m,n in STEMS.items()}
writer.REPEAT_METRES={m:(REPEAT[n],REPEAT[n])for m,n in STEMS.items()}
def metric_uv(part):
    name=STEMS[part['material']]
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*REPEAT[name])).tolist()

def generate():
    side=256
    v,u=np.indices((side,side));u=(u+.5)/side;v=(side-v-.5)/side
    for i,name in enumerate(STEMS.values()):
        rng=np.random.default_rng(32844+i)
        grains=rng.normal(size=(side,side))
        aggregate=gaussian_filter(grains,.58,mode='wrap')
        broad=writer.field(u,v,14,14,rng)
        tone=np.median([a['median_srgb']for a in READINGS[name]],axis=0)
        # The photographed patches include indirect shadow. Preserve their hue
        # while gently lifting the base tone for the separately lit 3-D scene.
        tone=tone*.87+np.mean(tone)*.13+23
        rms=np.median([a['fine_contrast_rms_on_255']for a in READINGS[name]])
        if name=='roughcast':
            bump=np.maximum(aggregate-.11,0)*.0038+aggregate*.0012
            luminance=aggregate/aggregate.std()*rms*.44+broad*4.3
        else:
            bump=aggregate*.00042+broad*.00031
            luminance=aggregate/aggregate.std()*rms*.62+broad*(6.4 if name=='stair-stone' else 4.9)
        color=np.uint8(np.clip(np.rint(tone+luminance[:,:,None]),0,255))
        pitch=REPEAT[name]/side
        dx=(np.roll(bump,-1,1)-np.roll(bump,1,1))/(2*pitch)
        down=(np.roll(bump,-1,0)-np.roll(bump,1,0))/(2*pitch)
        normal=np.stack([-dx,down,np.ones_like(dx)],axis=-1)
        normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        Image.fromarray(color).save(HERE/(name+'.png'))
        Image.fromarray(np.uint8(np.rint(127.5*(1+normal)))).save(HERE/(name+'-normal.png'))

if __name__=='__main__':generate()
