"""Locate two north-facing windows on the southern house, including partly hidden corners."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares


def append_inner(table):
    record=json.loads(Path(__file__).with_name('south-inner-window-stations.json').read_bytes())
    cams={name:np.array(v['local_xyz_to_image']) for name,v in record['sources'].items()}
    weak=record['relative_views']
    names=['S-inner-return3','S-inner-return2']
    def projected(params,idx,station):
        low,high,b,t=params[1+idx*4:5+idx*4];x=params[0]
        points=[[x,low,t,1],[x,high,t,1],[x,high,b,1],[x,low,b,1]]
        uv=np.array(points)@cams[station].T
        uv=uv[:,:2]/uv[:,2,None]
        if station in weak:
            i=weak.index(station)
            uv=uv+params[9+i*2:11+i*2]
        return uv
    def res(params):
        values=[(params[0]-record['plane_prior_x'])/record['sigma_m']*4]
        for station,marks in record['observed'].items():
            for i,name in enumerate(names):
                if name not in marks:continue
                obs=np.array(marks[name],dtype=float)
                diff=projected(params,i,station)-obs
                weights=np.array(record['weights'][station][name])
                valid=np.isfinite(diff)&(weights>0)
                values.extend((diff*weights)[valid])
        return values
    init=[-1.77,2.2,3.15,6.65,7.8,2.2,3.15,3.85,5.0,0,0,0,0]
    p=least_squares(res,init,loss='soft_l1',f_scale=3).x
    facet='south-inner-return'
    table['surfaces'][facet]=dict(axis='Y',local_reference=2.7,frame_plane=round(p[0],5),depth_slope=0.0,
        inward_sign=-1,error_rms_px=round(float(np.mean(np.square(res(p)[1:]))**.5),2),
        note='The visible face looks north toward the southern lane entrance. Positive frame depth points toward negative X.')
    table['south_inner_registration']={'source':'south-inner-window-stations.json','relative_photo_shifts_px':{k:p[9+i*2:11+i*2].round(3).tolist() for i,k in enumerate(weak)}}
    for i,name in enumerate(names):
        errors=[];obs={}
        for cam,marks in record['observed'].items():
            if name not in marks:continue
            obs[cam]=marks[name];diff=projected(p,i,cam)-np.array(marks[name],dtype=float)
            errors.extend(np.linalg.norm(diff[np.isfinite(diff).all(1)],axis=1))
        l,r,b,t=p[1+4*i:5+4*i]
        table['openings'].append(dict(id=name,facade=facet,u0=round(l,4),u1=round(r,4),z0=round(b,4),z1=round(t,4),frame='pale',
            horizontal_divisions=[],vertical_divisions=[.5],upper_undivided=False,front_pair=False,
            mean_projection_error_px=round(float(np.mean(errors)),2),max_projection_error_px=round(float(np.max(errors)),2),observed=obs,
            limit='Two pale lights share a vertical stile. The lane sign and rail obscure the lower edge in December 2015, and the 2019 photograph exposes only the head of the lower window.' if name.endswith('2') else 'A sloping ray sees the two lights between the tree and the lane opening. The window hardware and hinge angle are obscured.'))
    return table
