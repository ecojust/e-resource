"""Visible outer shell of Sichuan Road Bridge, looking west from the river.

The longitudinal x coordinate increases north. Heights are relative to the
photographic waterline and are only proportional estimates. The two terminal
edges follow the skew in the surveyed plan rather than perpendicular cuts.
"""
from pathlib import Path
import math,sys
from shapely.geometry import Polygon
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'hongkou-general-post-office/source/common'))
from photo_architecture import Builder
PALETTE={
 'pale concrete':{'color':[.67,.64,.56],'roughness':.9},
 'pier cap':{'color':[.46,.44,.39],'roughness':.92},
 'asphalt':{'color':[.074,.072,.069],'roughness':.94},
 'pavement':{'color':[.42,.40,.35],'roughness':.89},
 'moulding':{'color':[.74,.72,.66],'roughness':.87},
 'dark metal':{'color':[.095,.08,.062],'metallic':.56,'roughness':.47},
 'lantern glass':{'color':[.64,.43,.22],'roughness':.45},
}
HALF_LENGTH=70.97/2
HALF_WIDTH=(12.8+2*2.7)/2
def pos(x,y,z):
 return (x-.26*y,y,z)
def camber(x):
 return 4.10+.68*max(0.,1-(x/HALF_LENGTH)**2)
def span_height(x):
 ax=abs(x)
 if ax<=17.29:return .77+2.99*math.sqrt(max(0,1-(ax/17.29)**2))
 if ax<19.29:return .68
 u=(ax-19.29)/(HALF_LENGTH-19.29)
 return .68+2.12*math.sqrt(max(0,1-(2*u-1)**2))
def mesh_band(b,stations,y0,y1,lower,upper,mat,label,*,top=True,bottom=True):
 v=[];faces=[]
 for x in stations:v.extend([pos(x,y0,lower(x)),pos(x,y1,lower(x)),pos(x,y1,upper(x)),pos(x,y0,upper(x))])
 for i in range(len(stations)-1):
  j=i*4
  for s in range(4):
   if (s==0 and not bottom) or (s==2 and not top):continue
   t=(s+1)%4;faces.append((j+s,j+t,j+t+4,j+s+4))
 faces.extend([(3,2,1,0),tuple(range(len(v)-4,len(v)))]);b.add(v,faces,mat,label)
def tower_shell(b,x,y,levels,mat,label):
 v=[];f=[]
 for z,hx,hy in levels:v.extend([(x-hx,y-hy,z),(x+hx,y-hy,z),(x+hx,y+hy,z),(x-hx,y+hy,z)])
 for i in range(len(levels)-1):
  j=4*i
  for s in range(4):t=(s+1)%4;f.append((j+s,j+t,j+t+4,j+s+4))
 f.extend([(3,2,1,0),tuple(range(len(v)-4,len(v)))]);b.add(v,f,mat,label)
def build_bridge(b,lod=False):
 seg=16 if lod else 48
 points={-HALF_LENGTH,HALF_LENGTH,-19.29,-17.29,17.29,19.29}
 for a,z in [(-HALF_LENGTH,-19.29),(-17.29,17.29),(19.29,HALF_LENGTH)]:
  for i in range(seg+1):points.add((a+z)/2-(z-a)/2*math.cos(math.pi*i/seg))
 stations=sorted(points)
 mesh_band(b,stations,-HALF_WIDTH,HALF_WIDTH,span_height,camber,'pale concrete','Three open river spans',top=False)
 mesh_band(b,stations,-6.4,6.4,camber,lambda x:camber(x)+.035,'asphalt','Roadway',bottom=False)
 for side,side_name in [(-1,'east'),(1,'west')]:
  curb_min,curb_max=sorted([side*6.4,side*HALF_WIDTH])
  mesh_band(b,stations,curb_min,curb_max,camber,lambda x:camber(x)+.18,'pavement',side_name+' sidewalk',bottom=False)
  y=side*(HALF_WIDTH-.19)
  mesh_band(b,stations,y-.16,y+.16,lambda x:camber(x)+.15,lambda x:camber(x)+1.05,'pale concrete',side_name+' parapet')
  mesh_band(b,stations,y-.21,y+.21,lambda x:camber(x)+1.05,lambda x:camber(x)+1.17,'moulding',side_name+' parapet cap')
  mesh_band(b,stations,y-.23,y+.23,lambda x:camber(x)+.03,lambda x:camber(x)+.15,'moulding',side_name+' lower band')
  for x in [-18.29,18.29]:
   px,py,_=pos(x,side*(HALF_WIDTH-.38),0);z=camber(x)
   tower_shell(b,px,py,[(.10,.95,.61),(.62,1.09,.74),(.81,.83,.50),(z-.15,.76,.45),(z+.18,.88,.55),(z+1.8,.65,.43),(z+2.12,.48,.35),(z+3.26,.34,.31),(z+3.40,.36,.33)],'pale concrete',side_name+' stepped pier and lamp pedestal')
   tower_shell(b,px,py,[(z+3.40,.32,.28),(z+3.57,.27,.23),(z+4.68,.22,.21)],'lantern glass',side_name+' segmented amber lantern')
   for dz in [3.42,3.81,4.18,4.53,4.68]:
    b.box((px,py,z+dz),(.57,.53,.07),'dark metal',label=side_name+' lantern band')
   for xx in [-.23,.23]:
    for yy in [-.21,.21]:
     b.tube([(px+xx,py+yy,z+3.42),(px+.9*xx,py+.9*yy,z+4.67)],.026,'dark metal',sides=4,label=side_name+' lantern frame')
   tower_shell(b,px,py,[(z+4.7,.30,.27),(z+4.85,.16,.15),(z+5.05,.028,.026)],'dark metal',side_name+' lantern finial')
  if not lod:
   for i in range(-20,21):
    x=i*1.71;y=side*(HALF_WIDTH+.012);bottom=max(span_height(x)+.12,camber(x)-.75)
    if bottom<camber(x)-.10:b.box(pos(x,y,(bottom+camber(x)-.09)/2),(.018,.024,camber(x)-.09-bottom),'pier cap',label=side_name+' fascia joints')
