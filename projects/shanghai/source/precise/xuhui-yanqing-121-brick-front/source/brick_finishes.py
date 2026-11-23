"""Original procedural facing brick for the residence at 121 Yanqing Road, Shanghai."""
import argparse
from math import sqrt
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
GREY_BRICK = 'Yanqing 121 | grey Flemish bond'
RED_BAND = 'Yanqing 121 | red soldier course'
HERRINGBONE = 'Yanqing 121 | herringbone spandrel'
REPEAT_METRES = {GREY_BRICK:(1.332,1.020), RED_BAND:(.800,.400),
                 HERRINGBONE:(.64*sqrt(2),.64*sqrt(2))}
FILENAMES = {GREY_BRICK:'gray-flemish.png', RED_BAND:'red-bands.png',
             HERRINGBONE:'red-herringbone.png'}
PALETTE = {name:{'color':[1.,1.,1.],'roughness':rough,'texture':str(HERE/FILENAMES[name])}
           for name,rough in [(GREY_BRICK,.91),(RED_BAND,.84),(HERRINGBONE,.86)]}


def grey_bond(x,z):
    length, header, height = .222, .111, .051
    pitch = length + header
    row = np.floor(z/height).astype(int)
    xx = x + (row%2) * pitch/2
    along = xx%pitch
    short = along >= length
    brick_width = np.where(short,header,length)
    local = np.where(short,along-length,along)
    edge = np.minimum(np.minimum(local,brick_width-local),np.minimum(z%height,height-z%height))
    brick_id = (row%20)*8 + (np.floor(xx/pitch).astype(int)%4)*2 + short.astype(int)
    return edge,brick_id


def soldier_band(x,z):
    width,height = .040,.100
    ax,az = x%width,z%height
    edge = np.minimum(np.minimum(ax,width-ax),np.minimum(az,height-az))
    brick_id = (np.floor(z/height).astype(int)%4)*20 + np.floor(x/width).astype(int)%20
    return edge,brick_id


def herringbone(x,z):
    # In the rotated grid each four-cell run is a whole brick. The two
    # orientations meet squarely; no diagonal mortar line passes through a brick.
    w = .040
    u,v = (z+x)/(w*sqrt(2)),(x-z)/(w*sqrt(2))
    i,j = np.floor(u).astype(int),np.floor(v).astype(int)
    phase = (i+j)%8
    across = phase < 4
    fu,fv = u-i,v-j
    long = np.where(across,phase+fu,phase-4+fv)
    short = np.where(across,fv,fu)
    edge = w*np.minimum(np.minimum(long,4-long),np.minimum(short,1-short))
    start_i = np.where(across,i-phase,i)%16
    start_j = np.where(across,j,j-phase+4)%16
    brick_id = 256*across.astype(int) + 16*start_i + start_j
    return edge,brick_id


def varied_field(x,z,width,height,steps,rng):
    """A small toroidal noise field with smooth interpolation in both directions."""
    nx,nz = steps
    xx,zz = nx*x/width,nz*z/height
    i,j = np.floor(xx).astype(int),np.floor(zz).astype(int)
    ax,az = xx-i,zz-j
    ax = ax*ax*(3-2*ax); az = az*az*(3-2*az)
    grid = rng.normal(size=(nz,nx))
    first = grid[j%nz,i%nx]*(1-ax) + grid[j%nz,(i+1)%nx]*ax
    second = grid[(j+1)%nz,i%nx]*(1-ax) + grid[(j+1)%nz,(i+1)%nx]*ax
    return first*(1-az) + second*az


def draw(name,pixels,pattern,body,mortar,joint,seed):
    width,height = REPEAT_METRES[name]
    n,m = pixels
    iy,ix = np.indices((m,n))
    x,z = width*(ix+.5)/n,height*(m-iy-.5)/m
    edge,ids = pattern(x,z)
    rng = np.random.default_rng(seed)
    fine = rng.normal(0,1.8,edge.shape)
    mottle = varied_field(x,z,width,height,(38,28),rng)
    page = varied_field(x,z,width,height,(5,5),rng)
    batch = rng.normal(0,3.0,int(ids.max())+1)[ids]
    body_tone = fine + 1.9*mottle + 1.2*page + batch
    brick_rgb = np.array(body)[None,None,:] + body_tone[:,:,None]
    joint_rgb = np.array(mortar)[None,None,:] + (fine*.6+1.5*mottle+page)[:,:,None]
    pixel = (width/n+height/m)/2
    distance = edge - joint/2 - np.clip(mottle*.00042,-.0007,.0007)
    body_weight = np.clip(.5+distance/pixel,0.,1.)
    worn_edge = 4.5*np.exp(-((distance-.0016)/.00105)**2)
    brick_rgb += worn_edge[:,:,None]
    rgb = brick_rgb*body_weight[:,:,None] + joint_rgb*(1-body_weight[:,:,None])
    return Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255)))


def generate(directory=HERE):
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    recipes = [(GREY_BRICK,(768,576),grey_bond,[130,129,129],[203,203,202],.0070,121),
               (RED_BAND,(640,320),soldier_band,[149,112,96],[197,176,161],.0049,8121),
               (HERRINGBONE,(512,512),herringbone,[134,94,79],[184,151,130],.0045,5121)]
    for name,pixels,fn,body,mortar,joint,seed in recipes:
        draw(name,pixels,fn,body,mortar,joint,seed).save(directory/FILENAMES[name],optimize=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE)
    generate(parser.parse_args().output)
