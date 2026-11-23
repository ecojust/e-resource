"""Fit surveyed panorama rays in the published station frame, and retain each observation and residual."""
import itertools, math, json, hashlib
from pathlib import Path
import numpy as np
D=Path(__file__).parent
names={3:'court-3-2101-349',7:'court-7-2101-320',8:'court-8-2101-292'}
scenes={i:json.loads((D/(n+'.json')).read_bytes()) for i,n in names.items()}
ref=scenes[3]['station']['position']
scale=np.array([111320*math.cos(math.radians(ref[1])),110860])
cameras={}
for i,q in scenes.items():
 a,t=map(math.radians,[q['az'],q['pitch']])
 h=np.array([math.sin(a),math.cos(a),0.])
 up=np.array([0.,0.,1.])
 cams=dict(C=np.r_[(np.array(q['station']['position'])-ref)*scale,q['station']['height']],R=np.array([math.cos(a),-math.sin(a),0]),U=up*math.cos(t)-h*math.sin(t),F=h*math.cos(t)+up*math.sin(t),f=q['width']/(2*math.tan(math.radians(q['hfov'])/2)))
 cameras[i]=cams
def ray(i,p):
 c=cameras[i];q=scenes[i]
 u=(p[0]-q['width']/2)/c['f'];v=(q['height']/2-p[1])/c['f'];d=c['F']+c['R']*u+c['U']*v
 return c['C'],d/np.linalg.norm(d)
def project(i,x):
 c=cameras[i];q=scenes[i];s=x-c['C'];z=s@c['F']
 return np.array([q['width']/2+c['f']*(s@c['R'])/z,q['height']/2-c['f']*(s@c['U'])/z])
def fit(obs):
 M=np.zeros((3,3));b=np.zeros(3)
 for i,p in obs.items():
  c,v=ray(i,p);m=np.identity(3)-np.outer(v,v);M+=m;b+=m@c
 X=np.linalg.solve(M,b);return X
def rounded(v,n=3):return np.round(v,n).tolist()
# Each native crop is 640 x 430. The three independent station centres are all from 11 January 2021.
marks={
 'west-lantern-fixture-center':[(228,212),(201,228),(169,280)],
 'east-lantern-fixture-center':[(400,207),(424,212),(311,273)],
 'west-green-address-plate-center':[(211,182),(186,198),(158,251)],
 'west-pier-inner-front-ground':[(239,282),(215,306),(176,355)],
 'west-pier-inner-front-top':[(238,163),(210,176),(174,230)],
 'east-wall-inner-front-ground':[(391,265),(409,306),(298,365)],
 'east-wall-inner-front-under-moulding':[(391,182),(412,182),(300,232)],
 'east-wall-outer-front-ground':[(470,255),(560,300),(404,380)],
 'east-wall-outer-front-pier-top':[(465,156),(555,120),(399,180)],
 'sunburst-crown-upper-midpoint':[None,(473,114),(368,166)],
 'gold-shield-center':[None,(500,230),(371,292)],
}
result={}
for label,pts in marks.items():
 obs={i:p for i,p in zip(names,pts) if p is not None}
 X=fit(obs);pairs={str((a,b)):rounded(fit({a:obs[a],b:obs[b]}))for a,b in itertools.combinations(obs,2)};res={i:round(float(np.linalg.norm(project(i,X)-uv)),2)for i,uv in obs.items()}
 result[label]={'pixels':obs,'enu_m':rounded(X),'absolute_wgs84':rounded(np.array(ref)+X[:2]/scale,9),'residual_px':res,'pair_solutions_enu_m':pairs,'predicted_pixels':{i:rounded(project(i,X),2)for i in names}}
 print(label,rounded(X,2),res,'projected',*[rounded(project(i,X),0) for i in names])
srcs={i:{'filename':n+'.jpg','image_sha256':scenes[i]['photo_sha256'],'id':scenes[i]['station']['id'],'date':scenes[i]['station']['date'],'position_wgs84':scenes[i]['station']['position'],'eye_above_road_m':scenes[i]['station']['height'],'metadata_url':scenes[i]['station']['ref']['url'],'camera':{k:scenes[i][k]for k in ['width','height','pitch','az','hfov']}}for i,n in names.items()}
report={'frame_origin_wgs84':ref,'datum':'ENU. Station 3 road surface defines Z = 0; each published station is assumed on the same road grade.','sources':srcs,'station_pair_horizontal_baseline_m':{str((a,b)):float(np.linalg.norm(cameras[a]['C'][:2]-cameras[b]['C'][:2]))for a,b in itertools.combinations(names,2)},'points':result}
(D/'gate-ray-controls.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
