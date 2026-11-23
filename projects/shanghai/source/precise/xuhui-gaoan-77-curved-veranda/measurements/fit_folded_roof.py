from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
p=Path(__file__).with_name('curved-veranda-three-views.json')
data=json.loads(p.read_text())
stations=dict(data['photos']); originals=data['photos']
# Fourth file is an independent south-east exposure with the complete ridge end.
stations['sina-38']={'extent':[690,459],'file':'sina-image-38.jpg','plane_observations':{'post_l_low':[107.5,211.5],'post_l_cross':[110.7,171.2],'post_r_cross':[192.2,151.9],'outer_l_low':[84.8,214.8],'outer_l_cross':[90.4,177.0],'outer_r_cross':[220.5,148.2]}}
roof_points={k:v['observed']for k,v in data['independent_surface_points'].items()if k.startswith(('fascia','front_fascia','ridge'))}
add={'front_fascia_left':[84.2,109.1],'front_fascia_right':[165.1,78.8],'fascia_low_knee_l':[63.,161.6],'fascia_low_knee_r':[199.8,124.0],'fascia_tip_l':[41.1,176.7],'ridge_end':[190.7,47.1]}
for k,v in add.items():roof_points[k]['sina-38']=v
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--free-focal',action='store_true',help='Reproduce the first weak photo-frame prior.')
parser.add_argument('--omit',choices=['sina-35','sina-38'])
parser.add_argument('--output',type=Path,default=Path(__file__).with_name('curved-veranda-folded-roof.json'))
args=parser.parse_args()
if args.omit:
    stations.pop(args.omit)
plane=data['plane_unit_geometry']
def points(s):
 w,h,ac,xf,xk,xt,zk,zt,zr,df,dr,xo=s
 zf=zk+(zr-zk)*(1-xf/xk)
 kw={'front_fascia_left':[-xf+xo,df,zf],'front_fascia_right':[xf+xo,df,zf],'fascia_low_knee_l':[-xk+xo,df,zk],'fascia_low_knee_r':[xk+xo,df,zk],'fascia_tip_l':[-xt+xo,df,zt],'ridge_end':[xo,dr,zr]}
 for k,pos in plane.items():
  x,y,z=pos
  if k.startswith('outer'):x=w*np.sign(x)
  if 'cross'in k:z=h
  if 'apex'in k:z=ac
  kw[k]=[x,y,z]
 return kw
shape=[.76,.39,.9,.52,.81,1.07,.4,.34,1.75,-.33,.45,0]
cams=[]
for name,st in stations.items():
 W,H=st['extent']
 prev=st if name!='sina-38' else originals['sina-35'];f=prev['focal_px'];KW,KH=prev['extent'];K=np.array([[f,0,KW/2],[0,f,KH/2],[0,0,1.]])
 cc=np.linalg.inv(K)@np.array(prev['P']);cams.extend([*Rotation.from_matrix(cc[:,:3]).as_rotvec(),*cc[:,3],np.log(f)])
def camera(j,q):
 cf=q[12+j*7:19+j*7]; st=list(stations.values())[j];W,H=st['extent'];f=np.exp(cf[6]);K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]])
 return K@np.c_[Rotation.from_rotvec(cf[:3]).as_matrix(),cf[3:6]]
def err(q,raw=False):
 body=points(q[:12]);res=[]; reports={}
 for j,(name,st) in enumerate(stations.items()):
  P=camera(j,q)
  obs={**st['plane_observations'],**{k:v[name] for k,v in roof_points.items()if name in v}}
  uv=np.array(list(obs.values()));xyz=np.array([[*body[k],1]for k in obs])
  xy=xyz@P.T;dv=xy[:,:2]/xy[:,2:]-uv
  reports[name]={'focal_px':np.exp(q[18+j*7]),'P':P.tolist(),'residuals':dict(zip(obs,np.linalg.norm(dv,axis=1).round(3).tolist())),'measured':obs}
  for k,r in zip(obs,dv):
   res.extend(r*(.8 if k.startswith(('fascia','front_fascia','ridge'))else 1))
  if not args.free_focal and name in ('sina-37','sina-38'):
   nominal={'sina-37':1009.,'sina-38':864.}[name]
   res.extend([60*(q[18+j*7]-np.log(nominal))])
  else:res.extend([1.4*(q[18+j*7]-np.log(650))])
 shape0=q[:12]
 for j,t,s in [(0,.76,.12),(1,.38,.14),(2,.89,.23),(3,.515,.12),(4,.81,.14),(5,1.07,.20),(6,.4,.22),(7,.34,.20),(8,1.65,.50),(9,-.33,.30),(10,.45,.4),(11,0,.055)]:
  res.append((shape0[j]-t)/s)
 if raw:return reports
 return res
q=least_squares(err,[*shape,*cams],loss='soft_l1',f_scale=1.5,max_nfev=250,ftol=1e-7,xtol=1e-7).x
pts=points(q[:12]);r=err(q,True)
print(q[:12]); print('pts',{k:v for k,v in pts.items()if k in roof_points});print([(n,round(s['focal_px']),np.median(list(s['residuals'].values())),max(s['residuals'].values()),s['residuals'].get('ridge_end'))for n,s in r.items()])
out={'units':'Main timber post span. All roof points constrained to paired rakes and a common main side pitch.','sources':data['source'],'direction_groups':[['paper-25'],['sina-37'],['sina-35','sina-38']],'focal_information':{'sina-37':'2018-02-27 09:31:27, DSLR-A580, 35mm, equivalent 52mm; nominal focal about 1009 pixels on the 690-pixel width','sina-38':'2018-02-27 16:22:15, DSLR-A580, 30mm, equivalent 45mm; nominal focal about 864 pixels on the 690-pixel width'},'free_focal':args.free_focal,'controls':pts,'stations':r,'parameters':dict(zip(['outer_frame_x','cross_timber_height','arch_peak','upper_hip_half_width','knee_half_width','eave_tip_half_width','knee_height','tip_height','ridge_height','fascia_y','ridge_y','roof_centre_offset'],q[:12].tolist()))}
args.output.write_text(json.dumps(out,indent=2)+'\n')
