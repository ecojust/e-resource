"""Grey-brick end wall of the closest Yuyuan New Village house in the district archive photograph."""
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from math import sqrt
import numpy as np
BRICK='Weathered grey Shanghai brick';TRIM='Pale weathered fascia';SOFFIT='Green grey eaves underside';RED='Burnt red band bricks';JOINT='Dark red lime beds';GLASS='Dark green window glass';WOOD='Painted deep green joinery';SILL='White stone sill';TILES=['Muted terracotta pantile','Worn umber pantile','Faded clay pantile'];MORTAR='Dark tile bedding'
def linear(rgb):return [float(v/255.)**2.2 for v in rgb]
palette={BRICK:[255,255,255],TRIM:[212,207,190],SOFFIT:[87,110,91],RED:[135,75,53],JOINT:[95,76,57],GLASS:[60,79,76],WOOD:[78,87,72],SILL:[198,195,177],MORTAR:[94,70,58],TILES[0]:[144,88,65],TILES[1]:[123,77,59],TILES[2]:[158,103,75]}
PALETTE={key:dict(color=linear(v),roughness=.87)for key,v in palette.items()};PALETTE[BRICK]['texture']=str(Path(__file__).with_name('grey-brick.png'))
PROFILE=[(-3.2,2.40),(-2.78,2.50),(-2.25,2.69),(-1.70,3.14),(0,5.12),(2.65,2.65),(3.20,2.42)]
WINDOWS=[(-2.17,.56,1.62,.35),(-.77,.56,1.62,.35),(.77,.56,1.62,.35),(2.22,.56,1.62,.35),(-.60,2.66,3.50,.36),(.60,2.66,3.50,.36)]
def height(x):
 for (a,z),(b,w)in zip(PROFILE,PROFILE[1:]):
  if a-.000001<=x<=b+.000001:return z+(w-z)*(x-a)/(b-a)
 raise ValueError(x)
def solid(b,s,front,back,material,group):
 for part in getattr(s,'geoms',[s]):
  if part.geom_type=='Polygon' and part.area>.00001:b.prism(part,-back,-front,lambda x,z,k:(x,-k,z),material,label=group)
def cuboid(b,x1,x2,y1,y2,z1,z2,mat,group):
 b.box(((x1+x2)/2,(y1+y2)/2,(z1+z2)/2),(x2-x1,y2-y1,z2-z1),mat,label=group)
def brick_uv(b):
 for part in b.parts:
  if part['material']!=BRICK:continue
  vs=np.array(part['vertices']);verts=[];faces=[];uv=[]
  for tri in part['triangles']:
   pts=vs[np.asarray(tri)];ofs=len(verts);verts.extend(pts.tolist());faces.append([ofs,ofs+1,ofs+2]);axis=np.argmax(np.abs(np.cross(pts[1]-pts[0],pts[2]-pts[0])))
   for x,y,z in pts:uv.append([((x+3.2)/6.4 if axis!=0 else y/.40),1-z/5.16])
  part.update(vertices=verts,triangles=faces,texcoords=uv)
def model(b,lod=False):
 outline=Polygon([(-3.2,0),(3.2,0),*reversed(PROFILE)]);holes=unary_union([box(x-w/2,z0,x+w/2,z1)for x,z0,z1,w in WINDOWS])
 solid(b,outline.difference(holes),0,.35,BRICK,'Grey brick gable between six reveals')
 for i,(cx,z0,z1,span)in enumerate(WINDOWS):
  side='Attic' if i>3 else 'Lower';left=cx-span/2;right=cx+span/2
  cuboid(b,left,right,.133,.150,z0,z1,GLASS,side+' deeply set glazing')
  for x in (left+.016,right-.016):cuboid(b,x-.016,x+.016,.080,.137,z0,z1,WOOD,side+' outer jambs')
  for z in (z0+.021,z0+(z1-z0)*.66,z1-.021):cuboid(b,left,right,.070,.138,z-.021,z+.021,WOOD,side+' transoms')
  cuboid(b,cx-.012,cx+.012,.09,.130,z0,z1,WOOD,side+' slim glazing bar')
  cuboid(b,left-.055,right+.055,-.072,.12,z0-.065,z0+.002,SILL,side+' light projecting sill')
  # Short red jamb dressings and small square heads have a stronger contrast than the stock brick.
  for direction in (-1,1):
   edge=cx+direction*(span/2+.051)
   for idx in range(1,6):
    z=z0+(z1-z0)*idx/6
    cuboid(b,edge-.049,edge+.049,-.012,.057,z-.022,z+.023,RED,side+' red jamb teeth')
  for idx in range(-2,3):
   at=cx+idx*(span+.12)/5
   cuboid(b,at-.042,at+.042,-.024,.038,z1+.008,z1+.137,RED,side+' brick lintel')
 for z,group in ((.25,'Floor string'),(1.65,'Lower window heads'),(2.47,'Attic sill string'),(3.53,'Attic head dressings')):
  limits=box(-3.2,z,3.2,z+.125).intersection(outline).difference(holes)
  solid(b,limits,-.012,.014,JOINT,group+' bedding')
  for i in range(-13,14):
   cell=box(i*.26+.004,z+.004,(i+1)*.26-.004,z+.121).intersection(limits)
   solid(b,cell,-.019,.006,RED,group+' stretchers')
 for i,((x0,z0),(x1,z1))in enumerate(zip(PROFILE,PROFILE[1:])):
  s=Polygon([(x0,z0-.13),(x1,z1-.13),(x1,z1+.015),(x0,z0+.015)])
  solid(b,s,-.102,.38,SOFFIT,'Bent bargeboard underside')
  trim=Polygon([(x0,z0+.005),(x1,z1+.005),(x1,z1+.079),(x0,z0+.079)])
  solid(b,trim,-.125,.4,TRIM,'Continuous light fascia around gable')
  solid(b,Polygon([(x0,z0+.045),(x1,z1+.045),(x1,z1+.103),(x0,z0+.103)]),.08,1.30,MORTAR,'Tile bedding up to section cut')
  # Overlapping rows recede towards the ridge; individual tile heads remain visible at the cut.
  n=max(1,round(abs(x1-x0)/(.29 if lod else .177)));colcount=6 if lod else 10
  for r in range(n):
   a=x0+(x1-x0)*r/n;c=x0+(x1-x0)*(r+1)/n
   lo=height(a)+.098;hi=height(c)+.098
   for col in range(colcount):
    y=.10+col*1.20/colcount;step=1.2/colcount;ax=(a,c)
    # Shallow paired planes create the crown of each traditional machine tile.
    for t1,t2,zA,zB in [(0,.48,0,.023),(.48,.98,.023,0)]:
     verts=[(a,y+step*t1,lo+zA),(c,y+step*t1,hi+zA),(c,y+step*t2,hi+zB),(a,y+step*t2,lo+zB)]
     b.add(verts,[(0,1,2,3)],TILES[(r*7+col*5+i)%3],'Clay tile courses on roof return')
 brick_uv(b)
