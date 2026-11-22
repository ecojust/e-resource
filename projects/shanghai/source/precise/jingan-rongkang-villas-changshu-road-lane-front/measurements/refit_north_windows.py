"""Refit the northern street windows against the independent view from beyond the lane gate."""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.optimize import least_squares
from read_street_windows import fields,P,fit_facade
S=Path(__file__).resolve().parent
def fit():
    camera=json.loads((S/'independent-north-window-station.json').read_bytes())
    first='north-block-n21';second='north-block-s21';third=camera['facade_source'];views={**P,third:np.array(camera['local_xyz_to_image'])}
    marks=camera['marks']
    ids=[k for k in fields if k.startswith('N-') and 'return' not in k]
    older,initial=fit_facade(ids,'north-front',7)
    initial_map={o['id']:o for o in initial}
    obs={}
    for key in ids:
        a=initial_map[key];obs[key]={**a['observed'],third:marks.get(key,[None]*4)}
    def solve(use):
        def coords(params,k):
            l,r,b,t=params[2+4*k:6+4*k]
            return np.array([[u,params[0]+params[1]*(u-7),z,1]for u,z in [(l,t),(r,t),(r,b),(l,b)]])
        def residual(params):
            err=[]
            for i,k in enumerate(ids):
                c=coords(params,i)
                for view,pts in obs[k].items():
                    if view not in use:continue
                    hit=c@views[view].T;p=hit[:,:2]/hit[:,2:]
                    for j,pt in enumerate(pts):
                        if pt is not None:err.extend(p[j]-pt)
            return np.array(err)
        pars=[older['frame_plane'],older['depth_slope']]
        for k in ids:pars.extend([initial_map[k][f]for f in ('u0','u1','z0','z1')])
        params=least_squares(residual,pars,loss='soft_l1',f_scale=2.4).x
        return params,coords,residual
    allp,coords,res=solve([first,second,third]);idx={k:i for i,k in enumerate(ids)}
    comparisons={}
    for pair in ((first,second),(first,third),(second,third)):
        p,_,r=solve(pair)
        comparisons[' + '.join(pair)]={'frame_y_at_x7_m':round(float(p[0]),4),'slope_dy_dx':round(float(p[1]),5),'fitted_coordinate_rms_px':round(float(np.sqrt(np.mean(r(p)**2))),3)}
    output=[]
    for i,k in enumerate(ids):
        entry=initial_map[k]
        entry.update(dict(zip(('u0','u1','z0','z1'),np.round(allp[2+4*i:6+4*i],4))))
        entry['observed']=obs[k];xyz=coords(allp,i);dists=[]
        for view,pts in obs[k].items():
            q=xyz@views[view].T;uv=q[:,:2]/q[:,2:];dists.extend(float(np.linalg.norm(uv[j]-pt)) for j,pt in enumerate(pts)if pt is not None)
        entry['mean_projection_error_px']=round(np.mean(dists),2);entry['max_projection_error_px']=round(max(dists),2)
        output.append(entry)
    return dict(axis='X',local_reference=7,frame_plane=round(allp[0],5),depth_slope=round(allp[1],5),error_rms_px=round(float(np.sqrt(np.mean(res(allp)**2))),3)),output,comparisons

def update_book(book):
    face,updates,comparisons=fit();book['surfaces']['north-front']=face
    repl={o['id']:o for o in updates}
    book['openings']=[repl.get(o['id'],o) for o in book['openings']]
    book['north_facade_third_station']=dict(source='independent-north-window-station.json',sha256=hashlib.sha256((S/'independent-north-window-station.json').read_bytes()).hexdigest(),method='February 2021 reverse view, camera fixed to its surveyed position and 2.32 m height. The right part of the gate supplies five image marks and nine plumb edges constrain roll. The six northern front openings alone are refitted jointly at all three fixed camera positions. The returned side and southern wall retain their original two-view solution.',pairwise_fits=comparisons)
    return book

if __name__=='__main__':
    name=S/'street-window-openings.json';book=update_book(json.loads(name.read_bytes()))
    name.write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n')
