from pathlib import Path
import json
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from hashlib import sha256
from PIL import Image

import argparse
parser=argparse.ArgumentParser(description='Register published plates and intersect corresponding points in timber-span units.')
parser.add_argument('photographs',type=Path,help='Directory containing the three original JPEGs named in the survey')
parser.add_argument('output',type=Path)
args=parser.parse_args()
names=['post_l_low','post_r_low','post_l_cross','post_r_cross','outer_l_low','outer_r_low','outer_l_cross','outer_r_cross','arch_outer_apex']
views={'paper-25':('paper-2022-25.jpg',[[299.2,113],[375.3,119.4],[298.1,84.6],[374.3,89.7],[276.2,110.4],[395.2,119.2],[276.0,82.9],[394.8,92.1],[336.5,52.4]]),'sina-37':('sina-image-37.jpg',[[171.6,197.6],[305.8,193.4],[174.5,153.6],[306.4,144.7],[136.6,200.7],None,[142.4,154.7],[338.3,142.4],[243.7,93.2]]),'sina-35':('sina-image-35.jpg',[[91.0,198.3],None,[93.0,147.2],[199.3,119.4],[62.8,202.7],None,[70.0,153.4],[229.,116.5],None])}
stations={}
def xyz(shape):
 u,h,peak=shape
 return np.array([[-.5,0,0],[.5,0,0],[-.5,0,h],[.5,0,h],[-u,0,0],[u,0,0],[-u,0,h],[u,0,h],[0,0,peak]])
def cam(v,index):
 return v[3+7*index:10+7*index]
def project(points,cf,wh):
 r,t,f=cf[:3],cf[3:6],np.exp(cf[6]); W,H=wh; k=np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]])
 q=(np.array(points,dtype=float)@Rotation.from_rotvec(r).as_matrix().T+t)@k.T; return q[:,:2]/q[:,2:]
x=[.778,.357,.782]
for k,(name,points) in views.items():
 img=args.photographs/name;wh=Image.open(img).size;stations[k]={'file':name,'extent':wh,'sha256':sha256(img.read_bytes()).hexdigest(),'plane_observations':{a:b for a,b in zip(names,points) if b is not None}}
 ix=[i for i,z in enumerate(points) if z is not None];f=650.;k0=np.array([[f,0,wh[0]/2],[0,f,wh[1]/2],[0,0,1.]])
 A=[]
 for (a,_,b),(u,v) in zip(xyz(x[:3])[ix], [points[i] for i in ix]): A.extend([[a,b,1,0,0,0,-u*a,-u*b,-u],[0,0,0,a,b,1,-v*a,-v*b,-v]])
 h0=np.linalg.inv(k0)@np.linalg.svd(A)[2][-1].reshape((3,3))
 h0*=np.sign(h0[2,2])*2/(np.linalg.norm(h0[:,0])+np.linalg.norm(h0[:,1]))
 vi=h0[:,0];vk=h0[:,1];M=np.column_stack((vi,np.cross(vk,vi),vk));U,V,Vt=np.linalg.svd(M);R=U@Vt
 x.extend([*Rotation.from_matrix(R).as_rotvec(),*h0[:,2],np.log(f)])
def err(v):
 L=[]
 for idx,(_,st) in enumerate(stations.items()):
  pred=project(xyz(v[:3]),cam(v,idx),st['extent'])
  for i,key in enumerate(names):
   if key in st['plane_observations']:L.extend(pred[i]-st['plane_observations'][key])
  L.extend([.95*(cam(v,idx)[6]-np.log(650))])
 return L
opt=least_squares(err,x,loss='soft_l1',f_scale=1.5,max_nfev=600);x=opt.x
for j,st in enumerate(stations.values()):
 pp=project(xyz(x[:3]),cam(x,j),st['extent']); residual=[float(np.linalg.norm(pp[i]-st['plane_observations'][k])) for i,k in enumerate(names) if k in st['plane_observations']]
 cf=cam(x,j);r=Rotation.from_rotvec(cf[:3]).as_matrix();f=np.exp(cf[6]);W,H=st['extent'];K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]])
 st.update(P=(K@np.c_[r,cf[3:6]]).tolist(),focal_px=float(f),camera_center=(-r.T@cf[3:6]).tolist(),median_plane_reprojection_px=float(np.median(residual)),max_plane_reprojection_px=max(residual))
