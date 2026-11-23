"""Transfer the two calibrated ground cameras to the two unobstructed higher street photographs."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
m=Path(__file__).resolve().parent
j=json.loads((m/'street-facade-dimensions.json').read_bytes())
U=np.array(j['along_unit_vector']);N=np.array([U[1],-U[0]])
world=np.eye(3);world[:2,0]=U;world[:2,1]=-N
def ray_camera(az,pitch,hfov,w,h):
    az,pitch=np.radians([az,pitch]);f=w*.5/np.tan(np.radians(hfov*.5))
    fwd=np.r_[np.sin(az)*np.cos(pitch),np.cos(az)*np.cos(pitch),np.sin(pitch)]
    right=np.r_[np.cos(az),-np.sin(az),0]
    return np.array([[f,0,w*.5],[0,f,h*.5],[0,0,1]])@np.array([right,np.cross(fwd,right),fwd])@world
presets=[('south',307,23,90),('front',272,28,97)]
cams=[ray_camera(*pose[1:],707,560)@np.linalg.inv(ray_camera(original,14,82,720,534))@np.asarray(s['P']) for s,original,pose in zip(j['stations'],j['original_panorama']['manual_heading_deg'],presets)]
def proj(P,point):
    uv=P@np.r_[point,1];return uv[:2]/uv[2]
obs={
 'coping.south':[(413.0,191.4),(234.5,138.3)],
 'coping.north':[(475.5,227.9),(357.4,149.4)],
 'left.head.leading':[(438.0,214.9),(275.1,151.2)],'left.head.trailing':[(447.1,220.0),(288.3,152.1)],
 'left.sill.leading':[(439.2,237.8),(270.8,174.3)],'left.sill.trailing':[(448.2,241.4),(286.5,176.0)],
 'right.head.leading':[(450.6,221.3),(301.3,153.1)],'right.head.trailing':[(457.6,225.1),(314.9,153.4)],
 'right.sill.leading':[(451.6,243.0),(299.8,177.2)],'right.sill.trailing':[(459.2,246.5),(313.6,177.9)]}
def pts(a):
    south,north,depth,top,first,second,w1,w2,head,sill=a
    return [[south,depth-.060,top],[north,depth-.060,top],
      [first,depth+.115,head],[first+w1,depth+.115,head],[first,depth+.115,sill],[first+w1,depth+.115,sill],
      [second,depth+.115,head],[second+w2,depth+.115,head],[second,depth+.115,sill],[second+w2,depth+.115,sill]]
def err(a):
    return np.ravel([[proj(cam,q)-xy for cam,xy in zip(cams,row)] for q,row in zip(pts(a),obs.values())])
a=least_squares(err,[-2.2,2.5,.65,13.4,-.82,.37,.6,.6,12.83,11.44],loss='soft_l1').x
def cut(P,uv,axis,val):
    q=P[:,:3]; b=P[:,3];x,y=uv
    return np.linalg.solve(np.vstack((q[0]-x*q[2],q[1]-y*q[2],np.eye(3)[axis])),[x*b[2]-b[0],y*b[2]-b[1],val])
south_side_corner=(378.0,216.6)
clip=cut(cams[0],south_side_corner,2,a[3])
result=dict(basis='u north along front wall, d into building, z above pavement',date='2020-02-22',raster=[707,560],original_size=[960,760],
 projections=[{'station':k[0],'pano_id':id,'panorama_direction':[k[1],k[2]],'hfov':k[3],'P':p.tolist()} for k,p,id in zip(presets,cams,j['source_panorama_ids'])],
 parameters=dict(zip(['south','north','front_d','coping_z','left_x','right_x','left_width','right_width','window_head','window_sill'],a.tolist())),
 controls=[{'name':n,'observed_px':row,'uzd':q,'projected':[proj(p,q).round(3).tolist()for p in cams],'errors_px':[round(float(np.linalg.norm(proj(p,q)-v)),3)for p,v in zip(cams,row)]}for (n,row),q in zip(obs.items(),pts(a))],
 south_side_visible={'station':'south','last_visible_top_at_pixel':south_side_corner,'projected_to_coping_z':clip.tolist(),'depth_cut_m':float(clip[1]),'scope':'Coping vanishes behind the main parapet at this point. Rear wall is not observed; close the section here.'})
(m/'roof-room-two-stations.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(np.round(a,3),np.round(clip,2),np.sqrt(np.mean(err(a)**2)),np.max(np.abs(err(a))))
