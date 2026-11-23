from pathlib import Path
import numpy as np,json,math
from scipy.optimize import least_squares
D=Path(__file__).parent
def run():
 obs=json.loads((D/'facade-control-pixels.json').read_text());views=obs['views'];keys=list(views)
 lat=31.22157;lon=121.45155;deg=np.pi/180;conv=np.array([111320*np.cos(lat*deg),110860])
 def change(ang):
  a=ang*deg;return np.array([[np.sin(a),-np.cos(a),0],[np.cos(a),np.sin(a),0],[0.,0.,1.]])
 def basis(az,el,r):
  a,p,b=np.array([az,el,r])*deg;f=np.array([np.sin(a)*np.cos(p),np.cos(a)*np.cos(p),np.sin(p)]);x=np.array([np.cos(a),-np.sin(a),0]);y=np.cross(f,x);return np.array([x*np.cos(b)+y*np.sin(b),y*np.cos(b)-x*np.sin(b),f])
 def points(t):
  w,az0,az1,bx,bw,bz0,bz1,hx,hw,hz,ix,iz,dx,dz,ex,ez,fx=t;return {'AL':(-w/2,0,az1),'AR':(w/2,0,az1),'aL':(-w/2,0,az0),'aR':(w/2,0,az0),'BL':(bx-bw/2,0,bz1),'BR':(bx+bw/2,0,bz1),'bL':(bx-bw/2,0,bz0),'HL':(hx-hw/2,0,hz),'HR':(hx+hw/2,0,hz),'IL':(ix,0,iz),'DH':(dx,0,dz),'DF':(dx,0,0),'E':(ex,-.034,ez),'F':(fx,-.034,ez),'O':(0,0,0)}
 photo=views['2017'];s0=[257,5.89,5.74, 3945, -3.,20.3,1.70,154.,7.,0]
 for k in keys[1:]:
  v=views[k];s0.extend([*(((np.array(v['view_wgs'])-[lon,lat])*conv).tolist()),v['camera_above_road_m'],v['bearing'],v['pitch'],0])
 fields=[1.14,3.45,4.62,2.60,1.15,3.46,4.65,0,1.16,2.17,2.08,2.15,-4.56,2.0,-1.45,.72,-.45];s0.extend(fields);s0=np.array(s0);N=6*len(keys)+4
 def unpack(s):
  M=change(s[0]);O=np.array([s[1],s[2],0]);point=points(s[N:]);cams={};local={}
  for i,k in enumerate(keys):
   v=views[k];c=s[4+6*i:10+6*i];R=basis(*c[3:]);Q=R@M;cl=M.T@(c[:3]-O);f=s[3] if i==0 else v['f'];w,h=v['size'];A=np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
   K=np.c_[Q,-Q@cl];cams[k]=A@K;local[k]=dict(size=v['size'],image=v['image'],eye=cl.tolist(),K=A.tolist(),R=Q.tolist(),P=(A@K).tolist(),enu_eye=c[:3].tolist(),bearing_pitch_roll=c[3:].tolist())
  return cams,local,point
 def errors(s,report=False):
  cams,local,point=unpack(s);res=[];errs={}
  for i,k in enumerate(keys):
   v=views[k];P=cams[k];ix=list(v['points']);a=np.array([point[q] for q in ix]);h=(P@np.c_[a,np.ones(len(a))].T).T;upp=h[:,:2]/h[:,2:];diff=upp-np.array([v['points'][q]for q in ix]);sigma=np.array([v.get('sigma_overrides',{}).get(q,v['pixel_sigma'])*(1.7 if q in ('O','DF') and i else 1)for q in ix]);res.extend((diff/sigma[:,None]).flatten());errs[k]={q:round(float(np.linalg.norm(x)),2)for q,x in zip(ix,diff)}
   if i:
    j=4+6*i;t=s[j:j+6]-s0[j:j+6];res.extend(t/[.8,.8,.18,1.8,1.5,1.1])
  res.extend([(s[3]-3945)/370,(s[6]-1.55)/.28,(s[N+13]-2)/.15,(s[0]-252)/7])
  return errs if report else np.array(res)
 low=np.full_like(s0,-np.inf);high=np.full_like(s0,np.inf);low[:4]=[232,-6,-6,2500];high[:4]=[278,20,20,6500]
 low[N:]=[.6,2.8,4,1.8,.6,2.8,4,-.5,.55,1.5,1.5,1.5,-6.5,1.65,-3,.3,-1];high[N:]=[1.6,4.3,5.5,3.6,1.7,4.3,5.5,.5,1.7,2.6,3,2.6,-3.5,2.35,0,1.1,.5]
 opt=least_squares(errors,s0,bounds=(low,high),loss='soft_l1',f_scale=1.2,max_nfev=1000,x_scale='jac');s=opt.x;assert opt.success and np.max(np.abs(errors(s)))<9,(opt.message,np.max(np.abs(errors(s))));cams,local,point=unpack(s);errs=errors(s,True);g=[lon+s[1]/conv[0],lat+s[2]/conv[1]]
 out=dict(origin_wgs84=g,x_azimuth_deg=s[0],local_axes='X to image right parallel to the 2017 street elevation; Y inward; Z up. Door arch-to-floor 2.00 ±0.15 m is a soft check, not a surveyed height.',cameras=local,points={k:list(v)for k,v in point.items()},errors_px=errs,pixel_error_median={k:float(np.median(list(a.values())))for k,a in errs.items()},physical_door_height_prior_2m=s[N+13]);(D/'street-cameras.json').write_text(json.dumps(out,indent=2)+'\n');print('WGS/axis',g,s[0]);print('points',point);print('error',errs);print('medians',out['pixel_error_median']);print('eyes',[(k,c['eye'])for k,c in local.items()])
if __name__=='__main__':run()
