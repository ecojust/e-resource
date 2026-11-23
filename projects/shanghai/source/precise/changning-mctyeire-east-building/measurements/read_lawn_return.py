"""Transfer the independently observed 2017 south-east return sash corners to the existing author's metres."""
from pathlib import Path
import json
import numpy as np
s=Path(__file__).resolve().parents[1]
side_right=25.6
# The four datum points below are along the intersecting existing eave (13.41m) and ground.
# Right station on the face is set from the first projective fit to the old 70.69m main front.
def homography(src,dst):
 a=[];b=[]
 for (x,y),(u,v) in zip(src,dst):
  a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
 h=np.r_[np.linalg.lstsq(a,b,rcond=None)[0],1].reshape((3,3))
 return h
def map2(h,rows):
 p=np.c_[rows,np.ones(len(rows))]@h.T
 return p[:,:2]/p[:,2,None]
endpoints=[[0,0],[0,13.41],[side_right,13.41],[side_right,0]]
h=homography(endpoints,[[874.8,307.5],[874.0,211.2],[1093.3,195.3],[1097.0,301.1]]);inv=np.linalg.inv(h)
# Raw hand-read on the 1600x363 panorama. [left, top, right, bottom].
windows={
 'second-floor':[[891.5,216.3,903.6,231.8],[924.2,213.7,937.8,230.3],[959.6,211.1,974.6,227.7],[996.2,207.7,1011.9,225.4],[1035.4,205.8,1052.1,223.9],[1072.2,203.5,1090.1,222.2]],
 'first-floor':[[891.7,244.0,905.3,263.1],[924.6,241.0,939.1,261.8],[960.5,239.2,976.2,260.9],[996.7,237.4,1013.8,258.7],[1036.0,235.8,1053.1,256.4],[1073.5,233.8,1091.9,255.4]],
 'ground-floor':[None,[925.3,278.3,939.6,299.3],[960.7,277.2,976.5,298.2],[997.7,275.5,1014.2,297.4],[1037.6,273.9,1053.6,296.4],[1074.5,272.3,1093.1,295.4]]}
panels=[]
for level,bounds in windows.items():
 for index,r in enumerate(bounds,1):
  if r is None:continue
  a,b,c,d=r;quad=[[a,b],[c,b-.6],[c+.35,d-.6],[a+.35,d]];corners=map2(inv,quad);u0,z0=np.min(corners,axis=0);u1,z1=np.max(corners,axis=0)
  panels.append(dict(level=level,index=index,source_pixels=quad,rectified_uz_m=[round(float(x),4)for x in [u0,z0,u1,z1]]))
# Checked again in the independent single exposure, cropped origin(1330,475) and enlarged 2x.
# Separate from the window centres used in the broad photographic camera fit.
sh=[[1377,547.0,1403,575],[1442,537,1472,563],[1378,593,1407,629.2],[1447.3,587,1480,622.4],[1452,653.1,1484.5,683.0]]
hnames=[('second-floor',1),('second-floor',2),('first-floor',1),('first-floor',2),('ground-floor',2)]
refs=[(p,r) for j,r in zip(hnames,sh)for p in panels if (p['level'],p['index'])==j];input_uv=[[1344,542],[1357,695.3]];input_world=[[0,13.41],[0,0]]
for p,r in refs[:2]:
 a,b,c,d=p['rectified_uz_m'];xx,yy,xx1,yy1=r
 input_world+=[[a,d],[c,b]];input_uv+=[[xx,yy],[xx1,yy1]]
hf=homography(input_world,input_uv)
checks=[]
for p,r in refs[2:]:
 a,b,c,d=p['rectified_uz_m'];xx,yy,xx1,yy1=r
 projected=map2(hf,[[a,d],[c,b]])
 for label,expected,calc in zip(['upper-left','lower-right'],[[xx,yy],[xx1,yy1]],projected):
  checks.append(dict(window=[p['level'],p['index']],corner=label,source_uv=expected,projected_uv=calc.tolist(),distance_px=round(float(np.linalg.norm(calc-expected)),2)))
doc=dict(id='changning-mctyeire-east-building',revision_scope='Southeast lawn return in the original author coordinates, distinct from the older long courtyard face.',sources=dict(panorama=dict(title='Shanghai No. 3 Girls’ High School, Five-One lecture hall panorama',credit='Ctny, CC BY-SA 4.0',date='2017-08-21 16:44:57',size=[1600,363],sha256='f59edb1f93e506de8c72dc1847fcdc2add4ebae1498b84a7f66b1e3faf520b18'),single_exposure=dict(title='Shanghai No. 3 Girls’ High School, Five-One lecture hall',credit='Ctny, CC BY-SA 4.0',date='2017-08-21 16:37:25',size=[1600,1067],sha256='6f602d4bcc7e5a9530b54cdd3ce24d8ed6eb12681a3f00f4568a8b08f8cd8202')),frame={'x':36.55,'y_at_u_zero':3.78,'positive_u':'towards the lawn, negative Y','old_eave_z':13.41,'measurement':'Face X36.54–36.74m and its 29.5m total length are independently established by the cadastral and named OSM wall. Pixels cover only about 26m. Datum for the occluded corner base extrapolates the visible foot line. Absolute U scale over this partial plane is conditional: locked by the legacy width along the front and imperfect photographic station fit, allow ±2.3m at the tree.'},panorama_uz_to_uv=h.tolist(),front_near_wall_uz_to_uv=hf.tolist(),near_front_fit_picks=input_uv,near_front_fit_uz=input_world,near_front_independent_checks=checks,windows=panels,occlusions=['Ground floor at the first axis is entirely concealed by the end of the older arcade and shrubs. No opening is cut there.','A tree interrupts the sixth dormer; only the unoccluded face segment and left slope are modelled.','Original roof rear, entire west/north wing and the far side of this southeast wing are outside the revisited detail.'])
out=s/'measurements/lawn-return-observations.json';out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n');print(len(panels),checks);print([p['rectified_uz_m']for p in panels[::3]])
