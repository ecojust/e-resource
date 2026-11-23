"""Fit the visible gate against the 2012 photograph with a 35 mm focal-length prior."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from PIL import Image
import hashlib
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('photo',type=Path);parser.add_argument('output',type=Path)
args=parser.parse_args();photo=args.photo
width=2.8;L=(width-.10)/2; rows=[
 ('left',0,'head',(78,122),2),('left',1,'head',(233,178),2),
 ('right',0,'head',(797,94),2),('right',1,'head',(753,161),3),
 ('left',0,'rail',(77,411),2),('left',.50,'rail',(164,402),3),
 ('right',0,'rail',(800,419),2),('right',1,'rail',(754,401),3),
 ('left',1,'foot',(233,627),2),('right',1,'foot',(755,645),2),
 ('left',.125,'finial',(100,52),3),('left',.25,'finial',(120,60),3),
 ('right',.125,'finial',(791,15),3),('right',.25,'finial',(785,30),4)]
def cam(k):
 a,b,c,roll,yaw,pitch,f,*_=k
 base=np.array([[1.,0,0],[0,0,-1],[0,1.,0]])
 R=Rotation.from_euler('xyz',[pitch,yaw,roll],degrees=True).as_matrix()@base
 return np.array([[f,0,512],[0,f,341.5],[0,0,1]])@np.column_stack((R,-R@np.array([a,b,c])))
def point(k,leaf,t,z):
 al,ar,head,rail,tip=k[7:];ang=np.radians(al if leaf=='left' else ar)
 side=-1 if leaf=='left' else 1
 return np.array([side*(L-L*t*np.cos(ang)),.10+L*t*np.sin(ang),{'head':head,'rail':rail,'foot':.065,'finial':head+tip}[z],1.])
def predicted(k):
 P=cam(k);q=np.array([P@point(k,*r[:3]) for r in rows]);return q[:,:2]/q[:,2,None]
def res(k):
 a=(predicted(k)-np.array([r[3]for r in rows]))/np.array([r[4]for r in rows])[:,None]
 return np.r_[a.flat,(k[6]-995)/115,k[3]/4,(k[9]-2.24)/.35]
k=least_squares(res,[.1,-3.8,1.30,0,0,0,995,78,96,2.17,1.09,.29],bounds=([-1,-7,.65,-12,-25,-24,800,50,50,1.8,.7,.15],[1, -2,2.0,12,25,24,1250,115,115,2.8,1.4,.5]),loss='soft_l1').x
P=cam(k);errors=(predicted(k)-np.array([r[3]for r in rows])); photo_sha=hashlib.sha256(photo.read_bytes()).hexdigest()
def cut(uv,y):
 H=P[:,[0,2,3]].copy();H[:,2]+=P[:,1]*y
 X=np.linalg.solve(H,np.array([*uv,1.]));return [float(X[0]/X[2]),y,float(X[1]/X[2])]
plaque=[[878,60],[958,55],[962,110],[880,115]];corners=[cut(q,-.016)for q in plaque]
doc=dict(photo='flickr-11.jpg',sha256=photo_sha,dimensions_px=Image.open(photo).size,reference_clear_width_m=width,clear_height_m_estimate=3.05,
 clear_width_range_m=[2.50,3.15],front_post_centers_x_m=[-L,L],front_post_y_m=.10,leaf_width_m=L,opened_leaf_angles_from_closed_degrees={'left':k[7],'right':k[8]},head_z_m=k[9],middle_rail_z_m=k[10],finial_above_head_m=k[11],foot_z_m=.065,plaque_corners_xyphoto=plaque,plaque_corners_xyz_m=corners,camera=dict(eye=k[:3].tolist(),focal_px=k[6],P=P.tolist()),median_reprojection_px=float(np.median(np.linalg.norm(errors,axis=1))),max_reprojection_px=float(np.max(np.linalg.norm(errors,axis=1))), observations=[dict(leaf=r[0],distance_fraction=r[1],feature=r[2],photo_px=r[3],projected_px=a.tolist(),error_px=float(np.linalg.norm(b))) for r,a,b in zip(rows,predicted(k),errors)],notes=['Opening width is a display scale prior; vertical and horizontal dimensions share its uncertainty.','The upper street lintel and the ends of the near jambs lie outside the crop.','End-on rods in the right leaf overlap in projection. Finial count is an estimate constrained by the spacing.'])
args.output.write_text(json.dumps(doc,indent=2)+'\n')
print(k.tolist());print('median',doc['median_reprojection_px'],'max',doc['max_reprojection_px'],'plate',corners)
