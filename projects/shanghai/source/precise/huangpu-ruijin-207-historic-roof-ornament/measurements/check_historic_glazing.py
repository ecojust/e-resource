"""Compare the first surface of the exported historical bay to original film coordinates."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from historic_central_glazing import native,DARK,LINTEL,RECESS,PANEL,GLASS
from rosholt_front_plane import PROJECTION
from glb_triangles import SerialScene,first_hit

def samples():
    for xi,(lo,hi) in enumerate([(4,15),(16,29),(31,45),(47,59)]):
        for yi,(top,bottom)in enumerate([(432,449),(453,471),(475,483)]):
            for f in [.32,.68]:
                yield 'pane '+str(xi+1)+'.'+str(yi+1),native(lo+f*(hi-lo),top+.48*(bottom-top)),GLASS,1
    # Independent horizontal bands and column runs between the profile cuts.
    for i,x in enumerate([15.5,30.,46.1]):
        for j,y in enumerate([435.,445.5,455.,465.5,480.2]):yield f'vertical bar {i+1}.{j+1}',native(x,y),[DARK],1
    for i,y in enumerate([430.1,451.2,473.0,484.6]):
        for j,x in enumerate([7.2,22.7,37.2,54.]):yield f'horizontal bar {i+1}.{j+1}',native(x,y),[DARK],1
    for i,x in enumerate([5.,14.,29.,44.,57.]):yield f'grey head {i+1}',native(x,425.),[LINTEL],2
    for i,y in enumerate([437.,446.,455.,466.,480.,490.]):
        yield f'west side lining {i+1}',native(1.1,y),[RECESS],2
        yield f'east side lining {i+1}',native(65.1,y),[RECESS],2
    for i,x in enumerate([6.,14.,24.,34.,46.,56.]):yield f'lower dark field {i+1}',native(x,490.),[PANEL],2
def inspect(model):
    s=SerialScene(model);cam=PROJECTION;inv=np.linalg.inv(cam[:,:3]);eye=-inv@cam[:,3];p=s.tri@cam[:,:3].T+cam[:,3];den=p[:,:,2];valid=den.min(1)>0.;cross=(den.min(1)<=0.)&(den.max(1)>0.);uv=p[:,:,:2]/np.where(np.abs(den)>1e-12,den,1e-12)[:,:,None];lo=uv.min(1);hi=uv.max(1);out=[]
    for name,pixel,mat,delta in samples():
        px=np.rint(pixel).astype(int);ii=np.flatnonzero(cross|(valid&(lo<=px+delta+.001).all(1)&(hi>=px-delta-.001).all(1)))
        def surface(dx,dy):
            ray=inv@np.r_[px+[dx,dy],1.];ray/=np.linalg.norm(ray);idx=ii[s.cross[ii]@ray<0]
            if not len(idx):return None
            j,t,_=first_hit(s.tri[idx],eye,ray)
            return s.materials[s.mi[idx[j]]]if np.isfinite(t)else None
        first=surface(0,0);off=[0,0] if first in mat else None
        if off is None:
            choices=sorted((dx*dx+dy*dy,dx,dy)for dx in range(-delta,delta+1)for dy in range(-delta,delta+1)if 0<dx*dx+dy*dy<=delta*delta)
            for _,dx,dy in choices:
                if surface(dx,dy)in mat:off=[dx,dy];break
        out.append(dict(feature=name,native_pixel=px.tolist(),expected=mat,actual=first,radius_px=delta,matching_offset=off))
    return dict(asset=s.asset,triangles=len(s.tri),count=len(out),exact=sum(r['matching_offset']==[0,0]for r in out),near=sum(r['matching_offset']is not None for r in out),samples=out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=inspect(a.model);a.output.write_text(json.dumps(r,indent=1,ensure_ascii=False)+'\n');print(r['asset']['file'],r['count'],r['exact'],r['near'])
