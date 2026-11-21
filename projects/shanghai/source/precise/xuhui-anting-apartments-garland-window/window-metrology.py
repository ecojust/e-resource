"""Intersect two calibrated rays from independent dated street stations for each visible landmark."""
from pathlib import Path
from math import *
from hashlib import sha256
import numpy as np,json
q=Path(__file__).parent
def read(p):return json.loads(p.read_bytes())
P=lambda k:read(q/('geometry-'+str(k)+'.json'))
views=[P(2),P(3)]
ref=views[0]['station']['position'];earth=[111195.08*cos(radians(ref[1])),111195.08]
def point(v):return np.multiply(np.subtract(v,ref),earth)
def direction(v,uv):
 f=v['width']/2/tan(radians(v['hfov']/2));u=(uv[0]-v['width']/2)/f;y=(v['height']/2-uv[1])/f
 a=radians(v['az']);b=radians(v['pitch'])
 return np.array([sin(a)*(cos(b)-y*sin(b))+u*cos(a),cos(a)*(cos(b)-y*sin(b))-u*sin(a),sin(b)+y*cos(b)])
# Pixel locations are on exactly the documented 680x660 unmodified images.
marks={'plaque_lower_left':[(247,430),(119,380)],'plaque_lower_right':[(369,436),(157,383)],'plaque_upper_left':[(250,372),(120,351)],'plaque_upper_right':[(372,377),(157,352)],'arch_crown':[(318,95),(145,197)],'arch_spring_left':[(249,144),(119,228)],'arch_spring_right':[(385,141),(161,222)],'window_head_left':[(260,176),(125,241)],'window_head_right':[(377,173),(156,237)],'window_sill_left':[(258,338),(123,330)],'window_sill_right':[(373,340),(154,331)],'outer_sill_left':[(236,348),(114,337)],'outer_sill_right':[(384,351),(159,338)],'facade_south_corner':[(605,408),(224,373)]}
c=[np.array([*point(s['station']['position']),0.]) for s in views]
data={}
for label,px in marks.items():
 d=[direction(v,p)for v,p in zip(views,px)]
 t=np.linalg.lstsq(np.column_stack((d[0][:2],-d[1][:2])),(c[1]-c[0])[:2],rcond=None)[0]
 xyz=[ck+dk*tk for ck,dk,tk in zip(c,d,t)]
 mean=np.mean(xyz,axis=0);data[label]={'pixels':px,'enu_camera_datum':mean.tolist(),'height_delta_m':float(xyz[0][2]-xyz[1][2])}
def g(a):return np.array(data[a]['enu_camera_datum'])
for left,right in [('plaque_lower_left','plaque_lower_right'),('window_head_left','window_head_right'),('window_sill_left','window_head_left'),('outer_sill_left','outer_sill_right'),('plaque_lower_left','plaque_upper_left'),('arch_spring_left','arch_crown')]:
 print(left,right,np.round(g(right)-g(left),3),np.linalg.norm(g(right)-g(left)))
j=read(q/'city-part.json');we=j['way']['xy'];S=point(we[8]);N=point(we[9]);axis=(S-N)/np.linalg.norm(S-N);side=[axis[1],-axis[0]]
corner=g('facade_south_corner')[:2];mid=(g('window_sill_left')[:2]+g('window_sill_right')[:2])/2;along=float(np.dot(corner-mid,axis));anchor=np.add(ref,np.divide(S-along*axis,earth))
dist=float(np.dot(mid-(S-along*axis),side))
info={'views':[{'station':e['station']['id'],'date':e['station']['date'],'camera_wgs84':e['station']['position'],'frame':e['photo_sha256'],'projection':{'hfov':e['hfov'],'width':e['width'],'height':e['height'],'pitch':e['pitch'],'az':e['az']}} for e in views],'landmarks':data,'south_corner_distance_along_wall_m':along,'anchor_wgs84_sill_center':anchor.tolist(),'raw_center_normal_offset_m':dist,'west_edge_endpoints':we[8:10],'local_positive_x_bearing':degrees(atan2(axis[0],axis[1]))%360,'absolute_vertical_datum':'测高以同期两个相机中心的共同高度为零。绝对地面以上标高须另由同面地坪点测定。','control':'两图共同可见的临街墙南角用于消去街景与底图的平移。各地标高度差是两个相机独立测得的结果差。'}
(q/'measured-window.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
print('along',along,'anchor',anchor,'delta height',[(k,round(d['height_delta_m'],2))for k,d in data.items()])
