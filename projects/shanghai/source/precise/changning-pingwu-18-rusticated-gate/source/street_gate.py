"""Profiled stone piers and cambered iron street gate at 18 Pingwu Road."""
from pathlib import Path
from math import cos,sin,pi,sqrt
import numpy as np
from PIL import Image
from shapely.geometry import LineString,Point,Polygon,box
HERE=Path(__file__).resolve().parent
LIME='Pale streaked stone';JOINT='Recessed dark courses';TOP='Pale weathered capital';EDGE='Worn edge moulding';FOOT='Discoloured lower stone';IRON='Near-black painted wrought iron';IRON_EDGE='Worn iron edge';RED='Russet garden wall';MORTAR='Garden wall mortar';STONE_CAP='Dark brown wall cap';PLAQUE='Green enamel number plate';PALE='Light enamel figures'
PALETTE={name:dict(color=c,roughness=r) for name,c,r in [(LIME,[.99,.99,.99],.94),(JOINT,[.15,.144,.125],.93),(TOP,[.66,.63,.55],.96),(EDGE,[.76,.72,.63],.96),(FOOT,[.445,.432,.394],.97),(IRON,[.065,.070,.064],.64),(IRON_EDGE,[.112,.109,.088],.69),(RED,[.43,.239,.146],.93),(MORTAR,[.39,.31,.245],.97),(STONE_CAP,[.36,.275,.207],.96),(PLAQUE,[.056,.228,.168],.56),(PALE,[.88,.88,.73],.70)]}
ID='changning-pingwu-18-rusticated-gate'
CENTRES=(-.786,.786)
WIDTH=.568;DEPTH=.605
# Major control elevations, measured as proportions of the street photograph.
BOUNDARIES=(.025,.322,.598,.837,.926,1.160,1.248,1.471,1.550,1.794,1.881,2.195)
HALF_OPEN=.493
SPRING=1.867; RISE=.163
BARS=[-.449+i*.07485 for i in range(13)]

def texture():
 p=HERE/'weathered-stone.png'
 if not p.is_file():
  rng=np.random.default_rng(471);y,x=np.mgrid[:348,:224]
  cloud=np.asarray(Image.fromarray(rng.integers(0,255,(22,14),dtype=np.uint8)).resize((224,348),Image.Resampling.BICUBIC))/255
  tide=np.maximum(0,1-y/67)*2.6
  tone=16*(cloud-.5)+5*np.cos(x*.047+y*.010)+rng.normal(0,3.8,x.shape)-tide
  base=np.array([191,183,157])[None,None,:]+tone[:,:,None];pits=rng.random(x.shape)<.012;base[pits]-=rng.uniform(7,29,(pits.sum(),1))
  Image.fromarray(np.uint8(np.clip(base,0,255))).quantize(96).save(p)
 PALETTE[LIME]['texture']=str(p)

def decorate_uv(b):
 p=b.parts[-1];p['texcoords']=[[(.61*x+.18*y)% .89+.03,1-(z/3.13)] for x,y,z in p['vertices']]

def outline(b,x,profile,mat,label,facets=1):
 """Loft successive rounded rectangles. Profile rows contain height, width and depth."""
 vertices=[];faces=[]
 for z,width,depth in profile:
  cx=width/2;cy=depth/2;rad=min(.022,cx*.1);ring=[]
  for sx,sy,offset in [(1,1,0),(-1,1,1),(-1,-1,2),(1,-1,3)]:
   for t in range(facets+1):
    angle=(offset+t/facets)*pi/2
    ring.append((x+sx*(cx-rad)+rad*cos(angle),sy*(cy-rad)+rad*sin(angle),z))
  vertices+=ring
 n=len(ring)
 for lev in range(len(profile)-1):
  base=lev*n
  for k in range(n):faces.append((base+k,base+(k+1)%n,base+(k+1)%n+n,base+k+n))
 faces.append(list(reversed(range(n))));faces.append(list(range(len(vertices)-n,len(vertices))))
 b.add(vertices,faces,mat,label)
 if mat==LIME:decorate_uv(b)

def ol(b,x,levels,mat,name,far):
 outline(b,x,[(z,WIDTH+2*d,DEPTH+2*d) for z,d in levels],mat,name,1 if far else 3)
def simple(b,x,y,z,dx,dy,dz,mat,name):b.box((x,y,z),(dx,dy,dz),mat,label=name)
def face(b,poly,y0,y1,mat,name):b.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),mat,name)

