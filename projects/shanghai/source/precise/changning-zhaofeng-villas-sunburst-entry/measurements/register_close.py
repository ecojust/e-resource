"""Fit the eastern wall to surveyed controls and facade vanishing lines in the district photograph."""
from pathlib import Path
import numpy as np,json,math
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
s=Path(__file__).absolute().parents[1]
d=json.loads((s/'source/street-scale.json').read_bytes());pts=d['surveyed_local_xyz_m']
horizontal=[((559,108),(648,95)),((478,157),(559,145)),((655,133),(744,119)),((483,261),(765,237)),((489,370),(779,350)),((531,405),(618,399))]
vertical=[((400,207),(399,504)),((559,109),(562,148)),((648,95),(655,138)),((531,405),(536,477)),((618,399),(625,472)),((858,147),(864,199)),((427,342),(426,435))]
features={'east-lantern-fixture-center':((442,389),4.),'gold-shield-center':((691,445),5.),'sunburst-crown-upper-midpoint':((604,101),5.),'east-wall-inner-front-under-moulding':((401,248),12.),'east-wall-outer-front-pier-top':((861,122),9.)}
size=[1000,701];c0=np.array([2.0,-4.5,1.59]);center=np.array([1.30,.23,2.42]);front=(center-c0);front/=np.linalg.norm(front);right=np.cross(front,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(front,right);v0=Rotation.from_matrix(np.stack([right,down,front])).as_rotvec()
def profile(v):
 C=v[:3];R=Rotation.from_rotvec(v[3:6]).as_matrix();f=np.exp(v[6]);K=np.asarray([[f,0,500],[0,f,350.5],[0,0,1]])
 return C,R,K,K@np.column_stack([R,-R@C])
def error(v):
 C,R,K,P=profile(v);res=[]
 for k,(uv,sigma) in features.items():
  # The three panorama rays establish x and height. The name wall is a single
  # vertical plane; differences in depth are less precise at the crown.
  coords=np.array(pts[k]);coords[1]=.14 if 'lantern' in k else .201 if 'shield' in k else .23
  q=P@[*coords,1];res.extend((q[:2]/q[2]-uv)/sigma)
 for lines,axis in [(horizontal,[1,0,0]),(vertical,[0,0,1])]:
  vp=K@R@axis
  for p,p2 in lines:
   line=np.cross([*p,1],vp);res.append((line@[*p2,1])/np.linalg.norm(line[:2])/1.65)
 res.extend([(C[2]-1.55)/.52,(v[6]-np.log(790))/.67]);return res
v=least_squares(error,np.r_[c0,v0,np.log(850)],loss='soft_l1',max_nfev=1000,bounds=([-12,-24,.55,-7,-7,-7,np.log(300)],[12,-.3,3.,7,7,7,np.log(2100)])).x
C,R,K,P=profile(v)
# The outer survey mark is the inside crest of the eastern shoulder, also
# visible in station 7. The drain and the higher roof behind it are separate.
result=dict(C=C.tolist(),R=R.tolist(),K=K.tolist(),P=P.tolist(),size=size,
            horizontal=horizontal,vertical=vertical,controls=features,
            weighted_residuals=error(v),
            source="2021-05-06 长宁区照片，1000 × 701 对照网格",
            method="Five street-survey positions and thirteen architectural lines; soft-L1 fit. Heights are relative to the inside eastern threshold.")
(s/'source/close-camera.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
