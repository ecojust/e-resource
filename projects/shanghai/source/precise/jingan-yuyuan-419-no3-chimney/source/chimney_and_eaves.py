"""Tall rendered chimney interrupting the tiled street eaves of lane 419, house 3."""
from pathlib import Path
from math import pi, sin
import numpy as np
from PIL import Image
from shapely.geometry import box
ID='jingan-yuyuan-419-no3-chimney'
RENDER='Cream roughcast'; CAP='Weathered cement coping'; SHADOW='Shadow beneath eaves'
FASCIA='Dark run of fascia'; CLAY='Brown clay tile'; PALE='Sun-worn clay tile'; EDGING='Tile edge'
PALETTE={m:dict(color=c,roughness=.93) for m,c in [(RENDER,[1,1,1]),(CAP,[.57,.53,.44]),(SHADOW,[.20,.17,.13]),(FASCIA,[.184,.147,.103]),(CLAY,[.31,.18,.10]),(PALE,[.43,.27,.155]),(EDGING,[.255,.155,.087])]}
def texture():
 p=Path(__file__).with_name('cream-roughcast.png')
 if not p.is_file():
  rng=np.random.default_rng(583)
  grain=rng.normal(0,7,(260,310));flecks=rng.uniform(0,1,(260,310))<.013
  grain[flecks]-=19
  color=np.clip(np.array([219,212,186])+grain[:,:,None],0,255).astype('u1')
  Image.fromarray(color).quantize(88).save(p)
 PALETTE[RENDER]['texture']=str(p)
def roof_z(y): return 2.705+.59*(y+.39)
def add_building(b,far=False):
 texture()
 def solid(x0,x1,y0,y1,z0,z1,material,name):
  b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=name)
 # The stack rises on the wall face. Its base continues below the study.
 solid(-.575,.575,-.195,.48,0,6.42,RENDER,'Continuous render chimney breast')
 solid(-.597,.597,-.211,.501,6.42,6.464,CAP,'Fine collar at top of stack')
 solid(-.615,.615,-.233,.525,6.464,6.542,CAP,'Single lightly projecting rectangular coping')
 for x0,x1 in [(-2.36,-.575),(.575,2.36)]:
  solid(x0,x1,-.02,.75,0,2.69,RENDER,'Outer wall directly below the eaves')
  solid(x0,x1,-.32,.26,2.52,2.618,SHADOW,'Shaded soffit')
  solid(x0,x1,-.33,-.252,2.586,2.688,FASCIA,'Straight projecting dark fascia')
  # A solid pitched bedding supports overlapping, individually cupped pantiles.
  y0,y1=-.39,1.04
  profile=[(x,y,roof_z(y)+dz)for x in (x0,x1)for y,dz in [(y0,-.065),(y1,-.065),(y1,0),(y0,0)]]
  b.add(profile,[(0,3,2,1),(4,5,6,7),(0,4,7,3),(3,7,6,2),(2,6,5,1),(1,5,4,0)],EDGING,'Pitched bedding through the roof cut')
  pitch=(x1-x0)/11
  for col in range(11):
   for row in range(6):
    y=y0+row*.227
    n=6 if far else 14
    high=[(x0+pitch*(col+i/n),v,roof_z(v)+.016+dz+.045*(1-sin(pi*i/n))) for v,dz in [(y,.022),(y+.266,0)]for i in range(n+1)]
    low=[(x,y,z-.013)for x,y,z in high];v=high+low;rowlen=n+1;under=len(high)
    faces=[]
    for i in range(n):
     faces.extend([(i,i+1,rowlen+i+1,rowlen+i),(under+i,under+rowlen+i,under+rowlen+i+1,under+i+1),(i,under+i,under+i+1,i+1)])
    b.add(v,faces,PALE if (col+2*row)%7==3 else CLAY,'Overlapping clay pantile')
 for part in b.parts:
  if part['material']==RENDER:part['texcoords']=[[(x+.78*y+2.8)/5.6,z/6.75] for x,y,z in part['vertices']]
