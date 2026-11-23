"""Repeatable cream roughcast, smoother coping and weathered paving. No photographs are embedded."""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image
from central_front import PLASTER, COPING, TERRACE

HERE=Path(__file__).resolve().parent
SURFACES={
    PLASTER:('garden-cream-roughcast',3.16, (198,193,174),.95,.00061,8081),
    COPING:('garden-aged-coping',2.64, (211,207,194),.88,.00021,8082),
    TERRACE:('garden-terrace-stone',2.36,(147,144,128),.91,.00039,8083),
}
shared=HERE.parents[1]/'xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('garden_normal_maps',shared)
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
writer.HERE=HERE;writer.STEMS={name:v[0] for name,v in SURFACES.items()}
writer.NORMAL_FILENAMES={k:v[0]+'-normal.png' for k,v in SURFACES.items()}
embed_normals=writer.embed_normals
PALETTE={k:dict(color=[1.,1.,1.],roughness=v[3],texture=str(HERE/(v[0]+'.png')),
                normal=str(HERE/(v[0]+'-normal.png'))) for k,v in SURFACES.items()}

def map_finish(part):
    repeat=SURFACES[part['material']][1]
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*repeat)).tolist()

def generate(output):
    n=256;iy,ix=np.indices((n,n));u=(ix+.5)/n;v=(n-.5-iy)/n
    output.mkdir(exist_ok=True,parents=True)
    for name,(stem,repeat,base,rough,grain,seed) in SURFACES.items():
        rng=np.random.default_rng(seed)
        broad=writer.field(u,v,9,11,rng);fine=writer.field(u,v,92,77,rng)
        trowel=writer.field(u,v,24,39,rng);sand=rng.normal(0,1,(n,n))
        tone=.45*broad+.49*trowel+1.1*fine+.59*sand
        relief=grain*fine+grain*.37*trowel+grain*.23*sand
        colour=np.rint(np.clip(np.asarray(base)+tone[...,None],0,255)).astype('uint8')
        dx=(np.roll(relief,-1,1)-np.roll(relief,1,1))*n/(2*repeat)
        dv=(np.roll(relief,-1,0)-np.roll(relief,1,0))*n/(2*repeat)
        normal=np.stack([-dx,dv,np.ones_like(dx)],axis=2)
        normal/=np.linalg.norm(normal,axis=2)[...,None]
        Image.fromarray(colour).save(output/(stem+'.png'),optimize=True)
        Image.fromarray(np.rint((1+normal)*127.5).astype('uint8')).save(output/(stem+'-normal.png'),optimize=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default=HERE,type=Path)
    generate(parser.parse_args().output)
