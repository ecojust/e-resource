"""Refit the three face homographies from published native-pixel controls alone."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

def refit(study):
    names=list(study['views'])
    data=[]
    initials=[]
    for name in names:
        view=study['views'][name]
        w,h=view['original_dimensions']
        # First two stations were sampled at native resolution. The derelict
        # view was sampled at 760 wide and is weighted at that precision.
        scale=760/w if name=='earlier-oblique' else 1
        pts=[]; design=[];obs=[]
        for section,level in [('base',0),('deck',1),('cap',1.61)]:
            for i,pt in enumerate(view['controls'][section]):
                if not pt: continue
                uv=np.asarray(pt['uv'])*scale;u,v=uv
                design.extend([[i,level,1,0,0,0,-i*u,-level*u],[0,0,0,i,level,1,-i*v,-level*v]])
                obs.extend(uv);pts.append((section,i,uv))
        initials.extend(np.linalg.lstsq(design,obs,rcond=None)[0])
        data.append((name,scale,pts))
    def split(t):
        return [np.append(t[8*j:8*j+8],1).reshape(3,3) for j in range(3)],np.r_[0,t[24:30],7],t[-1]
    def errors(t):
        H,axes,cap=split(t);r=[]
        for plane,(_,_,pts) in zip(H,data):
            for typ,i,uv in pts:
                xy=plane@[axes[i],dict(base=0,deck=1,cap=cap)[typ],1];r.extend(xy[:2]/xy[2]-uv)
        return r
    start=np.r_[initials,np.arange(1,7),1.61]
    opt=least_squares(errors,start,loss='soft_l1',f_scale=2,max_nfev=900)
    hs,axes,cap=split(opt.x);out={}
    for h,(name,scale,pts) in zip(hs,data):
        native=np.diag([1/scale,1/scale,1])@h
        errors_px=[]
        for typ,i,uv in pts:
            v=native@[axes[i],dict(base=0,deck=1,cap=cap)[typ],1]
            errors_px.append(float(np.linalg.norm(v[:2]/v[2]-uv/scale)))
        out[name]={'H_local_plane_to_native':native.tolist(),'count':len(pts),
                   'median_error_px':float(np.median(errors_px)),'max_error_px':max(errors_px)}
    return {'axis_positions':axes.tolist(),'cap_fraction':float(cap),'views':out}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=Path(__file__).with_name('arcade-photograph-registration.json'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    d=refit(json.loads(a.input.read_text()));a.output.write_text(json.dumps(d,indent=2)+'\n')
