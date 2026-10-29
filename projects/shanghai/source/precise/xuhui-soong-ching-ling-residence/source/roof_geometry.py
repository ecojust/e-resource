"""Estimated curved hip roof and three barrel dormers, with actual cutouts.

The photo supports the arrangement, not surveyed curvature or tile dimensions.
The shell is split into narrow strips; dormer holes are clipped out of it and
out of its tiles, so the lower roof never passes through the dormer glazing.
"""
import math
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

class Roof:
 def __init__(self,lod=False):
  self.lod=lod;self.w=11.6;self.d=7.6;self.eave=7.7;self.rise=3.3
  self.front=-4.0;self.radius=.85;self.base=self.height(0,self.front)+.03
  self.centres=[-3.5,0,3.5];self.holes=[];self.samples=[]
  angles=np.linspace(-math.pi/2,math.pi/2,17 if lod else 41)
  for cx in self.centres:
   profile=[]
   for t in angles:
    x=cx+self.radius*math.sin(t);z=self.base+self.radius*math.cos(t)
    lo=0.;hi=1.
    for _ in range(50):
     mid=(lo+hi)/2
     if self.eave+self.rise*self.curve(mid)<z:lo=mid
     else:hi=mid
    y=self.d*((lo+hi)/2-1);profile.append((x,y,z))
   self.samples.append(profile)
   self.holes.append(Polygon([(cx-self.radius,self.front),(cx+self.radius,self.front)]+[(x,y) for x,y,z in reversed(profile)]))
  self.cutouts=unary_union(self.holes)
  w=self.w;d=self.d
  self.patches=[('south',Polygon([(-w,-d),(w,-d),(w-d,0),(-w+d,0)]),1),('north',Polygon([(-w,d),(-w+d,0),(w-d,0),(w,d)]),1),('east',Polygon([(w,-d),(w,d),(w-d,0)]),0),('west',Polygon([(-w,d),(-w,-d),(-w+d,0)]),0)]
 @staticmethod
 def curve(t):return t+.12*math.sin(math.pi*t)
 def height(self,x,y):
  t=max(0,min(1,(self.w-abs(x))/self.d,(self.d-abs(y))/self.d))
  return self.eave+self.rise*self.curve(t)
 def add(self,b):
  tile_count=0;shell_area=0
  for name,poly,axis in self.patches:
   poly=poly.difference(self.cutouts);shell_area+=poly.area
   x0,y0,x1,y1=poly.bounds;v0,v1=(y0,y1) if axis==1 else (x0,x1)
   for lo,hi in zip(np.linspace(v0,v1,15 if self.lod else 41)[:-1],np.linspace(v0,v1,15 if self.lod else 41)[1:]):
    band=box(-20,lo,20,hi) if axis==1 else box(lo,-20,hi,20)
    b.prism(poly.intersection(band),-.08,0,lambda x,y,d:(x,y,self.height(x,y)+d),'roof underlay','curved roof shell/'+name)
   if self.lod:continue
   # Three transverse subdivisions give each clay tile a real barrel profile.
   across=.24;along=.34
   u0,u1=(x0,x1) if axis==1 else (y0,y1)
   for col in range(math.floor(u0/across),math.ceil(u1/across)):
    for row in range(math.floor(v0/along),math.ceil(v1/along)):
     for segment in range(3):
      ua=col*across+.004+(across-.008)*segment/3;ub=col*across+.004+(across-.008)*(segment+1)/3
      va=row*along;vb=(row+1)*along-.004
      cell=box(ua,va,ub,vb) if axis==1 else box(va,ua,vb,ub)
      piece=poly.intersection(cell)
      if piece.is_empty or piece.area<1e-7:continue
      def mapper(x,y,d):
       u=x if axis==1 else y
       return (x,y,self.height(x,y)+.028+.045*math.sin(math.pi*(u-col*across)/across)+d)
      b.prism(piece,0,.014,mapper,f'tile{(col*7+row*11)%4}','barrel tiles/'+name);tile_count+=1
  for i,profile in enumerate(self.samples):
   b.tube([(x,y,z+.035) for x,y,z in profile],.065,'dormer red',8,'dormer roof flashing '+str(i))
   for a,c in zip(profile,profile[1:]):
    x,y,z=a;xx,yy,zz=c
    verts=[(x,self.front,z),(xx,self.front,zz),(xx,yy,zz),(x,y,z),(x,self.front,z-.035),(xx,self.front,zz-.035),(xx,yy,zz-.035),(x,y,z-.035)]
    b.add(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'dormer red','curved dormer shell '+str(i))
  # Ridge and hips trace the same curved envelope; no invented straight gables.
  b.tube([(-4,0,11.08),(4,0,11.08)],.09,'ridge red',8,'main ridge cap')
  for sx in [-1,1]:
   for sy in [-1,1]:
    pts=[]
    for t in np.linspace(0,1,20):
     x=sx*(11.6-7.6*t);y=sy*(7.6-7.6*t);pts.append((x,y,self.height(x,y)+.07))
    b.tube(pts,.07,'ridge red',8,'curved hip cap')
  for y in [-7.6,7.6]:b.tube([(-11.6,y,7.68),(11.6,y,7.68)],.055,'metal',8,'rain gutter')
  for x in [-11.6,11.6]:b.tube([(x,-7.6,7.68),(x,7.6,7.68)],.055,'metal',8,'side gutter')
  return {'main_shell_plan_area_m2':shell_area,'dormer_cutout_area_m2':self.cutouts.area,'whole_roof_plan_area_m2':23.2*15.2,'tile_segments':tile_count,'dormer_front_y':self.front,'dormer_base_z':self.base,'dormer_centres':self.centres,'all_dimensions_estimated':True}
