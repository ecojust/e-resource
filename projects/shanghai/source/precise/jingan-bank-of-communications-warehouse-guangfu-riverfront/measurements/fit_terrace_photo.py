"""Recover the photographed wall rail in metres from the renovation plan and image 38.

Run beside the two signed survey JSON files. A free-height upper plant enclosure
sets perspective. Its fitted height is not used to build the terrace.
"""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares, minimize_scalar

HERE=Path(__file__).resolve().parent

def project(camera, points):
    cx,cy,cz,yaw,pitch,roll,f,u0,v0=camera
    si,co=np.sin,np.cos
    right=np.array([co(yaw),-si(yaw),0.])
    forward=np.array([si(yaw)*co(pitch),co(yaw)*co(pitch),si(pitch)])
    up=np.cross(right,forward)
    rays=points-[cx,cy,cz]
    depth=np.clip(rays@forward,.001,1000.)
    return np.stack((u0+f*(rays@(right*co(roll)+up*si(roll)))/depth,
                     v0-f*(rays@(up*co(roll)-right*si(roll)))/depth),axis=-1)

def refit():
    obs=json.loads((HERE/'roof-terrace-fit.json').read_text())
    survey=json.loads((HERE/'roof-terrace-survey.json').read_text())
    matrix=np.array(obs['plan_pixel_to_xy'])
    def xy(uv):return np.c_[uv,np.ones(len(uv))]@matrix.T
    planar=xy(np.asarray(obs['plan_control_uv']))
    controls=np.c_[planar,np.zeros(len(planar))]
    curve=xy(np.asarray(survey['roof_plan_edges']['inner_south']))
    stations=np.r_[0,np.cumsum(np.linalg.norm(np.diff(curve,axis=0),axis=1))]
    top=np.asarray(obs['bracket_head_pixels'])
    bottom=np.asarray(obs['bracket_base_pixels'])
    def corners(params):
        return np.r_[
            ((project(params[:9],controls)-obs['base_image_uv'])/np.array([2,2,4,4,4])[:,None]).ravel(),
            ((project(params[:9],controls[:3]+[0,0,params[9]])-obs['pavilion_top_image_uv'])/np.array([2,2,4])[:,None]).ravel(),
            params[5]/.015,(params[2]-1.55)/.40,(params[7]-431)/15,(params[8]-287)/15,
        ]
    def bracket_positions(q,count,drop=0.):
        st=q[11]-np.arange(count)*q[10]
        return np.c_[np.interp(st,stations,curve[:,0]),np.interp(st,stations,curve[:,1])+.13,np.repeat(q[12]-drop,count)]
    def combined(q):
        return np.r_[corners(q[:10]),((project(q[:9],bracket_positions(q,len(top)))-top)/1.25).ravel()]
    bounds=([0,0,.5,-2.7,-.45,-.1,160,325,211,2.2],[45,30,3,-.2,.45,.1,1350,537,363,12])
    coarse=least_squares(corners,[25,3,1.55,-1.1,.03,0,520,431,287,5],bounds=bounds,max_nfev=420)
    final_bounds=([0,0,.5,-2.7,-.45,-.1,160,295,181,2.0,.5,30,.55],
                  [45,30,3,-.2,.45,.1,1350,567,393,12,2.7,56,1.65])
    final=least_squares(combined,[*coarse.x,1.2,42.8,.93],bounds=final_bounds,max_nfev=500)
    q=final.x
    drop=minimize_scalar(lambda dz:np.square(bottom[:,1]-project(q[:9],bracket_positions(q,len(bottom),dz))[:,1]).sum(),
                         bounds=(.15,.7),method='bounded').x
    return {'pitch_m':q[10],'top_z_over_deck_m':q[12],'bracket_drop_m':drop,
            'native_head_residuals_px':(project(q[:9],bracket_positions(q,len(top)))-top).round(4).tolist()}
if __name__=='__main__':
    print(json.dumps(refit(),ensure_ascii=False,indent=2))
