"""Procedural metre-scaled render and weathered ground-floor stucco at No. 2."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
writer_path=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('hunan_280_surface_writer',writer_path)
writer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
WALL='280-2 | pale ochre roughcast'
GROUND='280-2 | grey lower render'
SILL='280-2 | weathered sill stone'
STEEL='280-2 | dark steel joinery'
STEMS={WALL:'upper-render',GROUND:'lower-render'}
REPEAT={WALL:.81,GROUND:1.09}
PALETTE={
    SILL:{'color':[.47,.452,.395],'roughness':.90},
    STEEL:{'color':[.09,.095,.083],'roughness':.61,'metallic':.43},
    **{m:{'color':[1.,1.,1.],'roughness':.93,'texture':str(HERE/(n+'.png')),'normal':str(HERE/(n+'-normal.png'))}
       for m,n in STEMS.items()}}
writer.HERE=HERE;writer.STEMS=STEMS
writer.NORMAL_FILENAMES={m:n+'-normal.png' for m,n in STEMS.items()}
writer.REPEAT_METRES={m:(v,v) for m,v in REPEAT.items()}

def metric_uv(part):
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*REPEAT[part['material']])).tolist()

def generate():
    values=json.loads((HERE.parent/'measurements/surface-readings.json').read_text())['surface_readings']
    side=192
    y,x=np.indices((side,side));u=(x+.5)/side;v=(y+.5)/side
    for i,(material,name) in enumerate(STEMS.items()):
        rng=np.random.default_rng(28002+i)
        tone=np.median([r['median_srgb'] for r in values[name]],axis=0)
        # Independent periodic aggregate and runoff fields. No camera pixels are used as a texture.
        grain=gaussian_filter(rng.normal(size=(side,side)),.58,mode='wrap')
        stipple=gaussian_filter(rng.normal(size=(side,side)),1.75,mode='wrap')
        mottling=writer.field(u,v,9,8,rng)
        rain=writer.field(u,v,28,3,rng) if i else writer.field(u,v,16,9,rng)
        shift=grain*6+stipple*7+mottling*3+rain*(3.5 if i else 1.8)
        color=np.uint8(np.clip(np.rint(tone+shift[:,:,None]),0,255))
        relief=.00046*grain+.0008*stipple
        pitch=REPEAT[material]/side
        dx=(np.roll(relief,-1,axis=1)-np.roll(relief,1,axis=1))/(2*pitch)
        dy=(np.roll(relief,-1,axis=0)-np.roll(relief,1,axis=0))/(2*pitch)
        normals=np.stack([-dx,dy,np.ones_like(dx)],axis=-1)
        normals/=np.linalg.norm(normals,axis=-1,keepdims=True)
        Image.fromarray(color).save(HERE/(name+'.png'))
        Image.fromarray(np.uint8(np.rint(127.5*(1+normals)))).save(HERE/(name+'-normal.png'))

if __name__=='__main__':generate()