# Dots in original crops. On the roof the front break points lie in a different depth plane to the timber.
dots={
 'front_fascia_left':[[302,40.2],[158.4,76.8],[59.0,68.0]],'front_fascia_right':[[384.5,48.8],[292,69.7],[162.8,40.1]],
 'fascia_low_knee_l':[[275.6,70.6],[117,133.8],[37.8,136.9]],'fascia_low_knee_r':[[401,84.4],[337.6,124.0],[201.1,98.0]],
 'fascia_tip_l':[[251.6,74.2],[86.5,145],[6.1,146.7]],'fascia_tip_r':[None,[367.6,131.7],None],
 'ridge_end':[[330.8,8.3],[261.1,24.8],None],
 'wall_joint_under_balcony':[None,[237.6,216.8],[147,207.6]],'balcony_front_lip':[None,[235.8,194.0],[140.0,182.1]],
 'cap_inner_left':[[320.0,87.2],[207.4,152.8],[113.9,146.2]],'cap_inner_right':[[352.4,90.9],[269.4,151.4],[161.7,130.9]],
 'grille_bottom_left':[[320.0,105.7],[206.0,176.6],[111.1,169.6]],'grille_bottom_right':[[352.4,107.7],[269.2,175.6],[161.2,160.6]],
 'drain_face':[None,[252.2,186.9],[142.2,175.3]],'cap_outer_left':[None,[187.8,154.5],[104.2,140.2]],'cap_outer_right':[None,[289.0,148.6],[182.0,125.8]],'lip_joint_left':[None,[187.1,201.5],[100.5,193.1]],'lip_joint_right':[None,[290.7,197.0],[182.9,181.7]]
}
records={}
for key,obs in dots.items():
 rows=[(i,v) for i,v in enumerate(obs) if v]
 if len(rows)<2:continue
 def e(p):
  return np.concatenate([project([p],cam(x,i),list(stations.values())[i]['extent'])[0]-v for i,v in rows])
 fit=least_squares(e,[0,0,.4],loss='soft_l1',f_scale=1.5,max_nfev=150)
 records[key]={'observed':dict((list(stations)[i],v) for i,v in rows),'xyz_span_units':fit.x.round(5).tolist(),'reprojection_px':[round(float(k),2)for k in np.linalg.norm(e(fit.x).reshape(-1,2),axis=1)]}
print('shape',x[:3],[(k,round(v['median_plane_reprojection_px'],2),round(v['focal_px']))for k,v in stations.items()]);print([(k,v['xyz_span_units'],v['reprojection_px'])for k,v in records.items()])
result={'units':'One unit is the centre distance of the main timber uprights. Origin is their midpoint at the low transverse timber, on the plaster/timber face. +x to front photograph right, +y into the residence, +z upward.','source':{'paper':'https://www.thepaper.cn/newsDetail_forward_21316376','earlier_author':'高参 (gaocan88888)','earlier_post':'https://blog.sina.com.cn/s/blog_5d1bdf480101ee2y.html','blog_first_publication':'2013-09-04; subsequently revised with later images','note':'Plate 25 in the 2022 publication is the same exposure as plate 33 in the subsequently updated blog and is counted once.'},'uncertainty':'Single-plane image fit and unequal visibility constrain the reconstructed depth less than the silhouette. Principal points assumed at frame centres; the two images without focal metadata use a broad log-focal regularizer. Point correspondence on curved front lips is approximate.','plane_unit_geometry':dict(zip(names,xyz(x[:3]).round(6).tolist())),'photos':stations,'independent_surface_points':records}
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
