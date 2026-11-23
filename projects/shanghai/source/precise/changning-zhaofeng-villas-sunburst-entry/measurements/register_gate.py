"""Register three 2021 station orientations to the observed gate while retaining their published centres."""
import json,math,itertools,hashlib,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
D=Path(__file__).parent;raw=json.loads((D/'gate-ray-controls.json').read_bytes())
sources=raw['sources'];ref=np.array(raw['frame_origin_wgs84']);scale=np.array([111320*math.cos(math.radians(ref[1])),110860])
labels=list(raw['points']);rawpts=raw['points'];pairs=[('west-pier-inner-front-ground','west-pier-inner-front-top')]
I=[3,7,8]
def build(stations,leave=None):
 cams={}
 for i in stations:
  s=sources[str(i)];j=s['camera'];a,t=np.deg2rad([j['az'],j['pitch']]);h=np.array([np.sin(a),np.cos(a),0.]);up=np.array([0.,0.,1.]);C=np.r_[(np.array(s['position_wgs84'])-ref)*scale,s['eye_above_road_m']];U=up*np.cos(t)-h*np.sin(t);F=h*np.cos(t)+up*np.sin(t);R=np.array([np.cos(a),-np.sin(a),0]);cams[i]=(C,np.stack([R,U,F],axis=0),j['width']/(2*np.tan(np.deg2rad(j['hfov'])/2)))
 coords=np.array([rawpts[l]['enu_m']for l in labels]);active=[i for i,l in enumerate(labels)if l!=leave and sum(str(c)in rawpts[l]['pixels']for c in stations)>=2]
 obs=[(ii,j,np.array(rawpts[l]['pixels'][str(st)])) for ii,st in enumerate(stations) for j,l in enumerate(labels) if j in active and str(st) in rawpts[l]['pixels']]
 def residual(z,details=False):
  rotations=z[:3*len(stations)].reshape(-1,3);pts=z[3*len(stations):].reshape(-1,3);pix=[];projected={}
  for k,j,uv in obs:
   st=stations[k];c,m,f=cams[st];v=Rotation.from_rotvec(np.deg2rad(rotations[k])).apply((pts[j]-c))@m.T
   pred=np.array([320+f*v[0]/v[2],215-f*v[1]/v[2]]);pix.extend((pred-uv)/2.5);projected[(labels[j],st)]=pred
  if details:return projected
  # Independently observed pavement contacts, less certain behind the planter.
  for l,unc in [('west-pier-inner-front-ground',.08),('east-wall-inner-front-ground',.18),('east-wall-outer-front-ground',.17)]:
   if labels.index(l)in active:pix.append(pts[labels.index(l),2]/unc)
  for lo,hi in pairs:
   a,b=labels.index(lo),labels.index(hi)
   if a in active and b in active:pix.extend((pts[a,:2]-pts[b,:2])/.075)
  # Angular priors are deliberately soft. GNSS station centres supply the only scale.
  pix.extend((rotations/5).ravel())
  return np.asarray(pix)
 z0=np.r_[np.zeros(3*len(stations)),coords.ravel()];opt=least_squares(residual,z0,loss='soft_l1',max_nfev=110)
 z=opt.x;res=residual(z,True);pts=z[3*len(stations):].reshape(-1,3);ang=z[:3*len(stations)].reshape(-1,3)
 def point(l):return pts[labels.index(l)]
 A=point('west-pier-inner-front-ground');B=point('east-wall-inner-front-ground');C=point('east-wall-outer-front-ground');G=(A+B)/2;ax=C[:2]-B[:2];ax/=np.linalg.norm(ax);dep=np.array([-ax[1],ax[0]])
 if dep[1]<0:dep*=-1
 inner=point('east-wall-inner-front-under-moulding');mid=(B+C)/2
 measures={'gate_ground_clear_chord':np.linalg.norm(B[:2]-A[:2]),'gate_opening_projected_to_frontage_axis':(inner[:2]-A[:2])@ax,'wall_inside_corner_depth_from_west':(inner[:2]-A[:2])@dep,'right_name_wall_visible_planter_and_frontage_width':np.linalg.norm(C[:2]-B[:2]),'west_gate_post_observed_top_height':point('west-pier-inner-front-top')[2]-A[2],'right_east_end_top_height':point('east-wall-outer-front-pier-top')[2]-C[2],'right_sunburst_crown_height':point('sunburst-crown-upper-midpoint')[2]-mid[2],'right_front_normal_displacement_from_west_ground':(B[:2]-A[:2])@dep,'east_minus_west_fixture_normal_displacement':(point('east-lantern-fixture-center')[:2]-point('west-lantern-fixture-center')[:2])@dep,'right_panel_axis_true_bearing_deg':np.rad2deg(np.arctan2(ax[0],ax[1]))%360}
 if labels.index('sunburst-crown-upper-midpoint')not in active:measures.pop('right_sunburst_crown_height')
 ll=lambda xy:np.round(ref+xy[:2]/scale,9).tolist()
 return {'used_stations':stations,'left_out_landmark':leave,'camera_rotation_corrections_deg_enu':{st:ang[i].round(3).tolist()for i,st in enumerate(stations)},'registered_points':{l:{'enu':point(l).round(3).tolist(),'wgs84':ll(point(l)),'observed_minus_predicted_pixels':{st:(np.array(rawpts[l]['pixels'][str(st)])-res[(l,st)]).round(2).tolist()for st in stations if (l,st)in res}} for l in labels if labels.index(l)in active},'gate_opening_midpoint_wgs84':ll(G),'measures':{k:round(v,3)for k,v in measures.items()},'rms_pixels':round(float(np.sqrt(np.mean([np.linalg.norm(res[(labels[j],stations[i])]-uv)**2 for i,j,uv in obs]))),3)}
full=build(I);print(json.dumps(full,ensure_ascii=False,indent=1))
pairs_out=[]
for pair in [[3,7],[3,8],[7,8]]:pairs_out.append(build(pair))
report={'method':'Independent pinhole extracts of the native 2021 panoramas. The published vehicle centres are fixed. World-space camera rotations are jointly fit to marked stationary features; wall recesses and pillar widths are unconstrained. Include raw advertised headings and their unadjusted ray intersections in gate-ray-controls.json. Ground contacts are regularized to the station roadway plane, two contacts are partially hidden by the planter and barrier. All positions remain conditional on the producer GNSS baseline, panorama stitching, local vertical and roadway grade.','native_observations':raw,'all_three':full,'separate_station_pairs':pairs_out}
(D/'surveyed-street-gate.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
