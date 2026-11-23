"""Original tileable colour and normal maps for the court's four measured finishes."""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
source = PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec = importlib.util.spec_from_file_location('metric_glb_writer',source)
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
SCALES = {'exposed red brick':('garden-brick',.49,.292,.91),
          'weathered light stone':('portico-stone',.54,.64,.94),
          'dark foundation stone':('pedestal-stone',.47,.41,.88),
          'deep red door joinery':('painted-wood',.32,.78,.68),
          'weathered flat roof tile':('dormer-tiles',.88,.54,.86)}
writer.HERE = HERE
writer.STEMS = {k:v[0] for k,v in SCALES.items()}
writer.NORMAL_FILENAMES = {k:v[0]+'-normal.png' for k,v in SCALES.items()}
PALETTE = {k:dict(color=[1,1,1],roughness=rough,texture=str(HERE/(stem+'.png')))
           for k,(stem,_,_,rough) in SCALES.items()}


def generate():
    readings=json.loads((HERE.parent/'measurements/surface-colours.json').read_bytes())['readings']
    n=192
    v,u=np.indices((n,n))/n
    for i,(name,(stem,width,height,_)) in enumerate(SCALES.items()):
        rng=np.random.default_rng(32932+i)
        grain=rng.normal(size=(n,n))
        def field(nx,ny):
            # Periodic bilinear interpolation between random knots.
            seeds=rng.normal(size=(ny,nx))
            x=u*nx;y=v*ny
            ix=x.astype(int);iy=y.astype(int)
            fx=x-ix;fy=y-iy
            return ((1-fx)*(1-fy)*seeds[iy,ix]+fx*(1-fy)*seeds[iy,(ix+1)%nx]
                    +(1-fx)*fy*seeds[(iy+1)%ny,ix]+fx*fy*seeds[(iy+1)%ny,(ix+1)%nx])
        cloud=field(7,7)
        base=np.array(readings[name]['median_srgb'])+np.zeros((n,n,3))
        if stem=='garden-brick':
            row=np.floor(v*4).astype(int)
            shifted=u*2+.5*(row%2)
            joint=(np.minimum(shifted%1,1-shifted%1)<.015)|(np.minimum(v*4%1,1-v*4%1)<.049)
            variations=np.array([[-6,7],[-3,4],[8,-5],[3,-4]])[row,np.floor(shifted).astype(int)%2]
            colour=base+(variations+4*cloud+4*grain)[:,:,None]*[1,.79,.63]
            colour[joint]=np.array([112,97,86])+grain[joint,None]*4
            depth=.00075*grain+.0012*cloud-.0038*joint
        elif stem=='dormer-tiles':
            rows=(v*4).astype(int);x=(u*4+.5*(rows%2))%1;y=(v*4)%1
            seam=np.exp(-(np.minimum(x,1-x)/.033)**2)
            lap=np.exp(-(np.minimum(y,1-y)/.057)**2)
            colour=base+(4.5*grain+3*cloud+5*(1-y)-17*seam-23*lap)[:,:,None]*[1,.91,.85]
            depth=.0038*(1-y)-.0031*lap-.0021*seam+.00035*grain
        elif stem=='painted-wood':
            lines=field(67,4)
            colour=base+(2.5*grain+3.8*lines+1.3*cloud)[:,:,None]*[1,.70,.65]
            depth=.00010*grain+.00024*lines
        else:
            aggregate=(grain>1.3).astype(float)
            colour=base+(5.4*grain+5*cloud+5*aggregate)[:,:,None]
            depth=.00040*grain+.00045*aggregate+.00026*cloud
        du=(np.roll(depth,-1,1)-np.roll(depth,1,1))*n/(2*width)
        dv=(np.roll(depth,-1,0)-np.roll(depth,1,0))*n/(2*height)
        normal=np.stack([-du,dv,np.ones_like(du)],axis=-1)
        normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        for suffix,data in [('',colour),('-normal',(normal*.5+.5)*255)]:
            Image.fromarray(np.clip(np.rint(data),0,255).astype('uint8')).save(HERE/(stem+suffix+'.png'),optimize=True)


if __name__=='__main__':
    generate()
