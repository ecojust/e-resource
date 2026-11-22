"""Register the 2023 street gate to the separate building using opening-day photographs."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;d=json.loads((w/'gate-camera-fit.json').read_text());m=json.loads((w/'gate-registration-ties.json').read_text())
P=np.asarray(json.loads((w/'adjacent-building-camera.json').read_text())['front'])
def inverse(p,uv,y):
 h=p[:,[0,2,3]].copy();h[:,2]+=y*p[:,1];a=np.linalg.solve(h,[*uv,1]);return a[:2]/a[2]
def project(p,xyz):
 v=np.pad(xyz,((0,0),(0,1)),constant_values=1)@p.T;return v[:,:2]/v[:,2,None]
def unique(rows):
 seen=set();a=[]
 for r in rows:
  key=tuple(np.round(np.r_[r['p'],r['q']]).astype(int))
  if key in seen:continue
  seen.add(key);a.append(r)
 return a
rows=unique(m['0-1']);uv=np.array([r['p']for r in rows]);to=np.array([r['q']for r in rows]);xz=np.array([inverse(P,u,0.)for u in uv]);xyz=np.c_[xz[:,0],np.zeros(len(xz)),xz[:,1]]
A=[]
for (x,z),(u,v)in zip(xz,to):A.extend(([x,z,1,0,0,0,-u*x,-u*z,-u],[0,0,0,x,z,1,-v*x,-v*z,-v]))
h=np.linalg.svd(A)[2][-1].reshape(3,3)
def camera(c):
 f=c[0];K=np.array([[f,0,300],[0,f,200],[0,0,1.]]);return K@np.c_[Rotation.from_rotvec(c[1:4]).as_matrix(),c[4:7]]
f=380;K=np.array([[f,0,300],[0,f,200],[0,0,1.]])
a=np.linalg.inv(K)@h;a*=np.sign(a[2,2])/np.mean(np.linalg.norm(a[:,:2],axis=0));rx,rz,t=a.T;u,_,v=np.linalg.svd(np.c_[rx,np.cross(rz,rx),rz])
fitted=least_squares(lambda c:(project(camera(c),xyz)-to).ravel(),np.r_[f,Rotation.from_matrix(u@v).as_rotvec(),t],loss='soft_l1',f_scale=1);O=camera(fitted.x)
rows2=unique(m['1-2']);q=np.array(d['views'][0]['P']);dims=d['dimensions'];lc=[];obs=[]
for r in rows2:
 u,v=r['q']
 if v<145:continue
 depth=(-.024 if 142<u<254 and 169<v<263 else -.036 if 548<u<670 and 166<v<252 else 0.)
 x,z=inverse(q,r['q'],depth);lc.append([x,depth,z]);obs.append(r['p'])
lc=np.array(lc);obs=np.array(obs)
# Street view 13. Visible right pillar: two front sign corners, shaft top, base and cap.
front={'brown heading upper left':([550,167],[62,449]),'brown heading upper right':([665,167],[95,450]),'shaft right under cap':([665,142],[97,441]),'outer plinth right at ground':([665,512],[83,537]),'plinth top at right edge':([665,435],[88,518]),'plinth left at ground':([542,514],[49,537]),'plinth top left':([542,436],[54,517])}
cs=[];fs=[]
for label,(point,at) in front.items():
 y=-.036 if label.startswith('brown')else 0
 x,z=inverse(q,point,y);cs.append([x,y,z]);fs.append(at)
cs=np.array(cs);fs=np.array(fs)
def convert(c,pts):
 dx,dy,dz,s,angle=c;R=Rotation.from_rotvec([0,0,angle]).as_matrix();return pts@R.T*s+[dx,dy,dz]
def solve(ob1,ob2):
 def errors(c):return np.r_[(project(O,convert(c,lc[ob1]))-obs[ob1]).ravel(),(project(P,convert(c,cs[ob2]))-fs[ob2]).ravel(),c[4]/.10]
 results=[least_squares(errors,[-12,dy,-3,1,0],bounds=([-60,-30,-20,.5,-.3],[10,1,10,2,.3]),loss='linear',max_nfev=300)for dy in [-1,-4,-7,-10]]
 return min(results,key=lambda r:r.cost).x
fit=solve(np.arange(len(lc)),np.arange(len(cs)))
def both(x):
 c=x[:7];t=x[7:]
 return np.r_[((project(camera(c),xyz)-to)*1.6).ravel(),(project(camera(c),convert(t,lc))-obs).ravel(),((project(P,convert(t,cs))-fs)*2).ravel(),t[4]/.09]
joint=least_squares(both,np.r_[fitted.x,fit],loss='soft_l1',f_scale=2.5,bounds=([100,*[-np.inf]*6,-60,-30,-20,.45,-.4],[1000,*[np.inf]*6,10,1,10,2,.4]),max_nfev=1500)
O=camera(joint.x[:7]);fitted.x=joint.x[:7];fit=joint.x[7:];pp=project(P,convert(fit,cs));oo=project(O,convert(fit,lc));e=np.linalg.norm(project(O,xyz)-to,axis=1)
model=dict(source_2023_frontage_camera=P.tolist(),source_opening_camera=O.tolist(),opening_focal_px=fitted.x[0],facade_anchor_count=len(e),facade_median_px=float(np.median(e)),facade_p90_px=np.percentile(e,90),gate_anchor_count=len(lc),gate_median_opening_px=float(np.median(np.linalg.norm(oo-obs,axis=1))),gate_locator_frontage=front,gate_predicted_on_front13=pp.tolist(),gate_residual_front13=np.linalg.norm(pp-fs,axis=1).tolist(),local_to_provisional_building=dict(origin_XYZ=fit[:3].tolist(),uniform_scale=fit[3],rotation_about_Z_degrees=np.degrees(fit[4])),front13_witnesses=[dict(observed=r['p'],opening21=r['q'])for r in rows],gate21_witnesses=[dict(uv21=list(uv),xyz_gate=p.tolist())for uv,p in zip(obs,lc)],scope='Conditional placement on the published frontage frame. Post anchors and façade stations are independent features; the threshold, front entrance and green street number belong to different planes.')
(w/'frontage-registration.json').write_text(json.dumps(model,indent=2,ensure_ascii=False)+'\n')
print('parent reference gauge',fit,'F21',fitted.x[0], 'facade',len(e),np.median(e),np.percentile(e,90),'gate21',model['gate_median_opening_px'],'front13',np.round(model['gate_residual_front13'],1),pp)
