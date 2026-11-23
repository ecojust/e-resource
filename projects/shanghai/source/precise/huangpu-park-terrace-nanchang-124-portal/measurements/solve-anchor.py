import os
from pathlib import Path
import json, math
from shapely.geometry import Point, Polygon
from shapely.ops import transform
from statistics import mean
w=Path(__file__).resolve().parent
read=lambda f:json.loads(f.read_bytes())
lo=121.46370; la=31.22095
sx=111195.08*math.cos(math.radians(la)); sy=111195.08
def xy(lon,lat):return (lon-lo)*sx,(lat-la)*sy
def geo(x,y):return lo+x/sx,la+y/sy
def shot(name,x,y):
 r=read(w/(name+'.json'));f=r['width']/(2*math.tan(math.radians(r['hfov']/2)))
 u=(x-r['width']/2)/f;v=(r['height']/2-y)/f
 pitch=math.radians(r['pitch']);q=math.cos(pitch)-v*math.sin(pitch)
 a=math.radians(r['az'])+math.atan2(u,q);e=math.atan2(math.sin(pitch)+v*math.cos(pitch),math.hypot(u,q))
 return xy(*r['station']['position']), (math.sin(a),math.cos(a)), math.tan(e),r['station']['height']
def tri(a,b):
 p,d,t,h=shot(*a);q,v,s,k=shot(*b)
 det=d[0]*v[1]-d[1]*v[0]
 dx=q[0]-p[0];dy=q[1]-p[1];l=(dx*v[1]-dy*v[0])/det;m=(dx*d[1]-dy*d[0])/det
 X,Y=p[0]+l*d[0],p[1]+l*d[1]
 return dict(lnglat=geo(X,Y),z_each=[h+l*t,k+m*s],dist=[l,m],angle=math.degrees(math.acos(d[0]*v[0]+d[1]*v[1])))
if __name__=='__main__':
 root=Path(os.environ['SHANGHAI_SURVEY_ROOT'])
 for a,b in [
 (('portal-10-297',315,255),('portal-west124',440,237)),
 (('portal-10-297',318,266),('portal-west124',443,246)),
 (('portal-10-297',280,294),('portal-west124',409,271)),
 (('portal-10-297',348,289),('portal-west124',478,265)),
 ]:
  obj=tri(a,b);print(a,b,obj);pt=Point(xy(*obj['lnglat'])); near=[]
  for r in read(root/'source-block.json')['rows']:
   poly=Polygon([xy(*pt)for pt in r['geometry']['coordinates'][0]]);near.append((round(poly.distance(pt),2),r['localId'],round(poly.area,2),r['height']))
  print(sorted(near)[:6])
