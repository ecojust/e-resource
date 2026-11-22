"""Refit two historic street facade cameras from measured lines, matching keypoints and a public pavement view."""
from pathlib import Path
import numpy as np,json

S=Path(__file__).resolve().parents[1]
data=json.loads((S/'measurements/marconi-registration-observations.json').read_text())
def unit(p):return p/np.linalg.norm(p)
def ground(view,pixel,height):
 az,el=np.deg2rad([view['az'],view['pitch']]); f=view['width']/2/np.tan(np.deg2rad(view['hfov']/2))
 look=np.r_[np.sin(az)*np.cos(el),np.cos(az)*np.cos(el),np.sin(el)];right=np.r_[np.cos(az),-np.sin(az),0];up=np.cross(right,look)
 frame=np.array([[f,0,view['width']/2],[0,f,view['height']/2],[0,0,1.]])@np.array([right,-up,look])
 ray=np.linalg.solve(frame,[*pixel,1]);return ray*(-height/ray[2])
native={'2017':data['principal_axis_observations']}; h={k:np.array(v,dtype=np.float32) for k,v in data['matched_native_pixels'].items()}; h['homography']=np.array(data['common_plane_2015_to_2017'])
vx=np.array(native['2017']['horizontal']['point']);vz=np.array(native['2017']['vertical']['point'])
fr=np.hypot(2988,5312)*28/43.2666;cx=1494
cy=min(np.roots([1.,-(vx[1]+vz[1]),vx[1]*vz[1]+(vx[0]-cx)*(vz[0]-cx)+fr*fr]),key=lambda q:abs(q-2656))
K=np.array([[fr,0,cx],[0,fr,cy],[0,0,1.]])
rx=-unit(np.linalg.solve(K,[*vx,1]));rz=unit(np.linalg.solve(K,[*vz,1]));ry=np.cross(rz,rx)
# For image coordinates X right, Z image-up, the facade normal into the building has positive optical depth.
if ry[2]<0:ry=-ry
Rmat=np.stack([rx,ry,rz],axis=1)
base_uv=(2270.,4327.);ref_points=[[2000.,4287.],[2547.,4362.]]
translation=np.linalg.solve(K,[*base_uv,1])
def compose(scale):return K@np.column_stack([Rmat,translation*scale])
def inv(P,uv,y):
 plane=P[:,[0,2,3]].copy();plane[:,2]+=y*P[:,1];p=np.linalg.solve(plane,[*uv,1]);return p[:2]/p[2]
def proj(P,p):v=P@np.r_[p,1.];return (v[:2]/v[2]).tolist()
view=data['street_view_parameters'];gpx=[[343,839],[543,830]];nominal=2.32;curb=.13
gd=np.array([ground(view,uv,nominal-curb) for uv in gpx]);span=float(np.linalg.norm(gd[1,:2]-gd[0,:2]))
# Fit the span at the two front plinth corners. Their common forward projection is approximately 0.12 m.
from scipy.optimize import brentq
def width(scale):
 a,b=[inv(compose(scale),uv,-.12) for uv in ref_points];return b[0]-a[0]
