"""Bricks, three lozenge lines and concrete chimney crown in the Lixi Road photograph."""
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union
BRICK='Rust red running bond';COPING='Cool grey coping';DARK='Deep grey stringcourse';BROWN='Dark diamond brick';RUBBED='Red cut brick';GLASS='Recessed blue green glass';WOOD='Green black joinery';SHADE='Dark mortar between roof tiles';TILE='Fired roof tile';LIGHT='Weathered tile';BAND='Chimney crown shadow'
colors={BRICK:(255,255,255),COPING:(126,125,118),DARK:(69,67,67),BROWN:(81,61,59),RUBBED:(148,80,65),GLASS:(52,63,58),WOOD:(53,55,51),SHADE:(85,77,72),TILE:(156,111,94),LIGHT:(175,129,111),BAND:(76,78,73)}
PALETTE={k:dict(color=[(v/255.)**2.2 for v in c],roughness=.84)for k,c in colors.items()};PALETTE[BRICK]['texture']=str(Path(__file__).with_name('lixi-running-bond.png'))
W=2.25;EAVE=2.40;RIDGE=5.18;WINDOWS=[(-1.18,.61),(1.05,.61)]
PEN=[((0,4.76),(.278,3.86)),((.278,3.86),(0,2.965)),((0,2.965),(-.278,3.86)),((-.278,3.86),(0,4.76)),((0,4.15),(.11,3.86)),((.11,3.86),(0,3.58)),((0,3.58),(-.11,3.86)),((-.11,3.86),(0,4.15))]
def h(x):return RIDGE-(RIDGE-EAVE)*abs(x)/W
def slab(b,s,y0,y1,mat,name):
 for part in getattr(s,'geoms',[s]):
  if part.geom_type=='Polygon'and part.area>1.e-7:b.prism(part,-y1,-y0,lambda x,z,j:(x,-j,z),mat,label=name)
def cb(b,x0,x1,y0,y1,z0,z1,mat,name):
 b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)
def bricks_uv(b):
 for p in b.parts:
  if p['material']!=BRICK:continue
  vertices=[];tris=[];uv=[];before=np.array(p['vertices'])
  for tri in p['triangles']:
   pts=before[np.asarray(tri)];start=len(vertices);vertices.extend(pts.tolist());tris.append([start,start+1,start+2]);axis=np.argmax(np.abs(np.cross(pts[1]-pts[0],pts[2]-pts[0])))
   for x,y,z in pts:uv.append([(x+2.4)/5.74 if axis!=0 else (y+.22)/1.46,1-z/5.55])
  p.update(vertices=vertices,triangles=tris,texcoords=uv)
def model(b,lod=False):
 wall=Polygon([(-W,0),(W,0),(W,EAVE),(0,RIDGE),(-W,EAVE)])
 holes=unary_union([box(x-d/2,.14,x+d/2,1.63)for x,d in WINDOWS])
 slab(b,wall.difference(holes),0,.28,BRICK,'Front in running red brick')
 for n,(cx,span)in enumerate(WINDOWS):
  x0=cx-span/2;x1=cx+span/2;tag='Left window'if n==0 else 'Right window'
  cb(b,x0,x1,.13,.16,.14,1.63,GLASS,tag+' set-back panes')
  for x in (x0+.023,cx,x1-.023):cb(b,x-.016,x+.016,.080,.139,.14,1.63,WOOD,tag+' glazing uprights')
  for z in (.16,1.23,1.605):cb(b,x0,x1,.074,.14,z-.019,z+.019,WOOD,tag+' transoms')
  for x in [x0-.046,x1+.046]:cb(b,x-.039,x+.039,-.020,.11,.08,1.71,RUBBED,tag+' rubbed jamb')
  cb(b,x0-.084,x1+.084,-.020,.095,1.63,1.716,RUBBED,tag+' brick head')
  cb(b,x0-.08,x1+.08,-.070,.1,.075,.137,DARK,tag+' sill')
 for mat,lo,hi,front in [(DARK,2.10,2.175,-.072),(COPING,2.175,2.30,-.118),(DARK,2.30,2.40,-.143)]:
  cb(b,-W-.06,W+.06,front,.32,lo,hi,mat,'Courses below triangle '+mat)
 for sign in (-1,1):
  tip=sign*(W+.035);poly=Polygon([(0,RIDGE-.067),(tip,EAVE-.067),(tip,EAVE+.112),(0,RIDGE+.14)])
  slab(b,poly,-.101,.40,COPING,'Coping of pitched parapet')
  lo,hi=sorted([0.0,sign*W]);roof=Polygon([(lo,h(lo)-.042),(hi,h(hi)-.042),(hi,h(hi)-.105),(lo,h(lo)-.105)])
  slab(b,roof,.405,1.16,SHADE,'Tile bed behind parapet')
  # Each painted surface is a separate stepped tile course. Both pitches return behind the coping.
  for k in range(13):
   xa=sign*(.02+k*(W-.025)/13);xb=sign*(.02+(k+1)*(W-.025)/13);za,zb=h(xa)-.01,h(xb)-.01
   course=Polygon([(xa,za),(xb,zb),(xb,zb-.052),(xa,za-.077)])
   count=5 if lod else 9
   for j in range(count):
    a=.405+j*.735/count;slab(b,course,a+.003,a+.735/count-.003,LIGHT if (j+2*k)%5==0 else TILE,'Tiles on slope '+str(sign))
 for i,(a,c)in enumerate(PEN):
  count=(6 if i<4 else 2) if lod else (11 if i<4 else 4)
  dl=np.array(c)-np.array(a)
  for k in range(count):
   p0=np.array(a)+dl*((k+.045)/count);p1=np.array(a)+dl*((k+.955)/count)
   slab(b,LineString([p0,p1]).buffer(.037 if i<4 else .024,cap_style='flat'),-.012,.016,BROWN,'Dark brick outer lozenge'if i<4 else 'Small central lozenge')
 cb(b,2.27,2.91,-.039,.56,.0,4.61,BRICK,'Square chimney shaft')
 for lo,hi,delta,mat in [(4.60,4.69,.045,DARK),(4.69,4.78,.105,COPING),(4.78,5.14,.04,COPING),(5.14,5.205,.073,BAND),(5.205,5.278,.121,COPING)]:
  cb(b,2.27-delta,2.91+delta,-.039-delta,.56+delta,lo,hi,mat,'Chimney cap '+str(lo))
 for x in (2.34,2.54,2.73,2.85):cb(b,x-.009,x+.009,-.083,-.071,4.80,5.12,BAND,'Vertical joints in chimney cap')
 bricks_uv(b)
