"""Original intersected hip/gable roof envelope. Profiles are photo-guided estimates."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
from shapely.ops import unary_union

def pieces(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [p for x in getattr(g,'geoms',()) for p in pieces(x)]
def clip(poly,a,b,c):
 pts=list(poly.exterior.coords)[:-1];out=[]
 for p,q in zip(pts,pts[1:]+pts[:1]):
  d=a*p[0]+b*p[1]+c;e=a*q[0]+b*q[1]+c
  if d<=1e-10:out.append(p)
  if d*e<0:
   t=d/(d-e);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 return Polygon(out) if len(out)>2 else Polygon()
class Roof:
 def __init__(self):
  a=(11.7-7.85)/9.3;b=(11.7-7.85)/4.7;c=7.85+b*8.7
  g=(10.8-7.85)/4.5;d=(11.35-9.9)/2.3
  self.volumes=[{'id':'main-hip','bounds':(-9.3,-8.7,9.3,8.7),'planes':[(a,0,11.7),(-a,0,11.7),(0,b,c),(0,-b,c)]},
   {'id':'east-front-gable','bounds':(.3,-8.7,9.3,-3.6),'planes':[(g,0,10.8-g*4.8),(-g,0,10.8+g*4.8),(0,-.9,10.8-.9*5.5)]},
   {'id':'front-dormer','bounds':(-3.,-5.7,1.6,-3.8),'planes':[(d,0,11.35+d*.7),(-d,0,11.35-d*.7)]}]
  self.patches=[]
  for v in self.volumes:
   for i,plane in enumerate(v['planes']):
    p=box(*v['bounds'])
    for other in v['planes']:
     p=clip(p,*(np.array(plane)-other)) if not p.is_empty else p
    if p.is_empty:continue
    for other in self.volumes:
     if other is v:continue
     covered=box(*other['bounds'])
     for op in other['planes']:
      covered=clip(covered,*(np.array(plane)-op)) if not covered.is_empty else covered
     p=p.difference(covered)
    for j,poly in enumerate(pieces(p)):
     poly=poly.simplify(1e-7,preserve_topology=True)
     if poly.area>1e-8:self.patches.append({'id':f"{v['id']}/{i}/{j}",'plane':plane,'polygon':orient(poly,sign=1)})
  union=unary_union([p['polygon'] for p in self.patches]);domain=box(*self.volumes[0]['bounds'])
  assert union.symmetric_difference(domain).area<1e-7
  assert abs(sum(p['polygon'].area for p in self.patches)-domain.area)<1e-7
 def volume_height(self,v,x,y):return min(a*x+b*y+c for a,b,c in v['planes'])
 def height(self,x,y):
  return max(self.volume_height(v,x,y) for v in self.volumes if v['bounds'][0]-1e-8<=x<=v['bounds'][2]+1e-8 and v['bounds'][1]-1e-8<=y<=v['bounds'][3]+1e-8)
 def profile(self,a,b):
  # Include all exact plane intersection and footprint events along this edge.
  a=np.asarray(a);b=np.asarray(b);delta=b-a;events=[0.,1.];planes=[p for v in self.volumes for p in v['planes']]
  for p in planes:
   for q in planes:
    diff=np.array(p)-q;den=np.dot(diff[:2],delta)
    if abs(den)>1e-10:
     t=-(np.dot(diff[:2],a)+diff[2])/den
     if 0<t<1:events.append(t)
  for v in self.volumes:
   for axis in [0,1]:
    if abs(delta[axis])>1e-10:
     for val in [v['bounds'][axis],v['bounds'][axis+2]]:
      t=(val-a[axis])/delta[axis]
      if 0<t<1:events.append(t)
  return [(float(t),self.height(*(a+t*delta))-.08) for t in sorted(set(round(t,10) for t in events))]
 def add(self,builder,lod=False):
  report=[]
  for patch in self.patches:
   a,b,c=patch['plane'];poly=patch['polygon'];pid=patch['id']
   # Closed thin slabs; shared vertical seam caps lie inside the roof thickness.
   mapper=lambda u,v,d:(u,v,a*u+b*v+c+d)
   builder.prism(poly,-.08,0,mapper,'roof underlay','roof-shell/'+pid)
   n=np.array([-a,-b,1.]);n/=np.linalg.norm(n)
   u=np.array([b,-a,0.]);u/=np.linalg.norm(u);v=np.cross(n,u);origin=np.array([0.,0.,c])
   coords=[np.array([x,y,a*x+b*y+c]) for x,y in list(poly.exterior.coords)[:-1]]
   uv=Polygon([(np.dot(p-origin,u),np.dot(p-origin,v)) for p in coords]);count=0
   if not lod:
    x0,y0,x1,y1=uv.bounds
    for row in range(math.floor(y0/.30)-1,math.ceil(y1/.30)+1):
     for col in range(math.floor(x0/.24)-1,math.ceil(x1/.24)+1):
      for tile in pieces(uv.intersection(box(col*.24+.004,row*.30,(col+1)*.24-.004,row*.30+.34))):
       if tile.area<.0001:continue
       def tilemap(x,y,d):return origin+u*x+v*y+n*(.008+.05*(y-row*.30)+d)
       builder.prism(tile,0,.018,tilemap,f'clay tile {(row*13+col*7)%4}','tiles/'+pid)
       count+=1
   # Eave fascia only on true outer plan perimeter; no artificial patch edges.
   points=list(poly.exterior.coords)
   for p,q in zip(points,points[1:]):
    if np.linalg.norm(np.array(p)-q)>1e-6 and any(abs(p[axis]-value)<1e-7 and abs(q[axis]-value)<1e-7 for axis,value in [(0,-9.3),(0,9.3),(1,-8.7),(1,8.7)]):
     builder.tube([(p[0],p[1],a*p[0]+b*p[1]+c-.04),(q[0],q[1],a*q[0]+b*q[1]+c-.04)],.085,'pale trim' if abs(p[1]+8.7)<1e-7 and abs(q[1]+8.7)<1e-7 and (p[0]+q[0])/2>.3 else 'red wood',6,'eave fascia')
   report.append({'id':pid,'plane':patch['plane'],'plan':list(poly.exterior.coords),'tiles':count})
  # Ridge caps follow observed principal ridges; secondary intersection trim omitted.
  builder.tube([(0,-4,11.76),(0,4,11.76)],.09,'clay tile 1',8,'main ridge cap')
  builder.tube([(4.8,-8.7,10.86),(4.8,-5.5,10.86)],.08,'clay tile 1',8,'front ridge cap')
  return report
