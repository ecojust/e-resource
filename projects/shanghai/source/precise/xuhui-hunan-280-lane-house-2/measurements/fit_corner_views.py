"""Fit the four steel jambs jointly to Masa's opposing 2016 photographs, before applying street scale."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parents[1]
meas=json.loads((root/'measurements/corner-photo-controls.json').read_bytes()); views=['43052484','43052486'];obs=[]
for i,key in enumerate(views):
    for level,entry in meas['original_observations'][key].items():
        for edge,j in (('outer_left',0),('outer_right',3),('post',1 if i==0 else 2),('central_far',2 if i==0 else 1)):
            for tag,top in [('top',1),('sill',0)]:
                if edge+'_'+tag in entry:obs.append((i,int(level)-2,j,top,entry[edge+'_'+tag]))
def points(par):
    l,r,a,b=par[:4];a,b=np.radians([a,b]);return np.array([[-.5-l*np.cos(a),l*np.sin(a)],[-.5,0],[.5,0],[.5+r*np.cos(b),r*np.sin(b)]])
def rotation(c):
    yaw,inc,roll=np.radians(c[3:6])
    f=np.array([np.sin(yaw)*np.cos(inc),np.cos(yaw)*np.cos(inc),np.sin(inc)]);r=np.array([np.cos(yaw),-np.sin(yaw),0]);down=np.cross(f,r)
    return np.array([np.cos(roll)*r+np.sin(roll)*down,-np.sin(roll)*r+np.cos(roll)*down,f])
def project(p,c):
    vs=(p-c[:3])@rotation(c).T
    return 700*np.exp(c[6])*vs[:,:2]/vs[:,2:3]+[325,433]
def r(par,priors=True):
    xy=points(par);base=np.r_[0,par[4:7]];height=par[7:11];out=[]
    for i,level,j,top,uv in obs:
        c=par[11+i*7:18+i*7];p=np.r_[xy[j],base[level]+top*height[level]]
        out.extend(project(p[None,:],c)[0]-np.array(uv))
    if priors:
        # EXIF 5 mm and the 6.17 mm sensor long edge give 702 px before possible lens correction/cropping.
        out.extend([par[17]*32.,par[24]*32.])
        out.extend((np.diff(np.diff(base)))*3.)
        out.extend(np.diff(height)*2.)
    return out
initial=[.95,.95,48,48,1.8,3.6,5.4,1.2,1.2,1.2,1.2,-4,-5,-1.35,35,19,0,0,4,-8,-1.45,-29,14,0,0]
fit=least_squares(r,initial,loss='soft_l1',f_scale=2.,max_nfev=600,x_scale='jac')
a=fit.x;res=np.asarray(r(a,False)).reshape(-1,2); print(a.round(3),np.median(np.linalg.norm(res,axis=1)),np.max(np.linalg.norm(res,axis=1)))
data={'reference':'The central chord between the two structural posts is one unit. West and south origin positions and ENU scale are independently fitted to the street stations.','four_jambs_local_xy':points(a).tolist(),'sill_z':np.r_[0,a[4:7]].tolist(),'opening_heights':a[7:11].tolist(),'median_error_px':float(np.median(np.linalg.norm(res,axis=1))),'observations':[dict(camera=views[i],level=level+2,jamb=j,top=bool(top),observed=uv,error=res[k].tolist()) for k,(i,level,j,top,uv) in enumerate(obs)],'cameras':[dict(centre=a[11+7*i:14+7*i].tolist(),R=rotation(a[11+7*i:18+7*i]).tolist(),f_px=700*np.exp(a[17+7*i]))for i in range(2)]}
import argparse
cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',required=True,type=Path)
out=cli.parse_args().output;out.write_text(json.dumps(data,indent=2)+'\n')
