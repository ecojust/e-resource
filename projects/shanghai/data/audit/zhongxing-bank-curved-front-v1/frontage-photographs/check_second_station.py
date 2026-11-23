"""Fit a second independently published optical station to two frozen elevation hypotheses."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
p=argparse.ArgumentParser();p.add_argument('--photo',type=Path,required=True);p.add_argument('--corner',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
corner=json.loads(a.corner.read_bytes());first=json.loads(a.model.read_bytes());r=corner['arc_radius_m'];span=corner['fit']['spacing_m']
obs={'ground-contact':[(283,482),(382,485),(476,483)],'ground-aperture-sill':[(282,450),(382,451.5),(475,452)],'ground-aperture-head':[(282,393.5),(382,393.5),(475,397)],
'base-cap':[(285,345),(384,344),(476,350.5)],'L2-sill':[(285,340),(384,340),(475,346)],'L2-head':[(285,303.5),(384,300),(475,309)],
'L3-sill':[(289,265),(385,263),(469.5,274)],'L3-head':[(289,230),(385,224.5),(469.5,236)],
'L4-sill':[(294.5,198),(385,190),(467,204)],'L4-head':[(294.5,163),(385,154.5),(467,169)],
'L5-sill':[(299,132.5),(385,121.5),(464.5,139)],'L5-head':[(299,107),(385,96.5),(464.5,115)],
'L6-sill':[(302,60),(386,47.5),(464,66)],'L6-head':[(302,37.5),(386,25.5),(464,47)]}
alpha=np.arange(-1,2)*span/r
base=np.c_[r*np.sin(alpha),r*(1-np.cos(alpha))]
uv=np.array(list(obs.values())).reshape(-1,2)
weights=np.repeat([.4,.65,.75,.7]+[1.]*10,3)[:,None]
def compare(key):
 z=[first['model_and_conditional_photo_m'][name][key] for name in obs]
 world=np.vstack([np.c_[base,[h]*3]for h in z])
 def project(v):
  yaw,pitch,roll=v[3:6];dr=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
  rt=[np.cos(yaw),-np.sin(yaw),0];mat=Rotation.from_rotvec([0.,0.,roll]).as_matrix() @ np.array([rt,np.cross(dr,rt),dr])
  camera=(world-v[:3]) @ mat.T
  return camera[:,:2]/camera[:,2,None]*(690*v[6]/36)+[344.5,254.5]
 fit=least_squares(lambda v:((project(v)-uv)*weights).ravel(),[0,-20,1.6,0,.43,0,24.],
     bounds=([-15,-80,-3,-.9,-.5,-.22,14.],[15,-5,8,.9,1.3,.22,48.]),loss='soft_l1',f_scale=1.,max_nfev=600)
 err=np.linalg.norm(project(fit.x)-uv,axis=1)
 return {'photographer_xyz_m':fit.x[:3].tolist(),'yaw_pitch_roll_degrees':np.degrees(fit.x[3:6]).tolist(),'estimated_focal_35mm_equiv':float(fit.x[6]),'median_px':float(np.median(err)),'max_px':float(err.max()),'median_each_level_px': {k:float(np.median(err[i*3:i*3+3]))for i,k in enumerate(obs)},'projected_xy':project(fit.x).tolist()}
d={'reference_page':'https://blog.sina.com.cn/s/blog_5d1bdf480102vf2v.html','image_number':1,'published':'2015-01-26','capture_date':None,'photograph_sha256':hashlib.sha256(a.photo.read_bytes()).hexdigest(),'image_size':[690,510],'native_pixels':obs,'station_fit_notes':'Independent station and 42 independent pixels, with focal length estimated from a single image lacking EXIF. Shared 13.05 m arc, 3 axes and origin with the first photograph. Ground datums are partly obscured. Both use the same loss and lower confidence at street level.','original_model_elevations':compare('model'),'first_photograph_conditional_elevations':compare('photo')}
assert d['photograph_sha256']=='cc491c914bf9486a35179e1fcaa69f36e013406aa7c2fc734961f1e031f3a37b'
a.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print([(i,d[i]['median_px'],d[i]['max_px'],d[i]['estimated_focal_35mm_equiv'])for i in ['original_model_elevations','first_photograph_conditional_elevations']])
