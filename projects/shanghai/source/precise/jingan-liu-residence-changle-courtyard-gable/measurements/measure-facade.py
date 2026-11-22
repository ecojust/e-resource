"""Rectify the gable-facing plane of Gao Can 88's 2015-12-19 interior photograph."""
from pathlib import Path
import json, math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

WORK=Path(__file__).resolve().parent
W,H=452.,680.
# Camera portrait orientation, EXIF 30 mm equivalent, long side of 35 mm film is 36 mm.
F=H*30/36
scale_m=6.22
# Left vertical is seen down to the ground. On the right the projecting bay hides the
# bottom third: extrapolate its visible upper arris, and attach an explicit larger tolerance.
parts={'wall_foot_left':[117,566], 'wall_foot_right':[398,568], 'tie_top_right':[381,193], 'tie_top_left':[132,203]}
U=np.array([[-.5,0],[.5,0],[.5,1],[-.5,1]])
C=np.array(list(parts.values()),float)
K=np.array([[F,0,W/2],[0,F,H/2],[0,0,1]])
def fit(pix,sw):
 A=[]
 for (x,z),(px,py) in zip(U,pix):
  A.extend([[x,z,1,0,0,0,-px*x,-px*z,-px],[0,0,0,x,z,1,-py*x,-py*z,-py]])
 h=np.linalg.svd(A,full_matrices=True)[2][-1].reshape(3,3); h/=h[2,2]
 c=np.linalg.solve(K,h); ratio=np.linalg.norm(c[:,1])/np.linalg.norm(c[:,0]); skew=np.dot(c[:,0],c[:,1])/np.linalg.norm(c[:,0])/np.linalg.norm(c[:,1]); return h,ratio*sw,skew
picks=dict(apex=[254,49],eave_left=[121,184],eave_right=[397,165],attic_left_bottom=[234,151],attic_right_top=[275,114],upper_left_low=[192,282],upper_left_high=[234,217],upper_right_low=[276,280],upper_right_high=[319,214],lower_left_low=[164,479],lower_left_high=[210,388],plinth_top=[175,485],bay_roof_back=[249,377],bay_foot_back=[253,568])
def world(h,height,pts,sw):
 def xy(uv):
  q=np.linalg.solve(h,[*uv,1]);return np.array([q[0]*sw,q[1]*height])/q[2]
 return {k:xy(v) for k,v in pts.items()}
h,height_m,skew=fit(C,scale_m); d=world(h,height_m,picks,scale_m)
proj_m=np.array([[x*scale_m,0,z*height_m]for x,z in U]); rayseed=np.linalg.solve(K,h);r0=rayseed[:,0]/np.linalg.norm(rayseed[:,0]);r2=rayseed[:,1]/np.linalg.norm(rayseed[:,1]);r1=np.cross(r2,r0);angles=Rotation.from_matrix(np.column_stack([r0,r1,r2])).as_rotvec();t=rayseed[:,2]/np.linalg.norm(rayseed[:,0])*scale_m

def project(params,ps):
 cam=np.asarray(ps)@Rotation.from_rotvec(params[:3]).as_matrix().T+params[3:];return cam[:,:2]/cam[:,2:]*F+np.array([W/2,H/2])
res=least_squares(lambda q:(project(q,proj_m)-C).ravel(),np.r_[angles,t]);q=res.x;R=Rotation.from_rotvec(q[:3]).as_matrix();t=q[3:];center=-t@R

def unproject(uv,dim,val):
 ray=np.linalg.solve(K,[*uv,1.])@R; return center+ray*(val-center[dim])/ray[dim]
# The carried, horizontal stone course is continuous across the wall and bay; the
# 2015 lower picture lets us intersect the jamb feet and cornice returns with it.
# Tall opposite verticals of a shallow projection remove little image scale, so allow
# wide depth tolerance and round the dimension conservatively for model production.
stone_z=float(d['plinth_top'][1]);bay_picks={'west_wall_attachment':[251,485],'west_fold':[264,485],'panel_left':[286,485],'panel_right':[357,486],'right_fold':[387,485],'end_return':[424,484]}
qs={k:unproject(v,2,stone_z).tolist()for k,v in bay_picks.items()};rng=np.random.default_rng(321);V=[]
for _ in range(800):
 obs=C+rng.normal(0,[[1.8,3.0],[5,5],[1.6,2],[1.6,2]],C.shape);w=rng.uniform(5.75,6.7);hm,zt,_=fit(obs,w);v=world(hm,zt,picks,w);V.append([v[k][1]for k in picks]);
quant=np.percentile(V,[5,95],axis=0)
source=next(k for k in json.loads((WORK/'gao-images.json').read_bytes()) if k['i']==6)
out=dict(primary_photo=source,dated='2015-12-19',panel_width_estimate_m=scale_m,working_size=[W,H],focal_px=F,plane_picks=parts,notes='2015右山墙板以约6.22m宽为比例，谷歌20级屋面以原楼24.278m庭院边定向。屋面图有倾斜与树冠，宽5.75–6.70m；右脚处被凸窗遮挡。隐蔽屋面和室内未量。',source_owner=4658,width_uncertainty_m=[5.75,6.70],controls=picks,fitted_tie_height_m=height_m,camera_orthogonality_error=skew,camera_position_m=center.tolist(),reprojection_rmse_px=float(np.sqrt(np.mean(res.fun**2))),dimensions_xz_m={k:v.round(4).tolist()for k,v in d.items()},height_interval_m={k:quant[:,i].round(3).tolist()for i,k in enumerate(picks)},bay_stone_course=dict(pixel_inputs=bay_picks,z_m=stone_z,intersections_m=qs),roof_range_along_ground_edge_m=[14.7,21.5],roof_axis_estimate_m=18.1,roof_axis_longitudinal_uncertainty_m=1.4)
(WORK/'measured-facade.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:out[k]for k in ('fitted_tie_height_m','camera_position_m','reprojection_rmse_px','dimensions_xz_m','bay_stone_course')},indent=1))