scale=brentq(lambda q:width(q)-span,1,30);P=compose(scale)
# Pin pavement at the mid-line of the two plinth clear corners; Y=0 at the main wall, behind its plinth.
pairs=[inv(P,q,-.12) for q in ref_points];xc,zc=np.mean(pairs,axis=0);P[:,3]+=xc*P[:,0]+zc*P[:,2]
H=np.linalg.solve(h['homography'],P[:,[0,2,3]])
x,z,t=H.T
# The revealed return wall supplies a third vanishing direction. This avoids inferring the normal solely from the front wall.
side=data['oblique_return_axis_observations'];vpy=np.asarray(side['point'])
vpx=x[:2]/x[2];vpz=z[:2]/z[2]
cxy=np.linalg.solve([vpx-vpy,vpz-vpy],[(vpx-vpy)@vpz,(vpz-vpy)@vpx])
f2=np.sqrt(-(vpx-cxy)@(vpz-cxy))
k=np.array([[f2,0,cxy[0]],[0,f2,cxy[1]],[0,0,1]])
sa,sc=[np.linalg.norm(np.linalg.solve(k,col)) for col in (x,z)]
inward=unit(np.linalg.solve(k,[*vpy,1]))*np.sqrt(sa*sc)
other=np.stack([x,k@inward,z,t],axis=1)
pts=h['target_xy'];res=h['residual_px']
portal=[('keystone lower mid',[2283,2821],[1915,4125]),('keystone lower left',[2238,2821],None),('keystone lower right',[2329,2824],None),('east shoulder extremity',[1970,3014],[1723,4380]),('west shoulder extremity',[2600,3001],None),('east capital lower band',[1963,3419],[1770,4854]),('west capital lower band',[2629,3455],None)]
out=dict(id='huangpu-marconi-beijing-east-131-front',coordinates='X positive west along Beijing East Road; Y positive south into the building from its principal brick street wall; Z above adjacent pavement, X0 entrance axis.',dimensions_upright=[2988,5312],camera_matrices={'2017_front':P.tolist(),'2015_oblique':other.tolist()},projection='P @ [X,Y,Z,1], u,v equal the first two components divided by the third.',cameras={'2017_front':dict(file='北京东路131号-2017-08-31.jpg',creator='Antigng',license='CC BY-SA 4.0',date='2017-08-31',sha256=data['source_photos']['2017_front'],focal_native_px=fr,estimated_principal_px=[cx,float(cy)],vp_x=vx.tolist(),vp_z=vz.tolist(),line_support=[241,143]),'2015_oblique':dict(file='北京东路131号.jpg',creator='Antigng',license='CC BY-SA 4.0',date='2015-07-20',sha256=data['source_photos']['2015_oblique'],effective_projective_intrinsics=[*cxy,float(f2)],side_vanishing_point_px=vpy.tolist(),side_line_count=side["count"],side_edges_median_error_deg=side["median_degrees"],metric_axes_relative_scale_ratio=float(sa/sc),note="The effective projective focal distance from three orthogonal edge families differs from the EXIF-equivalent focal length. The common facade homography remains empirical; depths use the photographed return direction.")},historic_street_scale=dict(source_date=view['station']['date'],source_id=view['station']['id'],source_hash=view['photo_sha256'],view={k:view[k]for k in ('az','pitch','hfov','width','height')},station_height_m=nominal,assumed_kerb_rise_m=curb,sidewalk_height_sensitivity_m=[.05,.21],feet_in_street_view_px=gpx,feet_in_2017_px=ref_points,feet_horizontal_length_m=span,plinth_front_relative_to_wall_m=-.12,estimated_span_uncertainty_m=.13),common_plane=dict(source='2015_oblique',target='2017_front',matrix=h['homography'].tolist(),matched_points=len(pts),residual_median_px=float(np.median(res)),residual_90pc_px=float(np.percentile(res,90)),observations_file='marconi-wall-matches.json',limits='Station height and pavement rise set the metric scale. The ornamental relief and brick face can occupy different Y. The 2015 normal axis is inferred from the common-plane match and approximate intrinsics; camera-dependent Y is estimated.'),portal_upright_px=[dict(feature=n,front=u,oblique=v,approximate_xz_at_y0=inv(P,u,0).tolist(),wall_plane_oblique_prediction=proj(other,[inv(P,u,0)[0],0,inv(P,u,0)[1]])) for n,u,v in portal])
m=S/'measurements';m.mkdir(exist_ok=True);(m/'marconi-front-cameras.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(m/'marconi-wall-matches.json').write_text(json.dumps(dict(first='2015_oblique',second='2017_front',pairs=np.round(np.column_stack([h['source_xy'],h['target_xy']]),3).tolist()),indent=1)+'\n')
print('ground',gd,'span',span,'effective',cxy,f2,'origin',base_uv,'cam',np.linalg.solve(-P[:,:3],P[:,3]),'cam2',np.linalg.solve(-other[:,:3],other[:,3]));print(out['portal_upright_px'])
