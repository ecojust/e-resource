"""Estimate a central perspective independently of the direct pixel-to-tile homography."""
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

here=Path(__file__).resolve().parents[1]/'measurements';data=json.loads((here/'terrace-frame.json').read_bytes());grid=json.loads((here/'terrace-checker-grid.json').read_bytes());h=data['projection_h_tile_to_image'];pitch=data['estimated_tile_pitch_m'];z=data['floor_to_roof_z_m'][3]
def wpt(i,j,hgt=0):return [(i-data['grid_i_at_post_row'])*pitch,(j-data['longitudinal_bounds_grid_j'][0])*pitch,z+hgt]
def inverse(x,y):
 a,b,c,d,e,f=[h[0]-x*h[6],h[1]-x*h[7],x-h[2],h[3]-y*h[6],h[4]-y*h[7],y-h[5]];q=a*e-b*d;return ((c*e-b*f)/q,(a*f-d*c)/q)
xyz=[wpt(i,j,.009)for i,j,x,y in grid['training']['points']];pixels=[(x,y)for i,j,x,y in grid['training']['points']]
for foot,top in data['guard_calibration']['foot_and_top_xy']:
 xyz.append(wpt(*inverse(*foot),.91));pixels.append(top)
xyz=np.array(xyz);pixels=np.array(pixels)
# Axes right, down and forward in the optical frame. The source is a cropped period photograph.
init=np.eye(3)[[0,2,1]];init[1]*=-1
r0=Rotation.from_matrix(init).as_rotvec();x0=np.r_[[.8,-3.7,z+1.44],r0,720.,375.,230.]
def proj(p,points):
    pos=(points-p[:3])@Rotation.from_rotvec(p[3:6]).as_matrix().T
    return pos[:,:2]/pos[:,2,None]*p[6]+p[None,7:]
def res(p):return (proj(p,xyz)-pixels).ravel()
lo=[-10,-12,z+.75,-4,-4,-4,300,150,110];hi=[6,-.5,z+2.4,4,4,4,1550,540,370]
fit=least_squares(res,x0,bounds=(lo,hi),loss='soft_l1',f_scale=1.6,xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=3000).x
R=Rotation.from_rotvec(fit[3:6]).as_matrix();obs=grid['held_out_rows']['points'];test=proj(fit,np.array([wpt(i,j,.009) for i,j,x,y in obs]))-np.array([(x,y)for i,j,x,y in obs]);rr=np.linalg.norm(test,axis=1)
# A viewer with a centred principal point uses the direction of the image midpoint, preserving the scene framing.
mid=R.T@np.array([(330-fit[7])/fit[6],(239-fit[8])/fit[6],1.]);tar=fit[:3]+mid*7.4
r={'eye':fit[:3].tolist(),'camera_rows_right_down_forward':R.tolist(),'focal_px':fit[6],'principal_xy_working':fit[7:].tolist(),'working_size':[660,478],'training_points':len(pixels),'training_rms_px':np.sqrt(np.mean(np.sum((proj(fit,xyz)-pixels)**2,axis=1))),'heldout_points':len(obs),'heldout_rms_original_px':np.sqrt(np.mean(rr**2))*945/660,'heldout_max_original_px':max(rr)*945/660,'viewer':{'eye':fit[:3].tolist(),'target':tar.tolist(),'width_m':float(np.linalg.norm(tar-fit[:3])*660/fit[6])},'assumptions':'单焦距透视与裁切后的自由主点；用方砖与栏杆高度作比例，未测胶片和物距。'}
assert r['heldout_rms_original_px']<3
(here/'terrace-camera.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
