"""Use the two outward-facing February 2015 stations to check leaf and return-fence depth."""
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from fit_gate import street_rotation
D=Path(__file__).parent

def solve():
    obs=json.loads((D/'gate-return-observations.json').read_bytes());front=json.loads((D/'gate-cameras.json').read_bytes())
    origin=front['origin_wgs84'];p=front['parameters'];theta=p['bearing_rad'];ax=np.array([[np.sin(theta),-np.cos(theta),0],[np.cos(theta),np.sin(theta),0],[0,0,1.]])
    m=np.array([111320*np.cos(np.deg2rad(origin[1])),111130]);w=p['pier_width'];dd=p['axes_distance'];h=p['plain_cap']
    targets={'back_cap':[-dd,w,h],'back_base':[-dd,w,0],'lamp':[-dd,w/2,h+p['globe_center_above_cap']],'right_base':[0,w,0]}
    cams={}
    for n,v in obs['views'].items():
        ww,hh=v['size'];f=ww*.5/np.tan(np.deg2rad(v['hfov'])/2)
        k=np.array([[f,0,ww/2],[0,f,hh/2],[0,0,1.]])
        c=ax.T@np.r_[m*(np.asarray(v['center_wgs84'])-origin),v['height_m']]
        r=street_rotation(v['yaw'],v['pitch'])@ax
        def evalpose(q):
            return c+q[:3],Rotation.from_rotvec(np.deg2rad(q[3:])).as_matrix()@r
        def res(q):
            cc,rr=evalpose(q);out=[]
            for label,uv in obs['fixed_pier'][n].items():
                z=k@rr@(targets[label]-cc);out.extend((z[:2]/z[2]-uv)/(6 if label=='right_base' else 3))
            return [*out,*(q[:3]/[.40,.40,.2]),*(q[3:]/[1.,1.,.55])]
        fit=least_squares(res,np.zeros(6),loss='soft_l1');cc,rr=evalpose(fit.x)
        cams[n]=[cc,rr,k]
    result={}
    for name,vals in obs['paired_features'].items():
        origins=[];dirs=[]
        for (cc,r,k),uv in zip(cams.values(),vals):
            if not uv:continue
            ray=r.T@np.linalg.solve(k,[*uv,1]);ray/=np.linalg.norm(ray);origins.append(cc);dirs.append(ray)
        if len(origins)<2:continue
        mats=[np.eye(3)-np.outer(d,d)for d in dirs];xyz=np.linalg.solve(sum(mats),sum(a@c for a,c in zip(mats,origins)))
        distances=[float(np.linalg.norm(a@(xyz-c)))for a,c in zip(mats,origins)]
        result[name]={'observed_work_pixels':vals,'triangulated_m':xyz.tolist(),'closest_ray_offsets_m':distances}
    return {'points':result,'stations':{n:dict(C=c.tolist(),R=r.tolist(),K=k.tolist())for n,(c,r,k)in cams.items()}}
if __name__=='__main__':
    import argparse
    c=argparse.ArgumentParser(description=__doc__);c.add_argument('out',type=Path);a=c.parse_args();d=solve();a.out.write_text(json.dumps(d,indent=2)+'\n');print({k:np.round(v['triangulated_m'],2).tolist()for k,v in d['points'].items()})
