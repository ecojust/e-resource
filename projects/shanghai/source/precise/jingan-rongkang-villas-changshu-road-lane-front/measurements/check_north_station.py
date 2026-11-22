"""Rebuild the winter camera at a fixed eye from the clear northern half of the entrance head."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

D=Path(__file__).resolve().parent
def lens(im,delta=(0,0,0)):
    yaw,pitch,roll=np.radians([im['az']+delta[0],im['pitch']+delta[1],delta[2]])
    x,y=im['width']/2,im['height']/2
    f=x/np.tan(np.radians(im['hfov']/2))
    forward=np.array([np.sin(yaw),np.cos(yaw),0]);right=np.array([np.cos(yaw),-np.sin(yaw),0]);up=np.array([0,0,1])
    R=np.array([right,up*np.cos(pitch)-forward*np.sin(pitch),forward*np.cos(pitch)+up*np.sin(pitch)])
    c,s=np.cos(roll),np.sin(roll)
    return np.array([[c,-s,x*(1-c)+y*s],[s,c,y*(1-c)-x*s],[0,0,1]])@np.array([[f,0,x],[0,-f,y],[0,0,1]])@R

def check():
    b=json.loads((D/'independent-north-window-station.json').read_bytes())
    g=json.loads((D/'southern-lane-registration.json').read_bytes())
    a=np.deg2rad(g['x_bearing_degrees'])
    basis=np.array([[np.sin(a),np.cos(a),0],[-np.cos(a),np.sin(a),0],[0,0,1]])
    head=b['rectilinear_views'][b['head_source']];side=b['rectilinear_views'][b['facade_source']]
    def make(v):
        A=lens(head,v)@basis.T;P=np.c_[A,-A@b['origin_xyz']]
        return P,lens(side)@np.linalg.inv(lens(head))@P
    def err(v):
        P,Q=make(v);e=[]
        for obs in b['anchors']:
            q=P@np.r_[obs['local_xyz'],1];e.extend(q[:2]/q[2]-obs['native_uv'])
        van=Q[:2,2]/Q[2,2]
        for marks in b['marks'].values():
            for i,j in ((0,3),(1,2)):
                if marks[i] is None or marks[j] is None:continue
                top,bottom=np.array(marks[i]),np.array(marks[j]);d=top-bottom;v=van-bottom
                e.append(.7*(d[0]*v[1]-d[1]*v[0])/np.linalg.norm(v))
        return e
    pars=least_squares(err,[0,0,0],loss='soft_l1').x;assert np.allclose(pars,b['head_pose_degrees'],atol=2e-6)
    _,Q=make(pars);assert np.allclose(Q,b['local_xyz_to_image'],rtol=3e-8,atol=5e-5)
    return dict(camera=b['station'],fixed_xyz=b['origin_xyz'],angles=pars.tolist(),
                max_gate_residual_px=max(np.linalg.norm(np.array(err(pars)[:10]).reshape(-1,2),axis=1)))
if __name__=='__main__':print(check())
