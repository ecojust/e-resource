"""Generate repeatable painted-window and weathered-stone surfaces, without source photographs."""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
file=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('yao_embedded_texture_io',file)
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'Yao | russet window frame':'russet-painted-joinery','Yao | terrace stone':'water-garden-stone'}
REPEAT_METRES={'Yao | russet window frame':(.52,.65),'Yao | terrace stone':(.90,.90)}
NORMAL_FILENAMES={key:stem+'-normal.png' for key,stem in STEMS.items()}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={key:{'color':[1.,1.,1.],'texture':str(HERE/(name+'.png')),'normal':str(HERE/NORMAL_FILENAMES[key]),
              'roughness':.46 if 'joinery' in name else .84}for key,name in STEMS.items()}


def metric_uv(part):
    part['texcoords']=(np.array(part['texcoords'])/(.78*np.asarray(REPEAT_METRES[part['material']]))).tolist()


def generate():
    readings=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['materials']
    for j,(key,stem) in enumerate(STEMS.items()):
        rng=np.random.default_rng(851243+j)
        white=rng.normal(size=(128,128))
        coarse=gaussian_filter(white,2.6,mode='wrap')
        if j==0:
            fine=gaussian_filter(white,(2.9,.58),mode='wrap')
            scalar=2.3*fine+5*coarse
            height=.00008*fine
        else:
            fine=gaussian_filter(white,.66,mode='wrap')
            scalar=5.0*fine+8*coarse
            height=.00024*fine+.00013*coarse
        rgb=np.median(np.array([v['median_srgb']for v in readings[key]],float),axis=0)
        col=np.clip(rgb[None,None,:]+scalar[:,:,None],0,255).astype('uint8')
        dx=(np.roll(height,-1,1)-np.roll(height,1,1))*64/REPEAT_METRES[key][0]
        dy=(np.roll(height,-1,0)-np.roll(height,1,0))*64/REPEAT_METRES[key][1]
        vec=np.stack([-dx,dy,np.ones_like(height)],axis=-1)
        vec/=np.linalg.norm(vec,axis=-1,keepdims=True)
        norm=np.round((vec*.5+.5)*255).astype('uint8')
        Image.fromarray(col).save(HERE/(stem+'.png'),optimize=True)
        Image.fromarray(norm).save(HERE/NORMAL_FILENAMES[key],optimize=True)


if __name__=='__main__':
    generate()
