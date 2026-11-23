"""Repeat the measurements on the numbered post and street wall in the two calibrated winter exterior views."""
from pathlib import Path
import numpy as np
import hashlib,json,math
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=Path)
parser.add_argument('--april-photo',type=Path,help='Original local April 2015 frame, if available.')
args=parser.parse_args()
D=Path(__file__).absolute().parent;c=json.loads((D/'gate-station-cameras.json').read_bytes())
def ray(k,uv):
 cam=c['cameras'][k];r=np.asarray(cam['R']).T@np.linalg.solve(cam['K'],[*uv,1]);return np.asarray(cam['eye']),r/np.linalg.norm(r)
def intersection(ob):
 rows=[];bs=[]
 for k in c['cameras']:
  eye,d=ray(k,ob['native_pixels'][k]);q=np.eye(3)-np.outer(d,d);rows.append(q);bs.append(q@eye)
 a=np.vstack(rows);x=np.linalg.lstsq(a,np.concatenate(bs),rcond=None)[0]
 return {'both_winter_sites':x.tolist(),'four_site_reduction':ob['xyz'],'plane_condition_number':float(np.linalg.cond(a)),'source_pixels':{k:ob['native_pixels'][k] for k in c['cameras']}}
def over_surface(k,uv,y):
 e,r=ray(k,uv);p=e+(y-e[1])/r[1]*r;return p.tolist()
obs={k:intersection(v)for k,v in c['observations'].items()}
wall={'1512g':[800,455],'2101g':[945,418]};leaf={'1512g':[945,464],'2101g':[1063,424]}
reads={}
for k,points,y,sigma in [('wall_coping',wall,-.143,4),('gate_leaf_upper_edge',leaf,-.009,7)]:
 obs_z={}
 for name,uv in points.items():
  centre=over_surface(name,uv,y);sweep=[over_surface(name,[uv[0],uv[1]+dy],y+shift)[2] for dy in (-sigma,0,sigma)for shift in (-.16,0,.16)]
  obs_z[name]={'native_px':uv,'pixel_uncertainty':sigma,'model_plane_y':y,'local_xyz':centre,'height_range_m':[min(sweep),max(sweep)]}
 reads[k]=obs_z
# April head-on station. Pier-depth and perspective differences are carried as an interval.
spring={'frame':'gate-A.jpg, April 12 2015','sha256':'1a6e90a898ed800dbd388f8c6e42b9b0c19dd240572e64003f142f769aa4ca9a','size':[840,540],
 'plaque_rectangle_pixels':[364,274,390,296],'pier_apex_pixels':[[384,243],[600,235]],'april_pier_separation_m':1.72,'pier_separation_interval_m':[1.5,1.95],
 'dimensional_check':'Pixel ratio to the surveyed pier spacing, with 2 px contour tolerance, local obliquity and camera-centre uncertainty. The metallic edge is partially blended with the render in this photograph.',
 'plaque_width_interval_m':[.17,.25],'plaque_height_interval_m':[.13,.22],'model_width_height_m':[.214,.164]}
report={'sources_sha256':{'camera_frames':hashlib.sha256((D/'gate-station-cameras.json').read_bytes()).hexdigest(),'april_survey':hashlib.sha256((D/'courtyard-gate-survey.json').read_bytes()).hexdigest()},
 'observations':obs,'additional_height_observations':reads,'april_plaque_size':spring,'model':{'left_right_pier_centres_m':[11.90,13.62],'front_y_m':-.174,'number_centre_z_m':2.15,'numbered_pier_cap_z_m':2.545,'other_pier_cap_z_m':2.565,'leaf_head_z_m':2.38,'coping_head_z_m':2.44,'leaf_base_z_m':.035,'fixed_ground_z_m':0},'limitations':'The two winter photos give two slightly different rays for each feature. The additional April and September station positions use provider orientations and alter the inferred absolute depth by approximately a decimetre. The other post keeps its observed April spacing and small height difference. Ground-zero is the inherited street pavement; a single vertical offset was not used.'}
if args.april_photo: assert hashlib.sha256(args.april_photo.read_bytes()).hexdigest()==spring['sha256']
args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print({k:[round(v['local_xyz'][2],3)for v in vv.values()]for k,vv in reads.items()})
