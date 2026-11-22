"""Estimate north-front camera matrices from shared facade edges, photographed passage and street-level triangulation."""
from pathlib import Path
import math,json
import numpy as np
from scipy.optimize import least_squares
from math import cos,sin,radians
w=Path(__file__).resolve().parent
lon,lat=121.45976985847435,31.213092386457628
camnames=['center15','center15-upper','west15','west15-upper','east15','east15-upper','center20-upper','center20']
sources=json.loads((w/'yongjia-station-measurements.json').read_text())['sources']
def pose(k,o,ab,delta):
 j=sources[k];s=j['station'];en=np.array([(s['position'][0]-lon)*111320*cos(radians(lat)),(s['position'][1]-lat)*110870,s['height']])
 ang=radians(ab);B=np.array([[sin(ang),-cos(ang),0.],[cos(ang),sin(ang),0.],[0.,0.,1.]])
 a,p,r=map(radians,[j['az']+delta[0],j['pitch']+delta[1],delta[2]]);sa,ca,sp,cp=sin(a),cos(a),sin(p),cos(p)
 n=np.array([sa*cp,ca*cp,sp]);rr=np.array([ca,-sa,0]);up=np.cross(rr,n);m=np.array([rr*cos(r)+up*sin(r),rr*sin(r)-up*cos(r),n]);f=j['width']/2/math.tan(radians(j['hfov']/2))
 K=np.array([[f,0,j['width']/2],[0,f,j['height']/2],[0,0,1]])
 return K@m@np.column_stack((B,np.r_[o,0]-en))
def pix(x,m):
 t=m@np.r_[x,1.];return t[:2]/t[2]
def station(k):return k.split('-')[0]
F=['center15','west15','east15','center20']
# Coarse raster reads in each 1.22x panel. Convert back to native photograph pixels below.
rect={'center15-upper':(275,220),'west15-upper':(370,224),'east15-upper':(391,229),'center20-upper':(205,125),'center15':(180,257),'west15':(365,281),'east15':(370,285)}
reads={
'center15-upper':{'leftTL':(114,98),'leftTR':(226,93),'leftBL':(112,314),'leftBR':None,'rightTL':(386,72),'rightTR':(500,64),'rightBL':None,'rightBR':(519,282)},
'west15-upper':{'leftTL':(87,99),'leftTR':(138,86),'leftBL':(84,275),'leftBR':None,'rightTL':(221,64),'rightTR':(282,46),'rightBL':None,'rightBR':(281,238)},
'east15-upper':{'leftTL':(58,79),'leftTR':None,'leftBL':(57,320),'leftBR':(114,320),'rightTL':None,'rightTR':(247,123),'rightBL':None,'rightBR':(254,331)},
'center20-upper':{'leftTL':(102,144),'leftTR':(235,124),'leftBL':(91,386),'leftBR':(233,378),'rightTL':(433,84),'rightTR':(585,51),'rightBL':(453,334),'rightBR':(623,315)},
'center15':{'gatewayTL':(131,62),'gatewayTR':(351,64),'gatewayBL':(123,277),'gatewayBR':(357,261)},
'west15':{'gatewayTL':(46,72),'gatewayTR':(111,66),'gatewayBL':(54,164),'gatewayBR':(115,179)},
'east15':{'gatewayTL':(30,56),'gatewayTR':(70,61),'gatewayBL':None,'gatewayBR':None}}
obs={k:{name:(uv[0]/1.22+rect[k][0],uv[1]/1.22+rect[k][1])for name,uv in terms.items()if uv is not None}for k,terms in reads.items()}
# q = horizontal datum translation; bearing; 4 station yaw/pitch/roll sets;
# symmetric street opening from wall origin, 2 upper window rectangles.
def point(q,name):
 i=15
 if name.startswith('gateway'):
  return [(-1 if name[-1]=='L' else 1)*q[i]/2,0,q[i+1] if name[-2]=='T' else 0.]
 slot=i+2+(4 if name.startswith('right') else 0)
 return [q[slot+(name[-1]=='R')],0,q[slot+2+(name[-2]=='B')]]
