"""Refit both square-pixel north cameras from the saved original-image observations."""
import argparse
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
saved=json.loads(Path(__file__).with_name('nine-north-windows-and-stepped-gables.json').read_bytes())
identity=['upper-left','upper-right','sill-right','sill-left','head-fixing','lower-lamp-left','lower-lamp-right','lower-head-left','lower-head-right']
raw={'native_pixels':{n:{k:saved['views'][n]['readings'][k] for k in identity} for n in ('20','22')},
     'observed_vertical_arrises':{n:saved['views'][n]['vertical_arrises'] for n in ('20','22')}}
pts=[np.array(list(raw['native_pixels'][n].values()))for n in ['20','22']]
walls=raw['observed_vertical_arrises']
def camera(v,cx,cy):
 eye=v[:3];a,b,t=v[3:6];f=np.exp(v[6])
 forward=np.array([np.cos(b)*np.cos(a),np.cos(b)*np.sin(a),np.sin(b)])
 right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right)
 r=np.array([right*np.cos(t)+down*np.sin(t),down*np.cos(t)-right*np.sin(t),forward])
 return np.array([[f,0,cx],[0,f,cy],[0,0,1.]])@r@np.c_[np.eye(3),-eye]
def pview(v,i):
 return camera(v[10+i*7:17+i*7],*[(512,341.5),(330,440)][i])
def proj(P,xyz):
 p=P@np.c_[xyz,np.ones(len(xyz))].T;return (p[:2]/p[2]).T
def source(v):
 wu,wl,zu,zl,ground,headlamp,lamps,span,offset,total=v[:10]
 c=17.00;x=13.15
 yz=[(c-wu/2,zu),(c+wu/2,zu),(c+wu/2,zl),(c-wu/2,zl),(c,headlamp),
 (c-span/2+offset,lamps),(c+span/2+offset,lamps),(c-wl/2+offset,ground),(c+wl/2+offset,ground)]
 ds=[-.095]*4+[.085,.085,.085,-.095,-.095]
 return [[x+d,y,z] for (y,z),d in zip(yz,ds)]
def resid(v):
 wu,wl,zu,zl,ground,headlamp,lamps,span,offset,total=v[:10]
 errs=[]
 for i,n in enumerate(('20','22')):
  P=pview(v,i);u=proj(P,source(v));wr=walls[n]
  errs.extend(((u-pts[i])/2.5).ravel())
  for y,k in ((17-total/2,0),(17+total/2,2)):
   l=np.cross(np.r_[wr[k],1.],np.r_[wr[k+1],1.]);l/=np.linalg.norm(l[:2])
   for uv in proj(P,[[13.15,y,2],[13.15,y,5]]):errs.append(np.r_[uv,1.]@l/3.)
  q=v[10+i*7:17+i*7];errs.extend([(q[2]-1.55)/.42,(q[6]-np.log([900,850][i]))/.58,q[5]/.075])
 errs.extend([(zu-4.82)/.22,(zl-3.23)/.25,(ground-1.83)/.23,(headlamp-zu-.36)/.10,(lamps-ground-.36)/.10,offset/.14,(wu-1.05)/.38])
 return errs
start=[1.07,1.75,4.82,3.23,1.83,5.15,2.18,1.86,.05,4.6];start+=[23.,30.,1.5,-2.22,.15,0,np.log(750.)];start+=[22.,14.,1.5,2.80,.15,0,np.log(850.)]
s=least_squares(resid,start,max_nfev=2700,x_scale='jac',loss='soft_l1')
print('result',s.x[:10]);out={'method':'Independent two-camera fit with square pixels, a centered principal point, soft eye-height and storey-level priors, and an adjustable width for the projecting gable actually visible in the obliques. The original eight-metre aerial width was retained separately as a test.','parameters':dict(zip(('upper_width','lower_width','upper_head','upper_sill','lower_head','upper_fixing','lower_fixing','lower_fixing_span','lower_offset','roughcast_body_width'),s.x[:10].round(4).tolist()))}
for i,n in enumerate(('20','22')):
 P=pview(s.x,i);q=s.x[10+i*7:17+i*7];err=np.linalg.norm(proj(P,source(s.x))-pts[i],axis=1);print(n,err.round(2),'eye',q[:3].round(2),'f',np.exp(q[-1]))
 out.setdefault('views',{})[n]={'native_dimensions':[(1024,683),(660,880)][i],'P':P.tolist(),'eye':q[:3].tolist(),'focal':float(np.exp(q[-1])),'readings':raw['native_pixels'][n],'reprojection_px':err.round(3).tolist(),'vertical_arrises':walls[n]}
args.out.write_text(json.dumps(out,indent=1))
