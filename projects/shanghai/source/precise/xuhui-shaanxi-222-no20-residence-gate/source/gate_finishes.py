"""Original repeating surface fields, calibrated against the two No. 20 gate photographs."""
import argparse
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
from residence_gate import WALL,SHAFT,DARK

HERE=Path(__file__).resolve().parent
RECIPES={
    WALL:('enclosure-plaster',(.91,1.06),(195,189,175),(.94,1.9,.9,.7),761),
    SHAFT:('blue-grey-piers',(.76,.96),(100,113,133),(.91,4.0,1.9,1.4),763),
    DARK:('charcoal-doors',(.73,1.19),(33,33,38),(.83,2.6,.85,.47),769)}
FILENAMES={k:v[0]+'.png' for k,v in RECIPES.items()}
NORMAL_FILENAMES={k:v[0]+'-normal.png' for k,v in RECIPES.items()}
PALETTE={k:{'color':[1.,1.,1.],'roughness':v[3][0],'texture':str(HERE/FILENAMES[k]),
            'normal':str(HERE/NORMAL_FILENAMES[k])} for k,v in RECIPES.items()}
# Use the same binary GLB writer as the earlier Shanghai facades. Configure a
# private module, since other model builders use the same implementation.
shared=HERE.parents[1]/'xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('shaanxi_gate_normal_writer',shared)
surface_io=importlib.util.module_from_spec(spec);spec.loader.exec_module(surface_io)
surface_io.HERE=HERE;surface_io.STEMS=FILENAMES;surface_io.NORMAL_FILENAMES=NORMAL_FILENAMES
embed_normals=surface_io.embed_normals

def map_finish(part):
    tile=RECIPES[part['material']][1]
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.array(tile))).tolist()

def draw(name):
    _,(width,height),base,(_,large,medium,small),seed=RECIPES[name]
    n=256
    iy,ix=np.indices((n,n))
    u=(ix+.5)/n;v=(n-.5-iy)/n
    rng=np.random.default_rng(seed);field=surface_io.field
    coarse=field(u,v,4,4,rng)
    if name==DARK:
        grain=field(u,v,42,9,rng)
        fine=field(u,v,123,32,rng)
        bump=.000055*grain+.000028*fine
    else:
        grain=field(u,v,27,24,rng)
        fine=field(u,v,126,128,rng)
        bump=(.00024 if name==SHAFT else .00014)*grain+.00009*fine
    t=large*coarse+medium*grain+small*fine
    color=np.clip(np.rint(np.array(base)+t[:,:,None]),0,255).astype('uint8')
    dx=(np.roll(bump,-1,1)-np.roll(bump,1,1))/(2*width/n)
    down=(np.roll(bump,-1,0)-np.roll(bump,1,0))/(2*height/n)
    norm=np.stack([-dx,down,np.ones_like(dx)],axis=2)
    norm/=np.linalg.norm(norm,axis=2)[:,:,None]
    return Image.fromarray(color),Image.fromarray(np.rint((1+norm)*127.5).astype('uint8'))

def generate(folder):
    folder.mkdir(parents=True,exist_ok=True)
    for name in RECIPES:
        colour,normal=draw(name)
        colour.save(folder/FILENAMES[name],optimize=True)
        normal.save(folder/NORMAL_FILENAMES[name],optimize=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=HERE)
    generate(p.parse_args().output)
