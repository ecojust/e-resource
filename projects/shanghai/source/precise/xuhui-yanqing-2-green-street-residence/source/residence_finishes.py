"""Periodic roughcast, painted base and weathered clay roof tiles at No. 2 Yanqing Road."""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image
from central_stair import WALL, BASE

HERE = Path(__file__).resolve().parent
TILE = 'Yanqing 2 | red clay roof tile'
# Physical repeat and reference colours. Window surrounds and exposed geometry use solid finishes.
SURFACES = {
    WALL: ('celadon-roughcast', (.86,.86), (146,157,137), .95),
    BASE: ('painted-plinth', (.68,.68), (70,65,64), .91),
    TILE: ('weathered-clay-tiles', (1.20,1.08), (135,68,48), .89),
}
shared = HERE.parents[1]/'xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec = importlib.util.spec_from_file_location('yanqing_surface_writer',shared)
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
writer.HERE = HERE
writer.STEMS = {name: recipe[0] for name,recipe in SURFACES.items()}
writer.NORMAL_FILENAMES = {name: recipe[0]+'-normal.png' for name,recipe in SURFACES.items()}
embed_normals = writer.embed_normals
PALETTE = {name: dict(color=[1.,1.,1.],roughness=roughness,texture=str(HERE/(stem+'.png')),
                     normal=str(HERE/(stem+'-normal.png')))
           for name,(stem,_,rgb,roughness) in SURFACES.items()}

def map_finish(part):
    size = np.array(SURFACES[part['material']][1])
    uv = np.array(part['texcoords'])/.78
    if part['material'] == TILE:
        # The long ridges run down the roof slope; UVs in metres follow each individual roof plane.
        v = np.asarray(part['vertices'])
        ids = np.asarray(part['triangles'])
        for face in ids:
            a,b,c = v[face]
            normal = np.cross(b-a,c-a)
            normal /= np.linalg.norm(normal)
            if normal[2] < .2:
                continue
            across = np.array([-normal[1],normal[0],0.])
            if np.linalg.norm(across) < 1e-6:
                continue
            across /= np.linalg.norm(across)
            up = np.cross(normal,across)
            uv[face] = np.column_stack([v[face]@across,v[face]@up])
    part['texcoords'] = (uv/size).tolist()

def make(name):
    stem,(width,height),base,_ = SURFACES[name]
    n = 256; row,col = np.indices((n,n))
    u = (col+.5)/n; v = (n-.5-row)/n
    rng = np.random.default_rng({WALL:8021,BASE:8023,TILE:8027}[name])
    coarse = writer.field(u,v,5,5,rng)
    grain = writer.field(u,v,70,66,rng)
    fine = rng.normal(size=(n,n))
    tint = 2.4*coarse+1.2*grain+.7*fine
    relief = .00012*grain+.00007*fine
    if name == WALL:
        relief += .00029 * np.maximum(0,grain)
        tint += 1.25*grain
    elif name == TILE:
        cross = u*6; course = v*4
        roll = (.5+.5*np.cos(2*np.pi*cross))**2
        lap = course % 1
        batch = rng.normal(0,4.5,(4,6))[(course.astype(int)%4),(cross.astype(int)%6)]
        tint = 4*coarse + 2.4*grain + 1.1*fine + batch + 8*roll - 16*np.exp(-lap*26)
        relief = .008*roll + .0035*(1-lap) - .001*np.exp(-lap*24) + .00012*grain
    colour = np.clip(np.rint(np.array(base)+tint[...,None]),0,255).astype('uint8')
    dx = (np.roll(relief,-1,1)-np.roll(relief,1,1))/(2*width/n)
    dy = (np.roll(relief,-1,0)-np.roll(relief,1,0))/(2*height/n)
    normals = np.stack((-dx,dy,np.ones_like(dx)),axis=-1)
    normals /= np.linalg.norm(normals,axis=2)[...,None]
    return Image.fromarray(colour),Image.fromarray(np.rint((normals+1)*127.5).astype('uint8'))

def generate(output):
    output.mkdir(parents=True,exist_ok=True)
    for name,(stem,*_) in SURFACES.items():
        diffuse,normal = make(name)
        diffuse.save(output/(stem+'.png'),optimize=True)
        normal.save(output/(stem+'-normal.png'),optimize=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE)
    generate(parser.parse_args().output)
