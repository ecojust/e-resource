"""Compute the metric relationships of the 325 gate, the courtyard, and the paired roof.
The input consists of measured image coordinates. Original photograph pixels are not needed.
Usage: python georegister.py photographic-plot-controls.json PARENT_MEASUREMENTS OUTPUT.json
"""
import hashlib,itertools,json,math,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point,shape

def number(a):
 return np.asarray(a,dtype=float).round(5).tolist()

def similarity(source,target):
 s=[];t=[]
 for (x,y),(u,v) in zip(source,target):
  s.extend([[x,-y,1,0],[y,x,0,1]]);t.extend([u,v])
 a,b,dx,dy=np.linalg.lstsq(s,t,rcond=None)[0]
 return np.array([[a,-b,dx],[b,a,dy]])

def run(controls,measurement_dir):
 sys.path.insert(0,str(measurement_dir))
 from register_court import Camera
 c=controls;phot=json.loads((measurement_dir/'wing-cameras.json').read_bytes());front=json.loads((measurement_dir/'porch-frame.json').read_bytes())
 lon,lat=phot['origin_wgs'];angle=math.radians(phot['x_azimuth_deg']);east=111320*math.cos(math.radians(lat));north=110860.
 def xy(lng,lt):
  e,n=(lng-lon)*east,(lt-lat)*north
  return np.array([math.sin(angle)*e+math.cos(angle)*n,-math.cos(angle)*e+math.sin(angle)*n])
 def wgs(x,y):
  return [lon+(math.sin(angle)*x-math.cos(angle)*y)/east,lat+(math.cos(angle)*x+math.sin(angle)*y)/north]
 def pixel_wgs(x,y):
  ox,oy=c['mosaic_global_pixel_origin'];size=256*2**c['web_mercator_zoom']
  return [(x+ox)/size*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*(y+oy)/size))))]
 def stereo(keys):
  mats=[];bs=[]
  for key in keys:
   cam=Camera(key);v=cam.ray(c['plate_observations_native'][key]);M=np.eye(3)-np.outer(v,v);mats.append(M);bs.append(M@cam.c)
  p=np.linalg.lstsq(np.vstack(mats),np.concatenate(bs),rcond=None)[0]
  return p,{k:number(Camera(k).pixel(p)-c['plate_observations_native'][k])for k in keys}
 keys=list(c['plate_observations_native']);gate,diffs=stereo(keys);bottom=np.array(front['lower_newel_midpoint']);porch=np.array(front['frame_origin']);yard=np.zeros(2)
 results={'local_origin_wgs84':phot['origin_wgs'],'local_positive_x_bearing_true_degrees':phot['x_azimuth_deg'],'ground_floor_axes':'Metres; local +X right in the Fayhoo garden frame; +Y inward; +Z up. WGS84 is an outdoor camera association with a several-metre absolute uncertainty.','physical_no325_pier':{'local_xyz_m':number(gate),'wgs84':wgs(*gate[:2]),'residual_projected_minus_read_native_px':diffs,'pairwise_local_xyz_m':{'/'.join(q):number(stereo(q)[0])for q in itertools.combinations(keys,2)},'plan_distance_to_wing_front_anchor_m':float(np.linalg.norm(gate[:2])),'plan_distance_to_lower_newel_midpoint_m':float(np.linalg.norm(gate[:2]-bottom[:2])),'plan_distance_to_arch_reference_m':float(np.linalg.norm(gate[:2]-porch[:2])),'uncertainty':'Sign partly clipped at left in 2013. This close pole lies well forward of the features used to fit the cameras. Report the pairwise scatter and image residuals; about two metres depth uncertainty is more realistic than the digit count.'},'stairs_and_yard':{'lower_newel_midpoint_xyz':number(bottom),'porch_frame_origin_xyz':number(porch),'arch_axis_bearing_true_deg':(phot['x_azimuth_deg']-math.degrees(math.atan2(*front['axis_x'][::-1])))%360,'step_count':front['rises'],'rise_m':front['rise_m'],'run_m':front['tread_m'],'lower_newel_axis_spacing_m':front['axis_span_m'],'upper_axis_spacing_m':front['upper_axis_span_m'],'landing_height_m':front['landing_z'],'maximum_nosing_residual_native_px':float(max(abs(v)for v in front['predicted_minus_measured_dark_nosings_px'])),'wing_anchor_to_lower_newel_center_m':float(np.linalg.norm(bottom[:2])),'wing_anchor_to_porch_origin_m':float(np.linalg.norm(porch[:2])),'size_basis':'Nosing count directly read. Metric rise, run and stair width inherit the 5-station garden fit and the 2015 eye-height assumption. The outer courtyard boundary was not observed.'},'image_registrations':{}}
 for epoch,observed in c['aerial_roof_landmarks_native'].items():
  fixed=c['public_roof_native'];used=c['fit_names'];held=c['held_out_names'];F=similarity([fixed[k]for k in used],[observed[k] for k in used]);mapping=lambda uv:F@[*uv,1.]
  r={k:np.linalg.norm(mapping(fixed[k])-observed[k])for k in used+held};ground={k:xy(*pixel_wgs(*mapping(v))) for k,v in fixed.items()};boundary=Polygon([xy(*pixel_wgs(*mapping(v)))for v in c['approximate_main_roof_outline_native']])
  reports={}
  for k,native in c['candidate_polygons_local_xy'].items():
   h=shape(native);reports[k]={'overlap_area_m2':round(boundary.intersection(h).area,2),'area_native_footprint_m2':round(h.area,2),'roof_to_original_footprint_gap_m':round(boundary.distance(h),2)}
  results['image_registrations'][epoch]={'municipal_native_pixel_to_mosaic_pixel_similarity':number(F),'fit_residual_native_ortho_px':{k:round(r[k],3)for k in used},'held_out_residual_native_ortho_px':{k:round(r[k],3)for k in held},'held_out_max_m':round(max(r[k]for k in held)*c['mosaic_m_per_pixel'],3),'measured_landmark_xy_m':{k:number(v)for k,v in ground.items()},'approximate_roof_envelope_m2':round(boundary.area,2),'city_candidates':reports,'independent_fold_spacing_m':round(np.linalg.norm(ground['west gable valley']-ground['east gable valley']),2),'approximate_long_eave_span_m':round(np.linalg.norm(ground['southwest eave']-ground['southeast eave']),2)}
 return results
if __name__=='__main__':
 i,m,o=sys.argv[1:];r=run(json.loads(Path(i).read_bytes()),Path(m));Path(o).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
