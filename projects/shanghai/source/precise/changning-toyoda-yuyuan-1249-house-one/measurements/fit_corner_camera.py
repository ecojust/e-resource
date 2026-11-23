"""Fit a corner camera to local side-window controls and two elevations' line directions."""
from pathlib import Path
import json,numpy as np,sys
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
S=Path(__file__).absolute().parents[1]
sys.path.insert(0,str(S/'measurements'))
from check_triple_windows import camera
def cam(name):
    item=json.loads((S/'measurements/triple-window-calibration.json').read_bytes())['views'][name]
    m,o=camera(item,{})
    return np.diag([650/item['image_size'][0],650/item['image_size'][0],1])@np.column_stack((m,-m@o)),o
cal=json.loads((S/'measurements/triple-window-calibration.json').read_bytes())['views']['commons2018']
K=np.array([[661.1,0,425],[0,661.1,239],[0,0,1.]])
P,O=cam('commons2018');P=np.diag([850/650,850/650,1])@P
D=np.linalg.solve(K,P[:,:3]);U,sv,V=np.linalg.svd(D);R=U@V
if np.linalg.det(R)<0:R=-R
init=[*Rotation.from_matrix(R).as_rotvec(),*O,661.1]
points=[]
z=1.55+2.381*.66
for i in range(3):
 for j in range(2):
  points.append(([0,4.23+(i*1.64175+j-.5)*.66,z],np.array(cal['controls']['spring'][2*i+j])*850/5312))
 points.append(([0,4.23+i*1.64175*.66,1.55+.4563*2.381*.66],np.array(cal['controls']['bar'][i])*850/5312))
lines={'X':[[[130,277],[204,207]],[[134.5,297],[188,259]],[[223,340],[308,302]]],
'Y':[[[409,296],[561,308]],[[411,310],[557,319]],[[411,357],[553,361]]],
'Z':[[[218,329],[220,201]],[[321,285],[309,151]],[[466,260],[459,186]],[[564,259],[555,197]]]}

def matrices(a):
 K1=K.copy();K1[0,0]=K1[1,1]=a[-1];M=K1@Rotation.from_rotvec(a[:3]).as_matrix();return M,-M@a[3:6]
def uv(p,P):v=P@np.r_[p,1];return v[:2]/v[2]
def res(a):
 m,t=matrices(a);p=np.column_stack([m,t]);res=[]
 for xyz,s in points:res.extend(uv(xyz,p)-s)
 for k,v in enumerate(lines.values()):
  for aa,bb in v:
   a0=np.r_[aa,1];b0=np.r_[bb,1];L=np.cross(a0,b0);vp=m[:,k]
   res.append((L@vp)/np.linalg.norm(vp[:2]-vp[2]*np.array(aa))*1.3)
 res.append((a[-1]-661.1)/9)
 return res
f=least_squares(res,init,loss='soft_l1',f_scale=2,max_nfev=4000);m,t=matrices(f.x);P=np.column_stack([m,t]);O=f.x[3:6]
def cut(u,v,axis=1):
 i=[k for k in range(3)if k!=axis]+[3];h=np.linalg.solve(P[:,i],[u,v,1]);return np.round(h[:2]/h[2],3)

features={'front-crown':[(129.5,277.5),(151.4,259.5),(174.4,235.2),(205,207)],'spring-cols':[(138.3,296.3),(160.3,274),(188,257.8)],'front-right':[(220,326),(220,201),(263,275),(263,162),(307,302),(213,341)],'side':[(310,302),(315,110),(459,262),(396,152),(572,261),(598,198),(649,238),(680,201),(554,175),(554,140),(560,305),(696,136)]}
out={'source':'commons-full.jpg','original_size':[5312,2988],'digitised_width_px':850,'P':P.tolist(),'P_original':(np.diag([5312/850,5312/850,1])@P).tolist(),'eye':O.tolist(),'focal_850':f.x[-1],'controls':[[p,xy.tolist()]for p,xy in points],'vanishing_line_controls':lines,'signed_residuals':res(f.x),'features':{n:[{'pixel_850':v,'xz_or_yz_m':cut(*v,axis=int(n!='side')).tolist()}for v in arr]for n,arr in features.items()}}
(S/'measurements/commons-corner-camera.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
