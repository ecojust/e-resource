"""Refit four street-view cameras from the released numerical image measurements."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent

def apply(matrix,points):
    p=np.asarray(points)
    q=np.c_[p,np.ones(len(p))]@matrix.T
    return q[:,:2]/q[:,2:]

def basis(azimuth):
    az=np.deg2rad(azimuth)
    return np.array([[np.cos(az),-np.sin(az),0],[0,0,1],[np.sin(az),np.cos(az),0]])

def lens(d,yaw=0,pitch=0,roll=0):
    az,el,rr=np.deg2rad([d['az']+yaw,d['pitch']+pitch,roll])
    cx,cy=d['width']/2,d['height']/2
    f=cx/np.tan(np.radians(d['hfov']/2))
    fw=np.array([np.sin(az),np.cos(az),0]);up=np.array([0.,0.,1.]);side=np.array([np.cos(az),-np.sin(az),0])
    rotation=np.stack((side,up*np.cos(el)-fw*np.sin(el),fw*np.cos(el)+up*np.sin(el)))
    c,s=np.cos(rr),np.sin(rr)
    image_roll=np.array([[c,-s,cx*(1-c)+cy*s],[s,c,cy*(1-c)-cx*s],[0,0,1]])
    return image_roll@np.array([[f,0,cx],[0,-f,cy],[0,0,1]])@rotation

def refit():
    data=json.loads((HERE/'street-face-pose-controls.json').read_text())
    cams=data['sites'];keys=list(cams);ref=keys[0];obs=[cams[k]for k in keys];B=basis(data['normal_azimuth'])
    ground=data['ground'];foot=np.asarray(ground[ref]);eye=obs[0]['station']['height']
    sight=np.c_[foot,np.ones(len(foot))]@np.linalg.inv(lens(obs[0]['projection'])).T
    hits=sight*(-eye/sight[:,2:3])
    x_center=-np.mean(hits@B[0]);y_eye=-np.mean(hits@B[2])
    ll=np.asarray(obs[0]['station']['position']);metres=[111320*np.cos(np.radians(ll[1])),110880]
    initial=[]
    for m in obs:
        along,depth=B[[0,2],:2]@((np.asarray(m['station']['position'])-ll)*metres)
        initial.append([x_center+along,y_eye+depth,m['station']['height'],*m['vanishing_prior']])
    initial=np.asarray(initial)
    def matrices(flat):
        result=[]
        for p,m in zip(flat.reshape(-1,6),obs):
            xx,yy,zz,*angles=p
            axes=np.column_stack((B[0],B[1],-xx*B[0]-yy*B[2]-zz*B[1]))
            result.append(lens(m['projection'],*angles)@axes)
        return result
    def residual(flat):
        poses=flat.reshape(-1,6);mat=matrices(flat);res=[]
        for i,m in enumerate(obs[1:],1):
            a=m['correspondences'];world=apply(np.linalg.inv(mat[0]),a['source'])
            res.extend(((apply(mat[i],world)-a['target'])/1.65).ravel())
        for i,key in enumerate(keys):
            if key in ground:
                g=apply(np.linalg.inv(mat[i]),ground[key])
                res.extend(g[:,1]/(.065 if i==0 else .115))
                if i==0:res.append(g[:,0].mean()/.015)
            delta=poses[i]-initial[i]
            res.extend(delta[[2,3,4,5]]/[.065,.55,.40,.40])
            if i:res.extend((delta[:2]-(poses[0]-initial[0])[:2])/[1.65,1.65])
        i,j=keys.index('struct-2015-east'),keys.index('struct-2015-middle')
        res.extend(((poses[i,:2]-poses[j,:2])-(initial[i,:2]-initial[j,:2]))/[.35,.48])
        return np.asarray(res)
    slack=np.tile([6.,5.,.65,7.,4.,4.],(len(initial),1))
    sol=least_squares(residual,initial.ravel(),bounds=((initial-slack).ravel(),(initial+slack).ravel()),loss='soft_l1',f_scale=1.,max_nfev=100)
    saved=json.loads((HERE/'gate-camera-registration.json').read_text())['station_fits']
    grid=[[a,z]for a in (-5.5,-2,0,2,5.5)for z in (.2,2,4,7,9)]
    out={}
    for key,mat,p in zip(keys,matrices(sol.x),sol.x.reshape(-1,6)):
        diff=np.linalg.norm(apply(mat,grid)-apply(np.array(saved[key]['worldXZ_to_image']),grid),axis=1)
        out[key]=dict(parameters=p.tolist(),repeat_grid_max_px=float(diff.max()))
    return out

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path);args=cli.parse_args();out=refit()
    args.output.write_text(json.dumps(out,indent=1)+'\n')
    print({k:round(v['repeat_grid_max_px'],6)for k,v in out.items()})
    if max(i['repeat_grid_max_px']for i in out.values())>.05:raise SystemExit(1)
