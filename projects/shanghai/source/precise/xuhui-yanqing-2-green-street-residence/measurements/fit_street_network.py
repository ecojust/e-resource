"""Refit the June street camera and three winter stations from registered window and gate corners."""
import argparse
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from scipy.sparse import lil_matrix
W=Path(__file__).resolve().parent;raw=json.loads((W/'winter-control-initial.json').read_text());june=json.loads((W/'camera-initial.json').read_text())
marks=raw['measurements'];vkeys=['5','7','3'];meta=raw['station_data'];M=len(marks)
lon,lat=raw['wgs84_origin'];basis=np.array([raw['local_X_EN'],raw['local_Y_EN']])
T=np.eye(3);T[:2,:2]=basis
K=np.array(june['preliminary_intrinsics']);wz=float(june['eye_height_m'])
org=np.r_[raw['EN_origin_gate_middle'],0]
start_xyz=np.array([v['ENU_m']for v in marks])
start_yaw=Rotation.from_matrix(np.array(june['rotation_world_to_camera'])@T).as_rotvec()
Jstart=org+T.T@np.array(june['camera_centre'])
def station(k):
 m=meta[k];a,p=np.radians([m['az'],m['pitch']]);w,h=m['width'],m['height'];f=w*.5/np.tan(np.radians(m['hfov']/2))
 x,y=m['station']['position'];c=np.array([(x-lon)*111320*np.cos(np.radians(lat)),(y-lat)*110852,m['station']['height']])
 R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a)*np.sin(p),np.cos(a)*np.sin(p),-np.cos(p)],[np.sin(a)*np.cos(p),np.cos(a)*np.cos(p),np.sin(p)]])
 return c,R,np.array([[f,0,w/2],[0,f,h/2],[0,0,1]])
stations={k:station(k)for k in vkeys}
V=3*len(vkeys)
extras=V+6
initial=np.r_[np.zeros(V),start_yaw,Jstart,start_xyz.ravel()]
obs={};source=[]
for i,k in enumerate(vkeys):
 v=[(j,q['december_station_pixels'][k]) for j,q in enumerate(marks) if k in q['december_station_pixels']];obs[k]=(np.array([x[0]for x in v]),np.array([x[1]for x in v]))
jidx=np.array([i for i,m in enumerate(marks)if m['Fayhoo_June_pixel']]);jpoints=np.array([marks[i]['Fayhoo_June_pixel']for i in jidx])
def project(pts,C,R,K):
 q=(pts-C)@R.T@K.T;return q[:,:2]/q[:,2,None]
eq_z=[(1,2),(3,4),(5,6),(7,8),(9,10),(11,12),(13,14),(15,16),(17,18),(19,20),(21,22),(22,23),(23,24)]
eq_xy=[(1,3),(2,4),(9,11),(10,12)]
def residual(v,report=False):
 xyz=v[extras:].reshape((-1,3));results=[];err={}
 for i,k in enumerate(vkeys):
  c,r,Ks=stations[k];rot=Rotation.from_rotvec(v[i*3:i*3+3]).as_matrix()@r
  si,uv=obs[k];d=project(xyz[si],c,rot,Ks)-uv;err[k]=np.linalg.norm(d,axis=1)
  results.extend(d.ravel())
 jr=Rotation.from_rotvec(v[V:V+3]).as_matrix();jc=v[V+3:V+6]
 d=project(xyz[jidx],jc,jr,K)-jpoints;err['june']=np.linalg.norm(d,axis=1)
 results.extend((d*.62).ravel())
 if report:return err
 for a,b in eq_z:results.append((xyz[a,2]-xyz[b,2])/.043)
 for a,b in eq_xy:results.extend((xyz[a,:2]-xyz[b,:2])/.035)
 # Real rail and jamb pairs are level and vertical; retain modest prior ranges on camera aims.
 results.extend(v[:V]/np.radians(3))
 results.extend(xyz[[3,4],2]/.08)
 results.append((jc[2]-wz)/.18)
 return np.asarray(results)
# Finite-difference sparsity is constant throughout the bundle.
base=residual(initial);spars=lil_matrix((len(base),len(initial)),dtype=int)
for i in range(len(initial)):
 dv=initial.copy();dv[i]+=.0001
 spars[:,i]=np.asarray((abs(residual(dv)-base)>1e-10),int)[:,None]
fit=least_squares(residual,initial,jac_sparsity=spars.tocsr(),loss='soft_l1',f_scale=1.4,x_scale='jac',max_nfev=230,ftol=1e-7)
x=fit.x;xyz=x[extras:].reshape(-1,3);err=residual(x,True)
# A local street frame uses the actual tangent of the gate. The cylinder's turn
# is read in this frame; the point on the front gate itself sets the depth datum.
axis=xyz[2,:2]-xyz[1,:2];axis/=np.linalg.norm(axis);inward=np.array([-axis[1],axis[0]])
if inward@(xyz[0,:2]-stations['5'][0][:2])<0:inward=-inward
T=np.eye(3);T[:2,:2]=np.array([axis,inward]);org=(xyz[3]+xyz[4])/2;loc=(xyz-org)@T.T
out={'local_origin_ENU':org.tolist(),'ENU_to_local':T.tolist(),'optimizer_stop':fit.message,'cost':fit.cost,'photos':{},'june_camera':{},'points':[]}
for i,k in enumerate(vkeys):
 c,r,ks=stations[k];rr=Rotation.from_rotvec(x[i*3:i*3+3]).as_matrix()@r
 out['photos'][k]=dict(C=(T@(c-org)).tolist(),R=(rr@T.T).tolist(),K=ks.tolist(),rotation_correction_degrees=np.degrees(x[i*3:i*3+3]).tolist(),median_px=float(np.median(err[k])))
out['june_camera']=dict(C=(T@(x[V+3:V+6]-org)).tolist(),R=(Rotation.from_rotvec(x[V:V+3]).as_matrix()@T.T).tolist(),K=K.tolist(),median_px=float(np.median(err['june'])))
for i,coord in enumerate(loc):out['points'].append(dict(label=marks[i]['label'],xyz=coord.tolist(),june_pixel=marks[i]['Fayhoo_June_pixel'],winter_pixels=marks[i]['december_station_pixels']))
print('resid',[(k,round(float(np.median(v)),1),round(float(max(v)),1))for k,v in err.items()], 'Jcam',out['june_camera']['C'])
for r in out['points']:print(r['label'],np.round(r['xyz'],2))
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--output',type=Path,required=True)
cli.parse_args().output.write_text(json.dumps(out,indent=2)+'\n')
