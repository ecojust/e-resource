from pathlib import Path
import numpy as np, json
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from scipy.linalg import orthogonal_procrustes
from statistics import median
HERE=Path(__file__).resolve().parent; S=HERE.parent
data=[]
def mark(name,u,z,g,m,d=0,s=1.5):data.append((name,u,d,z,g,m,s))
# Same physical edges in both photographs. Floating letter keys preserve level and plumb constraints.
mark('door foot left',-.50,.46,[59,606],[314,510])
mark('door foot right',.50,.46,[116,597],[344,505])
mark('arch spring left',-.50,2.56,[83,399],None)
mark('arch spring right',.50,2.56,[130,409],None)
mark('number 3 plate centre','plate_u','plate_z',[72,409],[304,405],-.018)
mark('window lintel left','wl','wt',[157,423],[352.8,406])
mark('window lintel right','wr','wt',[182,431],[367.8,408.5])
mark('window sill left','wl','wb',[149,512],[355.5,457])
mark('window sill right','wr','wb',[177,514],[371.7,456.7])
mark('left corner at grade','gl',0,[5,678],[291.5,540],s=3)
mark('left timber belt lower edge','gl','belt',[58,276],[283.8,341],-.048)
mark('beam foot of left-hand board','beam1','belt',[116,312],[315.4,351.8],-.048)
mark('beam foot of next board','beam2','belt',[160.5,342],[346.2,364],-.048)
mark('small gable returns at lower belt','bu','belt',[194,361],[375.0,368.5],0,s=2.5)
mark('small gable lower wall junction','bu',0,[188,611],[390,511],s=2.5)
mark('main upper window first lintel left','uwl','uwt',[146,141],[315.6,249.9],-.065,s=2.2)
mark('main upper window first lintel right','uwc','uwt',[176,177],[338,268.2],-.065,s=2)
mark('main upper window first sill left','uwl','uwb',[136.8,224],[318.6,300.1],-.065)
mark('main upper window first sill right','uwc','uwb',[162.4,249],[339.2,310.1],-.065)
mark('main upper next window sill right','uwr','uwb',[186.6,272],[356.5,319.0],-.065,s=2)
mark('large gable left wall head','gl','eave',None,[275.7,169],-.075,s=3)
mark('large gable ridge','apex','ridge',[232,17.5],[354.1,148],-.18,s=2.2)
# Far primary eave masked by projecting secondary gable, estimate rather than tie to the latter.
mark('projecting small gable left side timber corner','bu','belt',[256,376],[410.5,366.5],'bd',s=2.4)
mark('projecting small gable first corner at grade','bu',0,[246.5,611],[431,511],'bd',s=2)
mark('small gable left eave edge','bu','se',[269.5,242],[405,285],'bd',s=2.2)
mark('small gable ridge peak','sa','sr',[293.2,183],[419.6,229.4],'bd',s=1.8)
mark('small gable right eave edge','br','se',[312.0,333.5],[462,331.5],'bd',s=2.2)
mark('projecting bay window frame upper left','bwl','bwt',[263.8,446],[433.5,405.5],'bd',s=2)
mark('projecting bay window frame lower left','bwl','bwb',[260.5,516],[438.8,457.7],'bd',s=2)
guess=dict(plate_u=-.73,plate_z=2.40,wl=1.1,wr=1.81,wb=1.33,wt=2.42,gl=-1.1,belt=3.50,beam1=.12,beam2=1.34,bu=2.45,uwl=.12,uwc=.93,uwr=1.58,uwt=5.32,uwb=4.30,eave=5.98,apex=1.35,ridge=7.7,bd=-.98,se=5.33,sa=4.24,sr=6.71,br=6.0,bwl=3.12,bwt=2.30,bwb=1.31)
keys=list(guess); init=np.array(list(guess.values()))
def values(params):
 D=dict(zip(keys,params)); return lambda k:D[k] if isinstance(k,str) else k
def getxyz(a):
 v=values(a);return np.array([[v(u),v(d),v(z)] for _,u,d,z,*_ in data])
def hfit(a,b):
 mat=[]
 for (x,y),(p,q) in zip(a,b):
  mat.extend(([x,y,1,0,0,0,-p*x,-p*y,-p],[0,0,0,x,y,1,-q*x,-q*y,-q]))
 A=np.linalg.svd(mat)[2][-1].reshape(3,3);return A/A[-1,-1]