def piers(b,far):
 for side,x in enumerate(CENTRES):
  suffix=' left' if not side else ' right'
  ol(b,x,[(.0,-.011),(.13,-.011),(2.19,-.011)],JOINT,'Deep horizontal joints'+suffix,far)
  for i,(low,high) in enumerate(zip(BOUNDARIES,BOUNDARIES[1:])):
   mat=FOOT if i<2 else LIME
   a=low+(.020 if i else -.040);b1=high-.016
   ol(b,x,[(a,-.006),(a+.013,.008),(a+.028,.016),(b1-.018,.016),(b1,.005)],mat,'Rusticated block '+str(i+1)+suffix,far)
   if i in (3,5,7,9):
    ol(b,x,[(high-.031,.014),(high-.022,.025),(high-.010,.025),(high-.006,.004)],EDGE,'Cut lip below bed joint '+str(i+1)+suffix,far)
  ol(b,x,[(2.17,.009),(2.20,.035),(2.23,.047),(2.265,.047),(2.287,.024)],EDGE,'Upper projecting abacus'+suffix,far)
  ol(b,x,[(2.282,.015),(2.325,-.029),(2.41,-.035),(2.43,.018)],LIME,'Narrow carved neck'+suffix,far)
  for k in range(9):
   dx=(k-4)*.047
   for sign in [-1,1]:
    y=sign*(DEPTH/2-.033);b.tube([(x+dx,y,2.323),(x+dx,y+sign*.005,2.404)],.009,TOP,5 if far else 8,'Neck fluting'+suffix)
  ol(b,x,[(2.424,-.020),(2.451,.038),(2.489,.053),(2.510,.035)],EDGE,'Capital ledge'+suffix,far)
  # The small silhouetted finial is only approximate. Four low corner lobes share a central block.
  ol(b,x,[(2.50,-.088),(2.54,-.104),(2.58,-.118)],TOP,'Upper weathered block'+suffix,far)
  for k in range(4):
   sx=1 if k%2 else -1;sy=1 if k<2 else -1
   b.tube([(x+sx*.192,sy*.211,2.493),(x+sx*.161,sy*.171,2.557),(x+sx*.105,sy*.104,2.604)],.053,TOP,6 if far else 12,'Capital corner relief'+suffix)
  ol(b,x,[(2.578,-.156),(2.626,-.181),(2.640,-.206)],TOP,'Central finial'+suffix,far)

def crown(x):return SPRING+RISE*(1-(x/HALF_OPEN)**2)
def gate(b,far):
 for side in (-1,1):
  left,right=(-HALF_OPEN,-.0035) if side<0 else (.0035,HALF_OPEN)
  zs=np.linspace(left,right,9 if far else 24)
  face(b,box(left,.04,right,1.536),.059,.085,IRON,'Recessed iron door leaf '+str(side))
  for x in ([left+.013,right-.013]):
   simple(b,x,.028,(crown(x)+.03)/2,.020,.057,crown(x)-.03,IRON_EDGE,'Door leaf stiles '+str(side))
  for z,d in [(0.074,.027),(.25,.018),(1.536,.028)]:
   simple(b,(left+right)/2,.007,z,right-left,.033,d,IRON_EDGE,'Iron horizontal strap '+str(side))
  for x in BARS:
   if not left<x<right:continue
   b.tube([(x,.013,.106),(x,.013,crown(x)-.004)],.0110,IRON_EDGE,5 if far else 10,'Slender vertical gate ridges '+str(side))
  curve=[(x,.015,crown(x))for x in zs]
  b.tube(curve,.018,IRON_EDGE,6 if far else 12,'Cambered upper rail '+str(side))
 # Subdued latch and a centre seam can be distinguished on the shaded leaf.
 simple(b,.032,-.014,.985,.041,.032,.115,IRON,'Iron latch plate')
 simple(b,.052,-.031,1.006,.048,.021,.014,IRON_EDGE,'Latch handle')

def street_wall(b,far):
 for side,length in [(-1,.83),(1,.28)]:
  inner=side*(abs(CENTRES[0])+WIDTH/2-.026);outer=inner+side*length;l,r=sorted((inner,outer))
  simple(b,(l+r)/2,.154,.912,r-l,.218,1.824,MORTAR,'Brick wall backing')
  # Brick ends on alternate rows turn flush into the bed joints of the posts.
  for j in range(27):
   z=j*.066+.032
   for k in range(-1,int(length/.20)+2):
    x0=max(l,l+(k-(j%2)/2)*.20+.0023);x1=min(r,l+(k+1-(j%2)/2)*.20-.0023)
    if x1-x0>.013:simple(b,(x0+x1)/2,.042,z,x1-x0,.020,.061,RED,'Orange brick course '+str(j//3))
  for k in range(int(length/.106)+1):
   x=l+k*.106+.020
   if x+.025<r:simple(b,x,.027,1.810,.051,.062,.110,STONE_CAP,'Standing brick dentils')
  simple(b,(l+r)/2,.097,1.888,length+.013,.248,.049,STONE_CAP,'Garden wall coping')

def number(b):
 x=CENTRES[0];y=-DEPTH/2-.019
 simple(b,x,y-.003,1.735,.182,.010,.106,PLAQUE,'Green street number plate')
 # The source caption gives 18; its small light digits are modelled as relief.
 for pts in [[(-.034,.021),(-.020,.033),(-.020,-.031)],[(-.033,-.031),(-.007,-.031)]]:
  b.tube([(x+dx,y-.012,1.735+dz)for dx,dz in pts],.0038,PALE,7,'Number one')
 for z,rx,rz in [(1.752,.0135,.0145),(1.715,.016,.018)]:
  pts=[(x+.019+rx*cos(t),y-.012,z+rz*sin(t)) for t in np.linspace(0,2*pi,19)]
  b.tube(pts,.0038,PALE,7,'Number eight')
 for i in (-1,1):for_screw(b,x+i*.079,y-.011,1.735)
def for_screw(b,x,y,z):simple(b,x,y,z,.005,.006,.006,IRON_EDGE,'Number plate fasteners')
def add_building(b,far=False):
 texture();piers(b,far);gate(b,far);street_wall(b,far);number(b)
