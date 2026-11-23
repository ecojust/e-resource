"""Original repeatable colour and tangent normal maps for three rendered plaster surfaces."""
import argparse,importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
from court_masonry import WALL,FENCE
from no6_loggia import ROSE
HERE=Path(__file__).resolve().parent
SURFACES={WALL:('qixia-buff-front',(3.12,3.12),(205,196,166),.94,8041,.00030),
          FENCE:('qixia-court-ochre',(2.84,2.84),(193,177,130),.93,8043,.00022),
          ROSE:('qixia-rose-loggia',(2.44,2.44),(150,104,91),.90,8045,.00013)}
shared=HERE.parents[1]/'xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('qixia_normal_writer',shared)
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
writer.HERE=HERE;writer.STEMS={k:v[0] for k,v in SURFACES.items()}
writer.NORMAL_FILENAMES={k:v[0]+'-normal.png' for k,v in SURFACES.items()}
embed_normals=writer.embed_normals
PALETTE={k:dict(color=[1.,1.,1.],roughness=v[3],texture=str(HERE/(v[0]+'.png')),
                normal=str(HERE/(v[0]+'-normal.png')))for k,v in SURFACES.items()}

def map_finish(part):
    tile=np.array(SURFACES[part['material']][1])
    part['texcoords']=(np.array(part['texcoords'])/(.78*tile)).tolist()

def generate(output):
    output.mkdir(parents=True,exist_ok=True)
    n=256;iy,ix=np.indices((n,n));u=(ix+.5)/n;v=(n-.5-iy)/n
    for name,(stem,(width,height),base,rough,seed,grain) in SURFACES.items():
        rng=np.random.default_rng(seed);coarse=writer.field(u,v,11,9,rng)
        brush=writer.field(u,v,47,31,rng);aggregate=writer.field(u,v,94,91,rng)
        fine=rng.normal(0,1,(n,n));tone=.38*coarse+.52*brush+1.15*aggregate+.65*fine
        relief=grain*aggregate+.00008*fine+.00014*brush
        colour=np.rint(np.clip(np.array(base)+tone[...,None],0,255)).astype('uint8')
        dx=(np.roll(relief,-1,axis=1)-np.roll(relief,1,axis=1))*n/(2*width)
        down=(np.roll(relief,-1,axis=0)-np.roll(relief,1,axis=0))*n/(2*height)
        normal=np.stack((-dx,down,np.ones_like(dx)),axis=2);normal/=np.linalg.norm(normal,axis=2)[...,None]
        Image.fromarray(colour).save(output/(stem+'.png'),optimize=True)
        Image.fromarray(np.rint((normal+1)*127.5).astype('uint8')).save(output/(stem+'-normal.png'),optimize=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=HERE)
    generate(p.parse_args().output)