def errors(q,printit=False):
 def m(k):
  i=F.index(station(k)); return pose(k,q[:2]-q[25+2*i:27+2*i],q[2],q[3+3*i:6+3*i])
 ms={k:m(k) for k in obs}
 r=[]
 for k,vals in obs.items():
  for name,uv in vals.items():
   p=pix(point(q,name),ms[k]);err=p-uv
   sig=(2.8 if k in ('center15-upper','west15-upper','center20-upper') else 4.5 if 'upper' in k else 3.4)
   r.extend(err/sig)
   if printit:print(k,name,tuple(np.round(err,1)))
 for k,pair in {'center15':[277.5,473],'west15':[397.5,459],'east15':[393,430.5],'center20':[297.5,619]}.items():
  cam=m(k)
  for side,u in zip([-1,1],pair):r.append((pix([side*q[15]*.5,0,2.32],cam)[0]-u)/4.5)
 r.append((q[15]-3.366)/.20)
 r.extend(q[25:]/.72)
 # Independent camera-station triangulation of the two portal edges at eye level.
 r.extend((q[:2]-[2.24,.081])/1.2)
 r.extend(np.array(q[:2])/2.0);r.append((q[2]-244.75)/2.5)
 for i in range(4):r.extend(q[3+i*3:6+i*3]/np.array([1.2,1.,1.] if i<3 else [5.,4.,2.]))
 return np.array(r)
q0=np.r_[0,0,247,[0.]*12,[3.6,3.3,-1.6,-.6,6.75,4.6,.6,1.65,6.75,4.6],[0.]*8]
r=least_squares(errors,q0,loss='soft_l1',max_nfev=500);q=r.x

matrices = {}
for k in camnames:
 i=F.index(station(k))
 matrices[k]=pose(k,q[:2]-q[25+2*i:27+2*i],q[2],q[3+3*i:6+3*i])
manual17={"leftTL":[664,263],"leftTR":[730,245],"leftBL":[670,445],"leftBR":[743,424]}
def latererr(a):
 m=pose('center17-upper',q[:2]-a[:2],q[2],a[2:])
 resid=[]
 for name,uv in manual17.items():
  resid.extend((pix(point(q,name),m)-uv)/3.2)
 return np.r_[resid,a/np.array([1.,1.,4.,6.,2.])]
a=least_squares(latererr,np.zeros(5),loss='soft_l1').x
for k in ['center17-upper','center17']:
 matrices[k]=pose(k,q[:2]-a[:2],q[2],a[2:])
errs=[]
for k,terms in obs.items():
 for name,uv in terms.items():
  predicted=pix(point(q,name),matrices[k])
  errs.append(dict(camera=k,point=name,observed=uv,projected=predicted.round(3).tolist(),residual_px=float(np.linalg.norm(predicted-uv))))
out={'coordinates':'X along the north street frontage toward the right (southwest); Y into the passage, Z up. Origin at the centre of the outer opening at paving level. The camera estimates are local to the doorway and the upper windows.',
     'approximate_metric':True,'gis_origin_WGS84':[lon,lat],'fitted_origin_east_north_m':q[:2].tolist(),'x_bearing_deg':float(q[2]),'main_opening_width_m':float(q[15]),'outer_front_opening_head_m':float(q[16]),
     'observed_windows':{name:point(q,name) for name in obs['center20-upper']},'stations':{k:{'projection':mat.tolist(),'date':sources[k]['station']['date'],'image_size':[sources[k]['width'],sources[k]['height']]} for k,mat in matrices.items()},
     'point_measurements':errs,'parameters':q.tolist(),'late_2017':{'parameters':a.tolist(),'window_edges':manual17,'scope':'Registration relative to the left opening. Absolute camera still approximate.'},
     'uncertainties':'3.35 ±0.35 m independent entrance width. The most oblique sunward station has tree and flare occlusions. Camera/height results are photogrammetric estimates, not survey measurements.'}
(w/'yongjia-street-cameras.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
