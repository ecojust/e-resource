"""A single window from the photographed frontage of 85 Hong Kong Road, Shanghai."""
from pathlib import Path
from math import sin,cos,pi
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import box,Polygon
ID='huangpu-hongkong-85-console-window'
BRICK='Salmon facing brick';STONE='Grey stone surround';EDGE='Projecting moulding';CUT='Carved corbel';SHADE='Recessed stone';GLASS='Blue grey daylight glass';IRON='Dark painted steel';INNER='Dim interior'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(BRICK,[1,1,1],.94),(STONE,[.661,.651,.606],.93),(EDGE,[.709,.693,.641],.87),(CUT,[.625,.609,.548],.90),(SHADE,[.487,.482,.45],.93),(GLASS,[.21,.31,.34],.34),(IRON,[.125,.142,.137],.68),(INNER,[.128,.153,.151],.89)]}
def texture():
 p=Path(__file__).with_name('salmon-brick.png')
 if not p.is_file():
  rg=np.random.default_rng(571);tile=np.zeros((480,640,3),dtype=float);tile[:]=[173,146,130]
  h,w=24,80
  for row in range(20):
   for col in range(-1,9):
    x=col*w+row%2*(w//2); y=row*h
    l,r=max(0,x+1),min(640,x+w-1)
    if r<=l:continue
    tile[y+1:y+h-1,l:r]=np.array([164,108,91])+rg.normal(0,6,(1,1,1))+rg.normal(0,1.9,(h-2,r-l,1))
  Image.fromarray(tile.clip(0,255).astype('u1')).quantize(100).save(p)
 PALETTE[BRICK]['texture']=str(p)
def front(x,z,d):return x,-d,z
def add_building(b,far=False):
 texture()
 def part(x0,x1,z0,z1,d0,d1,m,group):
  b.prism(box(x0,z0,x1,z1),d0,d1,front,m,group)
 clear=box(-.718,.24,.718,3.62);b.prism(box(-1.66,0,1.66,4.82).difference(clear),-.44,0,front,BRICK,'Running-bond wall with pierced opening')
 trim=box(-.842,.19,.842,3.755).difference(box(-.695,.241,.695,3.59))
 b.prism(trim,-.025,.075,front,STONE,'Flat continuous stone sides and top')
 # A shallow splay separates the pale face from the darker fixed steel frame.
 for side in (-1,1):
  v=[front(x,z,d)for x,d in[(.698*side,.072),(.629*side,-.186)]for z in (.240,3.592)]
  b.add(v,[(1,3,2,0) if side>0 else (0,2,3,1)],SHADE,'Inward sloping window reveal')
 part(-.64,.64,.241,3.603,-.264,-.259,INNER,'Interior plane behind open and closed leaves')
 part(-.633,.633,2.127,3.587,-.196,-.19,GLASS,'Fixed top pair of panes')
 part(.016,.633,.243,2.12,-.196,-.19,GLASS,'Stationary lower right sash glazing')
 for x,z0,z1 in [(-.626,.25,3.58),(.626,.25,3.58),(0,2.1,3.58),(.015,.25,2.12)]:
  part(x-.014,x+.014,z0,z1,-.216,-.135,IRON,'Thin stationary vertical window rails')
 for z in (.26,2.114,2.84,3.575):
  part(-.639,.639,z-.013,z+.013,-.21,-.127,IRON,'Straight stationary horizontal transom')
 for z in (.815,1.455):
  part(.015,.638,z-.012,z+.012,-.203,-.145,IRON,'Divisions in the stationary lower sash')
 # The front left edge stands out into the street in the 2017 image.
 hinge=(-.625,.147);ang=43*pi/180
 def work(x,z,d):
  return hinge[0]+x*cos(ang)-d*sin(ang),hinge[1]-x*sin(ang)-d*cos(ang),z
 def sash(x0,x1,z0,z1,d0,d1,mat,tag):
  b.prism(box(x0,z0,x1,z1),d0,d1,work,mat,tag)
 sash(.012,.642,.262,2.104,0,.01,GLASS,'Open left leaf glazing')
 for x in (0,.650):sash(x-.014,x+.014,.247,2.12,-.013,.039,IRON,'Outer stile on opened leaf')
 for z in (.26,.815,1.455,2.11):sash(-.01,.666,z-.013,z+.013,-.013,.037,IRON,'Bars crossing opened leaf')
 for x in (-.895,.895):
  part(x-.135,x+.135,3.47,3.52,0,.142,STONE,'Small corbel foot')
  # Cubic profile of corbel, projecting farther at its rolled head.
  profile=[(0,3.51),(.110,3.51),(.151,3.58),(.178,3.70),(.224,3.79),(.286,3.84),(.327,3.93),(.345,4.06),(.260,4.15),(.015,4.16)]
  b.prism(Polygon(profile),-.112,.112,lambda d,z,u:(x-u,-d,z),CUT,'Broken curved profile carved into each corbel')
  for u in (-.067,0,.067):
   pts=[(x+u,-d-.006,z)for d,z in profile[1:7]]
   b.tube(pts,.012,EDGE,sides=6 if far else 9,label='Three narrow ribs returning under the stone bracket')
  for hand in (-1,1):
   # The spiral is on the visible side plate of the corbel.
   ts=np.linspace(0,2*pi*1.06,14 if far else 33)
   pts=[(x+hand*.114,-(.244+(.015+.073*t/ts[-1])*cos(t)),4.015+(.015+.073*t/ts[-1])*sin(t))for t in ts]
   b.tube(pts,.017,EDGE,sides=6 if far else 10,label='Carved spiral on cheek of bracket')
 for z,height,half,depth,m in[(3.61,.09,.837,.112,EDGE),(3.708,.09,.872,.131,STONE),(3.84,.118,.895,.132,STONE),(4.15,.085,1.043,.325,STONE),(4.235,.061,1.09,.367,SHADE),(4.296,.085,1.125,.393,EDGE),(4.381,.065,1.163,.412,EDGE),(4.446,.046,1.15,.382,STONE)]:
  part(-half,half,z,z+height,-.02,depth,m,'Layered cornice and flat square-edge drip')
 for a in b.parts:
  if a['material']==BRICK:a['texcoords']=[[(x+1.66)/2.1,z/1.53]for x,y,z in a['vertices']]
