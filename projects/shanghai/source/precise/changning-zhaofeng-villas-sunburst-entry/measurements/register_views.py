"""Project the measured gate in three January panorama stations and three independent street photographs."""
from pathlib import Path
import argparse,json,math,sys
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
import wall_plane
read=lambda p:json.loads(p.read_bytes())
s=read(HERE.parent/'source/street-scale.json');survey=read(HERE/'surveyed-street-gate.json');native=survey['native_observations'];local=np.asarray(s['basis_enu_rows']);origin=np.asarray(s['frame_origin_enu_m']);sy,by=s['initial_z_to_metres'];sx,bx=s['initial_x_to_metres'];H=np.asarray(read(HERE.parent/'source/registered-name.json')['image_to_initial_xz'])
def matrix(c,rot,f,size):
 K=np.array([[f,0,size[0]/2],[0,f,size[1]/2],[0,0,1.]]);R=np.asarray(rot);C=np.array(c);P=K@np.column_stack((R,-R@C))
 return {'C':C.tolist(),'R':R.tolist(),'K':K.tolist(),'P':P.tolist(),'size':size}
def pixel(P,x):
 q=np.asarray(P)@[*x,1.];return q[:2]/q[2]
def panoramas():
 result={};ref=np.asarray(native['frame_origin_wgs84']);scale=np.asarray([111320*math.cos(math.radians(ref[1])),110860])
 for i,d in native['sources'].items():
  co=d['camera'];a,p=np.deg2rad([co['az'],co['pitch']]);h=np.array([np.sin(a),np.cos(a),0]);up=np.array([0,0,1]);b=np.array([[np.cos(a),-np.sin(a),0],-(up*np.cos(p)-h*np.sin(p)),h*np.cos(p)+up*np.sin(p)])
  correction=Rotation.from_rotvec(np.deg2rad(survey['all_three']['camera_rotation_corrections_deg_enu'][i])).as_matrix()
  center=np.r_[(np.asarray(d['position_wgs84'])-ref)*scale,d['eye_above_road_m']]
  cam=matrix(local@(center-origin),b@correction@local.T,co['width']/(2*np.tan(np.deg2rad(co['hfov'])/2)),[co['width'],co['height']]);res={}
  for k,r in native['points'].items():
   if i in r['pixels']:res[k]=round(float(np.linalg.norm(pixel(cam['P'],s['surveyed_local_xyz_m'][k])-r['pixels'][i])),3)
  cam.update(observed_residual_pixels=res,source=d['metadata_url'],image_sha256=d['image_sha256'],station_id=d['id']);result['street-station-'+i]=cam
 return result
def xyz(uv,depth=.0):
 return wall_plane.pixel_to_world(uv,depth)
# The close-up photograph uses paired crown corners and arrises. Corners on face,
# shelf noses, applied metal letters and the lantern occupy distinct depth planes.
control={'peak-west':((559,108),.0),'peak-east':((648,95),.0),'tier-west':((478,157),.0),'tier-east':((744,119),.0),'left-vee':((521,185),.018),'peak-vee':((605,139),.018),'right-vee':((701,164),.018),'cap-west':((480,247),.068),'cap-east':((758,216),.068),'rail-west':((487,359),.046),'rail-east':((779,339),.046),'lamp':((442,389),.09),'shield':((691,445),.023)}
def fit(name,size,points,seen,initial,omit):
 n=[x for x in seen if x not in omit];objects=np.asarray([points[k] for k in n]);uv=np.asarray([seen[k]for k in n])
 X=np.asarray(initial[:3]);target=np.asarray(initial[3:6]);f0=initial[6];forward=target-X;forward=forward/np.linalg.norm(forward);side=np.cross(forward,[0,0,1]);side/=np.linalg.norm(side);down=np.cross(forward,side);R0=np.array([side,down,forward]);v0=Rotation.from_matrix(R0).as_rotvec()
 def residual(v):
  cam=matrix(v[:3],Rotation.from_rotvec(v[3:6]).as_matrix(),np.exp(v[6]),size)
  p=np.asarray(cam['P']);a=objects@p[:,:3].T+p[:,3];xy=a[:,:2]/np.maximum(.12,a[:,2,None])
  return np.r_[(xy-uv).ravel(),(v[2]-1.60)/1.20,(v[6]-np.log(f0))*1.2]
 best=least_squares(residual,np.r_[X,v0,np.log(f0)],max_nfev=1300,loss='soft_l1',f_scale=2.7,bounds=([-20,-30,.25,-7,-7,-7,np.log(min(size)*.47)],[20,-.26,4.5,7,7,7,np.log(max(size)*2.8)]))
 v=best.x;cam=matrix(v[:3],Rotation.from_rotvec(v[3:6]).as_matrix(),np.exp(v[6]),size)
 rows={k:{'world_xyz':points[k],'image_uv':seen[k],'projected_uv':pixel(cam['P'],points[k]).round(3).tolist(),'residual_px':round(float(np.linalg.norm(pixel(cam['P'],points[k])-seen[k])),3),'held_out':k in omit} for k in seen}
 cam.update(registered_controls=rows,fit_rms_px=float(np.sqrt(np.mean([r['residual_px']**2 for r in rows.values() if not r['held_out']]))),held_out_rms_px=float(np.sqrt(np.mean([r['residual_px']**2 for r in rows.values()if r['held_out']]))));return cam
def build():
 result=panoramas();points={k:xyz(u,d)for k,(u,d)in control.items()};near={k:u for k,(u,d)in control.items()}
 result['district-detail']={k:wall_plane.primary[k] for k in ('C','R','K','P','size','controls','weighted_residuals')}
 result['district-detail']['source_calibration']='../source/close-camera.json'
 reverse={'peak-west':[126,142],'peak-east':[177,161],'tier-west':[65,148],'tier-east':[222,208],'left-vee':[104,188],'peak-vee':[155,185],'right-vee':[200,229],'cap-west':[66,219],'cap-east':[228,271],'rail-west':[64,311],'rail-east':[234,349],'lamp':[19,338]}
 result['opposite-detail']=fit('opposite-detail',[331,546],points,reverse,[-.55,-2.7,1.4,1.15,.23,2.4,390],['left-vee','right-vee'])
 street={'west-lantern-fixture-center':[85,272],'east-lantern-fixture-center':[452,275],'west-green-address-plate-center':[49,194],'west-pier-inner-front-top':[134,157],'east-wall-inner-front-ground':[438,397],'east-wall-inner-front-under-moulding':[426,215],'east-wall-outer-front-ground':[579,374],'east-wall-outer-front-pier-top':[548,192],'sunburst-crown-upper-midpoint':[492,161]}
 result['road-anniversary']=fit('road-anniversary',[600,450],s['surveyed_local_xyz_m'],street,[-2.6,-6,1.5,-2,0,1.7,450],['west-green-address-plate-center','east-wall-outer-front-ground'])
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out',type=Path);a=ap.parse_args();v=build();a.out.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 for k,o in v.items():print(k,o.get('fit_rms_px'),o.get('held_out_rms_px'),o['C'])
