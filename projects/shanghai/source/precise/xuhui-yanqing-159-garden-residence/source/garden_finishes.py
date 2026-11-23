"""Generate the pebbledash, pale render and street gate pier finishes of 159 Yanqing Road."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
PEBBLEDASH='Yanqing 159 | grey-brown exposed aggregate'
IVORY_RENDER='Yanqing 159 | ivory cement render'
GATE_GREY='Yanqing 159 | dark grey boundary pier'
REPEAT_METRES={PEBBLEDASH:(.384,.384),IVORY_RENDER:(.64,.64),GATE_GREY:(.80,.80)}
FILENAMES={PEBBLEDASH:'grey-brown-pebbledash.png',IVORY_RENDER:'ivory-render.png',GATE_GREY:'gate-grey.png'}
PALETTE={name:{'color':[1.,1.,1.],'texture':str(HERE/fn),'roughness':rough}
         for (name,fn),rough in zip(FILENAMES.items(),(.91,.89,.78))}


def periodic_noise(n,count,rng):
    iy,ix=np.indices((n,n));x=(ix+.5)*count/n;y=(iy+.5)*count/n
    i=x.astype(int);j=y.astype(int);u=x-i;v=y-j
    u=u*u*(3-2*u);v=v*v*(3-2*v)
    grid=rng.normal(size=(count,count))
    return ((1-u)*(1-v)*grid[j%count,i%count]+u*(1-v)*grid[j%count,(i+1)%count]
            +(1-u)*v*grid[(j+1)%count,i%count]+u*v*grid[(j+1)%count,(i+1)%count])


def image(data):
    return Image.fromarray(np.uint8(np.clip(np.rint(data),0,255)))


def pebbledash():
    n=480;rng=np.random.default_rng(159)
    base=np.array([122.,115.,101.]);binder=base+periodic_noise(n,11,rng)[:,:,None]*3.8
    binder+=periodic_noise(n,51,rng)[:,:,None]*2.3
    sheet=image(binder);draw=ImageDraw.Draw(sheet)
    stones=np.array([[169,163,145],[143,134,116],[113,105,89],
                     [152,145,134],[97,93,81],[181,175,157],[133,128,117]])
    # Each grain is an independent irregular pebble. Periodic copies allow a single
    # chip to cross a tile boundary. The generated albedo contains no directional shadow.
    for _ in range(9700):
        x,y=rng.uniform(0,n,2);a=rng.uniform(1.05,3.6);b=a*rng.uniform(.60,1.)
        theta=rng.uniform(0,np.pi);c,s=np.cos(theta),np.sin(theta)
        scale=rng.uniform(.80,1.11,7);angles=np.arange(7)*2*np.pi/7+rng.uniform(0,.7)
        dx=a*np.cos(angles)*scale;dy=b*np.sin(angles)*scale
        xx=x+c*dx-s*dy;yy=y+s*dx+c*dy
        rgb=tuple(np.uint8(np.clip(stones[rng.integers(len(stones))]+rng.normal(0,5),0,255)))
        xs=[0]+([n]if xx.min()<0 else [])+([-n]if xx.max()>=n else [])
        ys=[0]+([n]if yy.min()<0 else [])+([-n]if yy.max()>=n else [])
        for ox in xs:
            for oy in ys:draw.polygon(list(zip(xx+ox,yy+oy)),fill=rgb)
    mineral_grain=rng.normal(0,2.9,(n,n))+periodic_noise(n,76,rng)*1.45
    return image(np.array(sheet,dtype=float)+mineral_grain[:,:,None])


def render(n,seed,base,grain):
    rng=np.random.default_rng(seed);cloud=periodic_noise(n,7,rng)*1.35+periodic_noise(n,41,rng)*.74
    return image(np.array(base)[None,None,:]+(cloud+rng.normal(0,grain,(n,n)))[:,:,None])


def generate(directory=HERE):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    sheets={PEBBLEDASH:pebbledash(),IVORY_RENDER:render(240,216,[210,203,178],1.35),
            GATE_GREY:render(192,113,[61,73,75],.9)}
    for name,sheet in sheets.items():sheet.save(directory/FILENAMES[name],optimize=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=HERE)
    generate(parser.parse_args().output)
