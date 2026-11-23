"""Fit the common rectilinear wall and its hipped return to the 1937 record and 2014 proposal."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
S=Path(__file__).resolve().parent
j=json.loads((S/'wing-observations.json').read_bytes())['images'];keys=list(j)
width=14.8
def camera(C,aim):
 v=aim-C;v=v/np.linalg.norm(v);right=np.cross(v,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(v,right)
 return Rotation.from_matrix([right,down,v]).as_rotvec()
def project(params,station,point):
 C=params[:3];R=Rotation.from_rotvec(params[3:6]).as_matrix()
 wh=np.array(j[station]['size']);K=np.array([[np.exp(params[6]),0,wh[0]/2],[0,np.exp(params[6]),params[7]],[0,0,1.]])
 v=K@R@(point-C);return v[:2]/v[2]
def world(values):
 H,rail,p1,p2,portalH,depth,ridgeZ,hip1,hip2=values
 return {'left_grade':[0,0,0],'right_grade':[width,0,0],'left_eave':[0,0,H],'right_eave':[width,0,H],'left_rail':[0,0,rail],'right_rail':[width,0,rail],'portal_left_grade':[p1,0,0],'portal_right_grade':[p2,0,0],'portal_left_rail':[p1,0,portalH],'portal_right_rail':[p2,0,portalH],'side_rear_grade':[0,depth,0],'side_rear_eave':[0,depth,H],'ridge_left':[hip1,depth/2,ridgeZ],'ridge_right':[width-hip2,depth/2,ridgeZ]}
def residual(x,rows=False):
 vals=x[:9];pts=world(vals);out=[];recs={}
 for i,k in enumerate(keys):
  v=j[k];c=x[9+i*8:17+i*8];marks=v['plane']|{a:v[a] for a in ('side_rear_grade','side_rear_eave','ridge_left','ridge_right')};recs[k]={}
  for key,uv in marks.items():
   if key=='ridge_right':continue
   est=project(c,k,pts[key]);err=est-uv;recs[k][key]={'read':uv,'estimated':est.tolist(),'residual':err.tolist()}
   weight=2.5 if 'grade'in key or 'ridge'in key else 1.8
   out.extend(err/weight)
  size=v['size'];out.append((c[7]-size[1]/2)/(size[1]*.22))
  out.append((c[6]-np.log(size[0]*1.7))/.92)
  out.extend([(c[2]-(1.72 if k=='design' else 1.55))/.24])
  if k=='design':
   # Two figures by the proposed entrance. Scale comes from an explicitly approximate
   # standing height; the foot marks are the visible lawn grade in this view.
   for uv_top,uv_base,xx in [([294,212],[295,241],9.0),([314,211],[314,240],10.0)]:
    apparent=project(c,k,[xx,-.24,1.68])-project(c,k,[xx,-.24,0])
    out.extend((apparent-(np.asarray(uv_top)-uv_base))/3.3)
 out.extend((vals-np.array([4.0,2.45,7.0,10.6,2.8,7.,7.9,2.65,1.5]))/np.array([.4,.50,2.,2.,.5,1.35,1.5,1.0,.95]))
 if rows:return recs
 return np.array(out)
start=[4.0,2.45,7.,10.6,2.8,7,7.9,1.05,1.05];target=np.array([7,0,3.4])
for k,C in zip(keys,[[-10,-37,2.2],[-30,-70,3.2]]):
 C=np.array(C);start.extend([*C,*camera(C,target),np.log(j[k]['size'][0]*1.7),j[k]['size'][1]/2])
sol=least_squares(residual,start,max_nfev=1100,loss='soft_l1',x_scale='jac')
out={'dimensions':dict(zip(['eave','rail','portal_left','portal_right','portal_top','depth','ridge','left_hip','right_hip'],sol.x[:9])),'width':width,'local_points':world(sol.x[:9]),'views':{}}
for i,k in enumerate(keys):
 c=sol.x[9+8*i:17+8*i];rr=residual(sol.x,True)[k];size=j[k]['size']
 out['views'][k]={'C':c[:3].tolist(),'R':Rotation.from_rotvec(c[3:6]).as_matrix().tolist(),'K':[[np.exp(c[6]),0,size[0]/2],[0,np.exp(c[6]),c[7]],[0,0,1.]],'median_px':float(np.median([np.linalg.norm(v['residual'])for v in rr.values()])),'reads':rr}
print(out['dimensions'],[(k,v['median_px'],v['C']) for k,v in out['views'].items()])
(S/'wing-cameras.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
