from pathlib import Path
from math import *
import numpy as np,json
w=Path(__file__).parent
C=np.array([121.4721,31.21775]);M=np.array([111198*cos(radians(C[1])),111198.])
def ray(name,u,v):
 d=json.loads((w/(name+'.json')).read_bytes());t=radians(d['pitch']);a=radians(d['az']);f=d['width']/2/tan(radians(d['hfov']/2));x,y=(u-d['width']/2)/f,(d['height']/2-v)/f
 h=a+atan2(x,cos(t)-y*sin(t));el=atan2(sin(t)+y*cos(t),hypot(x,cos(t)-y*sin(t)));n=np.array([cos(h),-sin(h)]);pt=(d['station']['position']-C)*M
 return d,degrees(h)%360,degrees(el),n,pt
def fit(rows):
 f=[ray(*r)for r in rows];n=np.array([x[3]for x in f]);s=np.array([x[3]@x[4] for x in f]);xy=np.linalg.lstsq(n,s,rcond=None)[0];return list(C+xy/M),[(round(h,2),round(float(nn@xy-nn@p),2),round(float(np.linalg.norm(p-xy)),2),round(tan(radians(el))*np.linalg.norm(p-xy)+d['station']['height'],2))for d,h,el,nn,p in f]
if __name__=='__main__':
 rows=[('front-2015',185,326),('front-2020',162,383),('south-2020',362,362),('north-2020',211,367)];print(fit(rows));print(fit(rows[1:]));print(fit(rows[2:]))
