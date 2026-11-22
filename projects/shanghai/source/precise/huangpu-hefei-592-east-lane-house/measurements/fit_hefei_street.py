"""Fit local pinhole cameras from independent street stations and exterior opening edges."""
import json,math,numpy as np
from pathlib import Path
from math import sin,cos,radians
w=Path(__file__).resolve().parent
inputs=json.loads((w/'street-station-measurements.json').read_text())['camera_inputs']
lon,lat=121.46745622,31.21574226
ang=radians(76.495);B=np.array([[sin(ang),-cos(ang),0],[cos(ang),sin(ang),0],[0,0,1.]])
def mat(k,dx=0.,dy=0.,da=0.,dp=0.,dr=0.):
 j=inputs[k];s=j['station'];e=np.array([(s['position'][0]-lon)*111320*cos(radians(lat)),(s['position'][1]-lat)*110870,s['height']]);a,p,r=map(radians,[j['az']+da,j['pitch']+dp,dr]);sa,ca,sp,cp=sin(a),cos(a),sin(p),cos(p)
 n=np.array([sa*cp,ca*cp,sp]);rr=np.array([ca,-sa,0]);up=np.cross(rr,n);m=np.array([rr*cos(r)+up*sin(r),rr*sin(r)-up*cos(r),n])
 f=j['width']/2/math.tan(radians(j['hfov']/2));K=np.array([[f,0,j['width']/2],[0,f,j['height']/2],[0,0,1]])
 return K@m@np.column_stack([B,np.array([dx,dy,0])-e])
def proj(q,M):
 p=M@np.r_[q,1];return p[:2]/p[2]
def hit(uv,M,mode):
 i=[1,2] if mode=='side' else [0,2];h=np.column_stack((M[:,i[0]],M[:,i[1]],M[:,3]));p=np.linalg.solve(h,[*uv,1.]);return p[:2]/p[2]
