"""Original texture and low-relief normal maps for the repaired courtyard plaster."""
from pathlib import Path
import importlib.util
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
source=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('xiangyang_texture_export',source)
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
SURFACES={
    'Xiangyang 313 | pale courtyard render':('south-warm-plaster',(236,226,207),2.0,8361),
    'Xiangyang 313 | light yellow rendered window wall':('north-cream-plaster',(237,224,192),2.3,8362),
}
shared.HERE=HERE
shared.STEMS={mat:recipe[0] for mat,recipe in SURFACES.items()}
shared.NORMAL_FILENAMES={mat:stem+'-normal.png' for mat,stem in shared.STEMS.items()}
METRES=1/.78
shared.REPEAT_METRES={name:(METRES,METRES) for name in SURFACES}
PALETTE={mat:{'color':[1.,1.,1.],'roughness':.92,'texture':str(HERE/(stem+'.png')),
              'normal':str(HERE/(stem+'-normal.png'))}for mat,stem in shared.STEMS.items()}
embed_normals=shared.embed_normals

def generate():
    n=192
    yy,xx=np.indices((n,n));u,v=(xx+.5)/n,(yy+.5)/n
    for stem,base,contrast,seed in SURFACES.values():
        rng=np.random.default_rng(seed)
        fine=shared.field(u,v,112,109,rng)
        mid=shared.field(u,v,31,37,rng)
        wash=shared.field(u,v,7,6,rng)
        tone=.60*fine+.55*mid+.38*wash
        rgb=np.asarray(base)+contrast*tone[...,None]*np.array([1,.96,.90])
        Image.fromarray(np.clip(np.rint(rgb),0,255).astype('uint8')).save(HERE/(stem+'.png'),optimize=True)
        relief=.00015*fine+.00021*mid
        dx=(np.roll(relief,-1,1)-np.roll(relief,1,1))*n/(2*METRES)
        down=(np.roll(relief,-1,0)-np.roll(relief,1,0))*n/(2*METRES)
        normal=np.stack((-dx,down,np.ones_like(dx)),axis=-1)
        normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        Image.fromarray(np.uint8(np.rint((normal+1)*127.5))).save(HERE/(stem+'-normal.png'),optimize=True)
if __name__=='__main__':generate()