def cam_init(i):
 XY=getxyz(init);t=[k for k,p in enumerate(data) if p[4+i] is not None and p[2] in (0,-.048,-.065)]
 H=hfit(XY[t][:,[0,2]],[data[k][4+i] for k in t]);f=487 if i==0 else 400
 K=np.array([[f,0,236],[0,f,355],[0,0,1]]);A=np.linalg.inv(K)@H
 a,c=A[:,0],A[:,1];s=2/(np.linalg.norm(a)+np.linalg.norm(c))
 R=np.column_stack([a*s,np.cross(c*s,a*s),c*s]);U,L,V=np.linalg.svd(R);R=U@V
 return np.r_[Rotation.from_matrix(R).as_rotvec(),s*A[:,2],np.log(f)]
def matrix(c):
 f=np.exp(c[6]);K=np.array([[f,0,236.5],[0,f,355],[0,0,1]]);return K@np.column_stack((Rotation.from_rotvec(c[:3]).as_matrix(),c[3:6]))
def proj(P,xyz):
 t=np.column_stack((xyz,np.ones(len(xyz))))@P.T;return t[:,:2]/t[:,2:]
def residual(a):
 pts=getxyz(a[14:]);res=[]
 for i in (0,1):
  c=a[7*i:7*i+7];uv=proj(matrix(c),pts)
  for j,row in enumerate(data):
   if row[4+i] is not None:res.extend((uv[j]-row[4+i])/row[6])
  res.append((c[6]-np.log(484 if i==0 else 425))/(.026 if i==0 else .25))
 v=values(a[14:]);res.append((v('sa')-.5*(v('bu')+v('br')))/.16)
 # Front gable halves have equal pitches to the extent recoverable from the historical public façade.
 # With the far eave masked this only constrains the extrapolated right endpoint.
 return res
a=least_squares(residual,np.r_[cam_init(0),cam_init(1),init],loss='soft_l1',f_scale=1.8,max_nfev=800).x
cs=[a[:7],a[7:14]]; Ps=[matrix(c) for c in cs];D=dict(zip(keys,a[14:])); pts=getxyz(a[14:]);print({k:round(v,2) for k,v in D.items()});print('f',*[np.exp(c[6]) for c in cs])
out=[]
for j,p in enumerate(data):
 us=[]
 for i in (0,1):
  obs=p[4+i];pred=proj(Ps[i],pts[[j]])[0];us.append(None if obs is None else {'pixel':obs,'projected':pred.round(3).tolist(),'residual_px':round(float(np.linalg.norm(pred-obs)),3)})
 out.append({'point':p[0],'local_udz_m':pts[j].round(5).tolist(),'gao':us[0],'museum':us[1]})
 print(p[0],[u and u['residual_px'] for u in us])
SOURCES=json.loads((HERE/'house-three-reference-sources.json').read_bytes())['references'];cams=[]
for key,i in [('gao-08',0),('museum-current',1)]:
 c=cs[i];raw=next(r for r in SOURCES if r['name']==key);size=[473,710] if i==0 else [474,710];P=Ps[i];w,h=raw['dimensions'];K=np.diag([w/size[0],h/size[1],1])
 cams.append(dict(source=raw,observed_image_size=size,principal=[236.5,355],focal_pixels=float(np.exp(c[6])),P=P.tolist(),native_P=(K@P).tolist(),eye_udz_m=(-Rotation.from_rotvec(c[:3]).as_matrix().T@c[3:6]).tolist(),median_fit_px=float(np.median([u[['gao','museum'][i]]['residual_px'] for u in out if u[['gao','museum'][i]]]))))
doc={'schema':'wuyuan-289-house-3-front/v1','axes':'u right facing the large gable; d positive inward; z up from lane paving. Door centre u0. Main brick front d0. Metres approximate.','scale':'The clear iron door width was fixed at 1.00 m; the granite/brick threshold is 0.46 m above lane grade and the arch spring is 2.56 m. These are photographic scale assumptions. Allow roughly 10–15% on metric lengths.','method':'Joint robust nonlinear two-camera resection and coplanar/upright line adjustment. Sony DSLR-A580 16mm APS-C lens gives about 484 pixels focal in the 710px portrait; second camera focal estimated from shared marks. The far end of the larger gable remains occluded.','observations':out,'dimensions_approx_m':{k:round(float(v),5) for k,v in D.items()},'stations':cams}
(S/'measurements/house-three-two-registered-views.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
