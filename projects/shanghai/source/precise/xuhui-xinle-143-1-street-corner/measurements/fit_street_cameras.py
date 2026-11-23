"""Bundle original views using survey vehicle centres, rectified feature correspondences and photographed openings."""
from pathlib import Path
import json,math,numpy as np
from scipy.optimize import least_squares
D=Path(__file__).parent
R=D.parent/'research/east'
V=json.loads((D/'shooting-station-measurements.json').read_bytes());KEYS=list(V)
DEG=np.pi/180;meters=np.array([95182.,110868.]);O=np.array([121.45018,31.21925])
def basis(yaw,pitch,roll):
 a,b,c=np.deg2rad([yaw,pitch,roll]);f=np.array([np.sin(a)*np.cos(b),np.cos(a)*np.cos(b),np.sin(b)]);r=np.array([np.cos(a),-np.sin(a),0]);down=np.cross(f,r);return np.array([r*np.cos(c)+down*np.sin(c),down*np.cos(c)-r*np.sin(c),f])
def en_axes(a):
 a=np.deg2rad(a);return np.array([[np.sin(a),-np.cos(a),0],[np.cos(a),np.sin(a),0],[0,0,1]])
def camera(s,i,a,origin):
 d=V[KEYS[i]];w,h=d['dimensions'];j=4+i*6;cen=s[j:j+3];rr=basis(*s[j+3:j+6]);f=s[3]if i==0 else .5*w/np.tan(.5*DEG*d['hfov'])
 k=np.array([[f,0,(w-1)/2],[0,f,(h-1)/2],[0,0,1.]]);r=rr@a;c=a.T@(cen-origin);p=k@np.column_stack((r,-r@c));return p,r,c,k
N=4+len(KEYS)*6
# Exposed house/brick corner and its foot share the same vertical; the two upper-centre sash readings share the same horizontal coordinate.
def pts(s):
 corner,zc,vx,vz,tx,ts,th,mx,mz,hx,hz,lx,lz,px,pz=s[N:]
 return {'origin':(0,0,0),'end':(corner,0,0),'corner':(corner,0,zc),'vent':(vx,0,vz),'topS':(tx,0,ts),'topH':(tx,0,th),'mid':(mx,0,mz),'leftH':(hx,0,hz),'leftL':(lx,0,lz),'panel':(px,0,pz)}
def pref():
 s=[247.,0.,0.,3943.]
 for i,k in enumerate(KEYS):
  d=V[k]
  if not i:s += [-6.4,12.2,1.62,150.,9.,0.]
  else:s += [*list((np.array(d['view_wgs'])-O)*meters),d['height_m'],d['yaw'],d['pitch'],0.]
 return np.array(s+[2.1,8.3,.5,9.0,-2.4,7.8,9.2,-2.5,5.3,-4.6,6.4,-4.6,4.0,.7,8.3])
def project(p,ws):
 h=np.column_stack((ws,np.ones(len(ws))))@p.T;return h[:,:2]/h[:,2,None]
initial=pref(); sel=[];fit_pairs={}
def features():
 records=json.loads((D/'registered-photo-features.json').read_text())
 return {(KEYS.index(row['views'][0]),KEYS.index(row['views'][1])):np.asarray(row['uvuv']) for row in records['pairs']}
def errors(s,details=False):
 axes=en_axes(s[0]);origin=np.r_[s[1:3],0];points=pts(s);cams=[camera(s,i,axes,origin) for i in range(len(KEYS))]
 res=[];sums={}
 for i,k in enumerate(KEYS):
  d=V[k];names=list(d['xy']);uv=np.array([d['xy'][n]for n in names]);forecast=project(cams[i][0],np.array([points[n]for n in names]));delta=forecast-uv
  sums[k]={k:round(float(np.linalg.norm(x)),2)for k,x in zip(names,delta)};weights=np.array([(5.0 if n in ['mid','leftH','leftL','topS','topH'] else 4.) for n in names])*(3.7 if i==0 else 1.)
  res.extend((delta/weights[:,None]).ravel())
  j=4+6*i
  if i:
   res.extend((s[j:j+2]-initial[j:j+2])/.43);res.extend((s[j+2:j+3]-initial[j+2:j+3])/.24);res.extend((s[j+3:j+6]-initial[j+3:j+6])/[2.9,2.6,2.3])
 for (i,j),xy in fit_pairs.items():
  h=cams[j][0][:,[0,2,3]]@np.linalg.inv(cams[i][0][:,[0,2,3]]);p=np.column_stack((xy[:,:2],np.ones(len(xy))))@h.T
  delta=p[:,:2]/p[:,2,None]-xy[:,2:];res.extend((delta/3.8).ravel())
 res.extend([(s[3]-3943)/300,(s[6]-1.60)/.24,(s[0]-248)/5])
 return (cams,points,sums) if details else np.array(res)
def run():
 global fit_pairs
 low=np.full_like(initial,-np.inf);high=np.full_like(initial,np.inf);low[0],high[0]=218,275;low[3],high[3]=2700,5400
 for use in [False,True]:
  fit_pairs=features()if use else {}
  start=sol.x if use else initial
  sol=least_squares(errors,start,bounds=(low,high),loss='soft_l1',f_scale=1.0,max_nfev=210,x_scale='jac');print(use,sol.message,sol.nfev,flush=True)
 s=sol.x;cams,geom,stats=errors(s,True);out={'origin_wgs84':(O+s[1:3]/meters).tolist(),'x_azimuth_degrees':s[0],'camera_2018_focal_px':s[3],'local_axes':'X along the street wall towards the image-right (west), Y inward, Z up. Origin below the 143-1 doorway centre.','points':geom,'residual_distance_px':stats,'pair_feature_counts':{KEYS[i]+' / '+KEYS[j]:len(v) for (i,j),v in fit_pairs.items()},'cameras':{}}
 for k,(p,r,c,kk) in zip(KEYS,cams):
  out['cameras'][k]={'dimensions':V[k]['dimensions'],'C':c.tolist(),'K':kk.tolist(),'R':r.tolist(),'P':p.tolist()}
 print('origin',out['origin_wgs84'],'angle',s[0],'f',s[3]);print('metric',geom);print('residuals',[(k,round(np.median(list(v.values())),2),max(v.values()))for k,v in stats.items()]);print('eyes',[(k,np.round(c['C'],1))for k,c in out['cameras'].items()]);(D/'street-cameras.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':run()
