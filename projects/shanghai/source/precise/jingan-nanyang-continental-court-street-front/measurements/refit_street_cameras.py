"""Recompute the street plan and camera fit using published numerical observations, NumPy and SciPy."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent

def line_measurements(segments):
    v=segments[:,1]-segments[:,0]
    length=np.linalg.norm(v,axis=1)
    return segments.mean(axis=1),np.column_stack((-v[:,1],v[:,0]))/length[:,None],length

def gravity_error(vanishing,lines):
    centre,normal,length=lines
    direction=vanishing[:2]-centre*vanishing[2]
    return length*np.sum(normal*direction,axis=1)/np.linalg.norm(direction,axis=1)

def fit(data):
    chain=np.array(data['footprint_polyline_local_m']);walk=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(chain,axis=0),axis=1))]
    spl=PchipInterpolator(walk,chain,axis=0)
    def plan(state):
        along=np.linspace(0.,walk[-1],12)+state[:12]
        tangents=spl(along,1);tangents/=np.linalg.norm(tangents,axis=1)[:,None]
        return spl(along)+np.c_[-tangents[:,1],tangents[:,0]]*state[12:24,None]
    cameras={}
    levels=['grade','band','tip']
    for i,(tag,p) in enumerate(data['photos'].items()):
        size=np.array(p['native_size']);scale=512/size[0];obs=p['controls']
        cameras[tag]=dict(row=i,scale=scale,dimensions=size*scale,prior=p['prior_f_512'],sigma=p['focal_sigma'],
                          uv=np.array([x['native_pixel']for x in obs])*scale,
                          pier=np.array([x['pier']for x in obs]),height=np.array([levels.index(x['level'])for x in obs]),
                          fit=line_measurements(np.array(p['fit_verticals_native'])*scale),
                          test=line_measurements(np.array(p['withheld_verticals_native'])*scale))
    pairs=[]
    for record in data['stereo_pairs']:
        ca,cb=record['photos'];uv=np.array(record['observations_native_xyxy']);ones=np.ones(len(uv))
        pairs.append((ca,cb,np.c_[uv[:,:2]*cameras[ca]['scale'],ones],np.c_[uv[:,2:]*cameras[cb]['scale'],ones]))
    def optical(state,cam):
        start=26+9*cam['row'];q=state[start:start+9];R=Rotation.from_rotvec(q[:3]).as_matrix()
        cx,cy=cam['dimensions']/2+q[7:9];K=np.array([[q[6],0,cx],[0,q[6],cy],[0,0,1.]])
        return R,q[3:6],K,q
    def project(P,xyz):
        pp=np.c_[xyz,np.ones(len(xyz))]@P.T
        return pp[:,:2]/pp[:,2,None]
    def residual(state):
        xy=plan(state);z=np.r_[0.,state[24:26]];cal={};out=[]
        for tag,cam in cameras.items():
            R,t,K,q=optical(state,cam);cal[tag]=(R,t,K);h=cam['height']
            p=np.c_[xy[cam['pier']],z[h]];e=project(K@np.c_[R,t],p)-cam['uv']
            e/=np.choose(h,[3.5,3.,1.35])[:,None];e[h!=2,0]*=.22
            out.extend(e.ravel());out.extend([(q[6]-cam['prior'])/cam['sigma'],q[7]/25,q[8]/35])
        south=data['external_south_bay'];ratio=np.linalg.norm(xy[-1]-xy[-2])/south['reference_width']
        out.extend((state[24:26]-ratio*np.array([south['shop_course'],south['crown']]))/south['sigmas'])
        for tag,cam in cameras.items():
            R,_,K=cal[tag];out.extend(gravity_error(K@R[:,2],cam['fit'])/.31)
        for ca,cb,a,b in pairs:
            ra,ta,ka=cal[ca];rb,tb,kb=cal[cb];relative=rb@ra.T;x,y,z0=tb-relative@ta
            skew=np.array([[0,-z0,y],[z0,0,-x],[-y,x,0]])
            F=np.linalg.solve(kb.T,skew@relative)@np.linalg.inv(ka);lb=a@F.T;la=b@F
            out.extend(np.sum(lb*b,axis=1)/np.sqrt(np.sum(lb[:,:2]**2+la[:,:2]**2,axis=1))/.48)
        out.extend((state[:12]-np.r_[.30,np.zeros(10),-.30])/np.r_[.33,np.ones(10)*1.5,.33])
        out.extend(state[12:24]/.55);out.extend(np.diff(state[:12],2))
        out.extend([(state[24]-5.6)/1.5,(state[25]-20.6)/2.6]);return out
    result=least_squares(residual,np.array(data['initial_parameters']),loss='soft_l1',f_scale=1.6,x_scale='jac',max_nfev=180)
    state=result.x;xy=plan(state);elevations=np.r_[0.,state[24:26]]
    summary={'axes_m':xy.tolist(),'levels_m':elevations.tolist(),'cameras':{}}
    for tag,cam in cameras.items():
        R,t,K,_=optical(state,cam);P=K@np.c_[R,t];P[:2]/=cam['scale']
        p=np.c_[xy[cam['pier']],elevations[cam['height']]]
        read=project(P,p);saved=project(np.array(data['photos'][tag]['P_native']),p)
        v=abs(gravity_error(K@R[:,2],cam['test']))/cam['scale']
        summary['cameras'][tag]=dict(eye_local_m=(-R.T@t).tolist(),P_native=P.tolist(),
            maximum_difference_from_published_projection_px=float(np.linalg.norm(read-saved,axis=1).max()),
            withheld_verticals=len(v),withheld_end_to_end_angular_drift_px=np.percentile(v,[50,90]).tolist(),
            fitted_control_distance_px=np.percentile(np.linalg.norm(read-cam['uv']/cam['scale'],axis=1),[50,90]).tolist())
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    args=parser.parse_args();summary=fit(json.loads((HERE/'street-photo-registration.json').read_text()))
    args.output.write_text(json.dumps(summary,indent=2)+'\n')
    for tag,cam in summary['cameras'].items():print(tag,cam['maximum_difference_from_published_projection_px'],cam['withheld_end_to_end_angular_drift_px'])