from scipy.optimize import least_squares
k1,k2,k3='2015_west','2015_oblique','2015_winter_side'
obs={
'n-outer-head-back':[[217.5,243.5],[315,319.5],[322,296]],
'n-outer-head-street':[[245,237.5],[342.5,319],[357,296]],
'n-sill-top-back':[[219.5,304.5],[316,378],None],
'n-sill-top-street':[[237.5,303],[341,377.5],[354.5,356.5]],
's-outer-head-back':[[313,217],[None,None],None],
's-outer-head-street':[[354,208],None,None],
's-sill-top-back':[[317,289],[448,377.5],None],
's-sill-top-street':[[347.5,285.5],[469.5,375.5],None],
'street-corner-upper':[[374,None],[501,None],None],
'street-corner-lower':[[354,None],[501,None],None],
}
# Fit each named architectural corner. Aperture quadrilaterals share near-vertical jambs and level sills.
keys=[k1,k2,k3]
# global origin E/N, three camera angular corrections in degrees. hold February camera roll & pitch close to recorded level
def material(q,i):
 if i>=8:return np.array([0,0,[6.2,1.25][i-8]])
 group=i//4;j=i%4
 level=q[11+group*4:15+group*4]
 return np.array([0,level[j%2],level[2+j//2]])
def resid(q,with_names=False):
 ms=[mat(k,*q[:2],*q[2+3*j:5+3*j]) for j,k in enumerate(keys)];rs=[];names=[]
 for i,(name,a) in enumerate(obs.items()):
  for j,uv in enumerate(a):
   if uv is None:continue
   pv=proj(material(q,i),ms[j])
   for axis,v in enumerate(uv):
    if v is None:continue
    rs.append((pv[axis]-v)/(5 if i>=8 else 2.0 if j!=2 else 3.0));names.append(name)
 # the GIS ring corner is only an envelope. Held loosely. Angles are priors in degrees
 rs.extend(q[:2]/2.0)
 for j in range(3):
  rs.extend(q[2+3*j:5+3*j]/np.array([1.4,.85,.8] if j<2 else [2.5,1.9,1.8]))
 return np.array(rs)
q0=np.r_[[0.]*11,[5.8,4.8,6.,4.4,2.1,1.1,6.,4.4]]
r=least_squares(resid,q0,loss='soft_l1');q=r.x
print('origin/angular',q[:11].round(3),'openings',q[11:].round(3))
for i,(name,a) in enumerate(obs.items()):
 xyz=material(q,i)
 print(name,xyz.round(2),[np.round(proj(xyz,mat(k,*q[:2],*q[2+3*j:5+3*j])),1).tolist() for j,k in enumerate(keys)])
allkeys=['2015_west','2015_oblique','2015_winter_side','2015_west_side','2015_winter_front','2015_front','2015_east','gate15-ne','gate17-ne','gate19-ne']
s=w.parent
fn=w/'hefei-street-cameras.json'
o=dict(units='metres; X along street towards east, Y north into lane, Z up',gis_southwest_origin=[lon,lat],long_edge_bearing=76.495,cameras={})
for k in allkeys:
 j=inputs[k];o['cameras'][k]={q:j[q] for q in ['width','height','hfov','az','pitch']};o['cameras'][k].update(station=j['station']['id'],date=j['station']['date'],wgs84=j['station']['position'])
o['stage']='Street stereo fit of two projected upper openings and the white street corner. Other years use station pose unless marked.'
o['relative_origin_EN_m']=q[:2].tolist();o['frame_origin']='intersection of street and lane wall planes at the southwest corner of the east-side street building, ground datum beside lane; absolute position approximate'
o['axis_control']='GIS west wall tangent is modeled perpendicular to 76.495-degree streetside. Approximate orthogonality; 43.594 m is the entire adjacent block edge.'
o['angular_corrections_order']='yaw, pitch and roll degrees'
for k in allkeys:
 j=keys.index(k) if k in keys else 0 if k=='gate15-ne' else None
 a=q[2+3*j:5+3*j] if j is not None else [0,0,0]
 o['cameras'][k]['angular_correction']=list(a);o['cameras'][k]['projection']=mat(k,*q[:2],*a).tolist()
 o['cameras'][k]['role']='fitted camera' if j is not None else 'unrefined orientation; approximate camera only'
o['opening_ties']={name:{'xyz':material(q,i).round(6).tolist(),'observed_pixels':dict(zip(keys,a))} for i,(name,a) in enumerate(obs.items())}
fn.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')

d=o;dest=fn;origin=d['relative_origin_EN_m']
three={'upper_sill_lane':[0,1.476,5.418],'upper_sill_street':[0,.649,5.418],'upper_head_lane':[0,1.476,6.902],'upper_head_street':[0,.649,6.902],'lower_sill_street':[0,.750,1.950],'lower_head_street':[0,.750,3.685]}
obs={'gate17-ne':{'upper_sill_lane':[207,171.5],'upper_sill_street':[240,165.5],'upper_head_lane':[212,97],'upper_head_street':[245,88],'lower_sill_street':[236,355],'lower_head_street':None},'gate19-ne':{'upper_sill_lane':[168,171.5],'upper_sill_street':[201,166],'lower_sill_street':[186.5,360]}}
for k,rows in obs.items():
 def residual(a):
  m=mat(k,origin[0]+a[0],origin[1]+a[1],*a[2:]);r=[]
  for key,point in rows.items():
   if point is not None:r.extend((proj(three[key],m)-point)/(3.7 if 'head' in key else 2.5))
  return np.r_[r,a/np.array([.55,.55,3.0,5.5,1.5])]
 fit=least_squares(residual,np.zeros(5),loss='soft_l1');p=fit.x;m=mat(k,origin[0]+p[0],origin[1]+p[1],*p[2:])
 r={}
 for key,uv in rows.items():
  if uv is not None:r[key]={'observed':uv,'projected':proj(three[key],m).round(2).tolist(),'residual_px':round(float(np.linalg.norm(proj(three[key],m)-uv)),2)}
 print(k,p.round(3),r)
 d['cameras'][k].update(role='Later images, local fit to the streetward gable aperture, two shutters and stone sill; local uncertainties increase away from this area',angular_correction=p[2:].tolist(),relative_station_offset_EN_m=(-p[:2]).tolist(),projection=m.tolist(),observations=r)
dest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
