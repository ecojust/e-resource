"""Survey fragment of the roughcast tower, arch recess and two eaves at 21 Lane 1340."""
from pathlib import Path
from math import sin,cos,pi
import numpy as np
from shapely.geometry import box,Polygon
from PIL import Image
ID='jingan-xinzha-1340-no21-arched-recess'
WALL='Grey pebbledash'; SHADE='Grey reveal in shade'; INSIDE='Inner wall of recess'; CEMENT='Pale projecting eaves band'; TILE='Weathered brown roofing'; END='Ceramic barrel tile edge'
PALETTE={m:dict(color=c,roughness=.93)for m,c in [(WALL,[1,1,1]),(SHADE,[.42,.43,.397]),(INSIDE,[.361,.367,.341]),(CEMENT,[.77,.768,.712]),(TILE,[.278,.212,.161]),(END,[.363,.28,.214])]}
def texture():
 p=Path(__file__).with_name('grey-pebbledash.png')
 if not p.exists():
  rng=np.random.default_rng(587);a=rng.normal(0,9,(400,480));grit=rng.random(a.shape)
  a[grit<.072]-=17;a[grit>.92]+=13
  Image.fromarray(np.clip(np.array([166,168,156])+a[:,:,None],0,255).astype('u1')).quantize(99).save(p)
 PALETTE[WALL]['texture']=str(p)
def add_building(b,far=False):
 texture();sub=14 if far else 34
 def front(x,z,d):return x,-d,z
 def wall(shape,d0,d1,m,label):b.prism(shape,d0,d1,front,m,label)
 def rectangle(x0,x1,z0,z1,d0,d1,m,label):wall(box(x0,z0,x1,z1),d0,d1,m,label)
 def arch(x,rad,start,bottom):
  return Polygon([(x-rad,bottom),(x+rad,bottom)]+[(x+rad*cos(a),start+rad*sin(a))for a in np.linspace(0,pi,sub+1)])
 hole=arch(.10,.336,3.19,.65)
 wall(box(-1.42,0,.77,4.59).difference(hole),-.51,.08,WALL,'Roughcast face of narrow round-head opening')
 wall(hole,-.56,-.54,INSIDE,'Recess back, with its lower part screened by the tree in the source')
 rectangle(.77,1.10,0,5.68,-.22,-.02,WALL,'Narrow vertical return beside recessed bay')
 # The upper roof sits behind and above the eaves of the pierced wall.
 rectangle(-1.62,.77,4.48,5.53,-.86,-.36,WALL,'Raised rear bay behind the lower eaves')
 def roof(x0,x1,level,d,unit,row):
  rectangle(x0,x1,level-.09,level,-d,-d+.23,CEMENT,'Pale course beneath roof '+row)
  rectangle(x0-.055,x1+.055,level,level+.06,-d-.09,-d+.25,TILE,'Bedding and lower edge of roof '+row)
  for idx,x in enumerate(np.arange(x0+.076,x1-.008,unit)):
   # Pantile curves run from front lip up the pitched strip.
   radius=unit*.49;n=6 if far else 15;v=[]
   for depth,dz in [(-d+.29,0),(-d+.03,.162),(-d-.17,.28)]:
    for angle in np.linspace(0,pi,n+1):
     v.append((x+radius*cos(angle),-depth,level+.038+dz+.058*sin(angle)))
   faces=[]
   for j in (0,1):
    for i in range(n):a=j*(n+1)+i;faces.append((a,a+n+1,a+n+2,a+1))
   b.add(v,faces,TILE if idx%3 else END,'Individual curved clay roofing course')
 roof(-1.43,.77,4.58,.08,.145,'front')
 roof(-1.64,.78,5.59,.35,.149,'rear')
 # Repeated rounded voids under the upper slope allow the dark pebbledash behind them to show.
 band=box(-1.63,5.22,.772,5.564)
 for x in np.arange(-1.513,.755,.207):
  band=band.difference(arch(x,.079,5.294,5.19))
 wall(band,-.329,-.182,CEMENT,'Pale upper cornice with repeated shallow scallops')
 for part in b.parts:
  if part['material']==WALL:part['texcoords']=[[(x+.75*y+2)/4,z/6]for x,y,z in part['vertices']]
