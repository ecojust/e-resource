"""Build original, repeating masonry finishes from procedural grains and mortar."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

from material_names import DARK, PLASTER, RED, TEXTURES


def noise(rng, shape, blur):
    a = gaussian_filter(rng.normal(size=shape), blur, mode='wrap')
    return a / a.std()


def bricks(rng, base, mortar, destination):
    shape=(384,768)
    y,x=np.indices(shape,dtype=float)
    course=(y//24).astype(int)
    along=x+(course%2)*48
    col=(along//96).astype(int)%8
    u,v=along%96,y%24
    edge=np.minimum.reduce([u,96-u,v,24-v])+noise(rng,shape,.8)*.65
    fine=noise(rng,shape,.55)*2.8+noise(rng,shape,3.1)*1.8
    variation=rng.normal(0,7.5,(16,8,1))+rng.normal(0,2.1,(16,8,3))
    bed=np.asarray(mortar)+(fine*1.1+noise(rng,shape,8)*2)[:,:,None]
    brick=np.asarray(base)+variation[course,col]+(fine+noise(rng,shape,9)*2.3)[:,:,None]
    blend=np.clip((edge-.8)/1.65,0,1)[:,:,None]
    Image.fromarray(np.clip(bed*(1-blend)+brick*blend,0,255).astype('uint8')).save(destination,quality=90,subsampling=0)


def pebble(rng):
    shape=(512,512)
    y,x=np.indices(shape,dtype=float);uv=np.column_stack([x.ravel(),y.ravel()])
    cells=rng.uniform(0,512,(6500,2));tree=cKDTree(cells,boxsize=512.)
    dist,idx=tree.query(uv,k=2)
    near=idx[:,0];d0,d1=dist.T
    relief=np.clip((d1-d0)/2.7,0,1)
    delta=(uv-cells[near]+256)%512-256
    light=3.6*np.clip((-delta[:,0]*.5-delta[:,1]*.8)/2.,-2,2)
    colors=np.asarray([[125,115,101],[151,144,133],[109,104,101],[164,149,129],[93,86,79],[171,165,153]])
    chip=colors[rng.choice(len(colors),len(cells),p=[.25,.21,.19,.14,.10,.11])][near]+(rng.normal(0,5,len(cells))[near]+light)[:,None]
    base=np.array([97,89,81])+(noise(rng,shape,1.15).ravel()*3)[:,None]
    grain=(noise(rng,shape,.52)*3.2+noise(rng,shape,9.)*2).ravel()
    img=base*(1-relief[:,None])+chip*relief[:,None]+grain[:,None]
    Image.fromarray(np.clip(img,0,255).reshape(512,512,3).astype('uint8')).save(TEXTURES[PLASTER],quality=92,subsampling=0)


if __name__=='__main__':
    rng=np.random.default_rng(193208)
    bricks(rng,[153,87,64],[159,124,98],TEXTURES[RED])
    bricks(rng,[127,77,63],[127,98,80],TEXTURES[DARK])
    pebble(rng)
