"""Apartment wing photographed by the district. Model the hip roof and corbelled parapet."""
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from profile_tools import BRICK,slab,cb,bricks_uv
STONE='Grey stone coping';BAND='Shade below coping';GLASS='Deep green glazing';WOOD='Green steel glazing bars';TILE='Fired red tile';LIGHT='Light red weathered tile';RIDGE='Ochre ridge tile';PARAPET='Dark parapet facing';SOFFIT='Concrete corbel'
rgb={PARAPET:(91,97,89),'Roof bedding':(107,65,49),BRICK:(255,255,255),STONE:(199,199,183),BAND:(107,114,108),GLASS:(63,89,83),WOOD:(83,97,90),TILE:(151,78,53),LIGHT:(161,86,57),RIDGE:(183,106,73),SOFFIT:(137,148,139)}
PALETTE={k:{'color':[(q/255)**2.2 for q in c],'roughness':.85} for k,c in rgb.items()}
PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))
HALF=3.18;DEPTH=3.56;EAVE=2.48;RIDGE_Z=3.51
WINS=[-2.43,-1.22,.0,1.25,2.49]
def roof_z(x,y):
 return EAVE+(RIDGE_Z-EAVE)*max(0,min(1.,(HALF-.18-abs(x))/2.18,(y-.16)/1.49,(DEPTH-.14-y)/1.49))
def model(b,lod=False):
 wall=box(-HALF,0,HALF,1.90);cut=unary_union([box(x-.38,.12,x+.38,1.22)for x in WINS])
 slab(b,wall.difference(cut),0,.21,BRICK,'Brick face of wing below parapet')
 for x in WINS:
  cb(b,x-.38,x+.38,.139,.16,.12,1.22,GLASS,'Windows of uppermost storey')
  for fx in (x-.345,x,x+.345):cb(b,fx-.014,fx+.014,.087,.15,.12,1.22,WOOD,'Narrow upright frames')
  for fz in (.145,.91,1.20):cb(b,x-.38,x+.38,.077,.15,fz-.012,fz+.012,WOOD,'Crossbars')
 for x in (-HALF,HALF-.19):cb(b,x,x+.19,.205,DEPTH,0,1.91,BRICK,'Side return below frieze')
 for z,d,mat in [(1.87,.064,BAND),(1.944,.105,SOFFIT),(2.02,.14,STONE)]:
  cb(b,-HALF-d,HALF+d,-d,.22,z,z+.077,mat,'Horizontal cornice course')
  for sign in (-1,1):
   xc=sign*(HALF+d/2-.04);cb(b,xc-.09-d/2,xc+.09+d/2,.22,DEPTH+d,z,z+.077,mat,'Side cornice course')
 for i in range(17):
  x=-HALF+.15+i*(2*HALF-.30)/16
  cb(b,x-.047,x+.047,-.087,.03,1.54,1.94,SOFFIT,'Rectangular modillions')
  cb(b,x-.061,x+.061,-.111,.04,1.83,1.91,STONE,'Modillion shoulder')
 for side in (-1,1):
  for i in range(10):
   y=.16+(DEPTH-.29)*i/9;xc=side*(HALF+.03);cb(b,xc-.054,xc+.054,y-.045,y+.045,1.55,1.93,SOFFIT,'Side modillions')
 for y in (.021,DEPTH-.16):
  cb(b,-HALF-.04,HALF+.04,y-.045,y+.15,2.097,2.26,STONE,'Low parapet wall')
  for i in range(14):
   x=-HALF+.215+(2*HALF-.43)*i/13
   cb(b,x-.171,x+.171,y-.028,y+.14,2.26,2.423,PARAPET,'Dark parapet teeth')
   cb(b,x-.177,x+.177,y-.038,y+.145,2.423,2.455,STONE,'Pale caps on parapet teeth')
  if y<.1:
   # The taller rectangular riser is to the right of the center in the front photograph.
   cb(b,.43,.76,y-.009,y+.145,2.26,2.746,PARAPET,'Raised parapet block')
   cb(b,.405,.786,y-.036,y+.152,2.746,2.789,STONE,'Light cap of the raised block')
 for side in (-1,1):
  xc=side*(HALF-.04);cb(b,xc-.092,xc+.092,.12,DEPTH-.10,2.097,2.26,STONE,'Return parapet')
  for j in range(1,9):
   y=.13+j*(DEPTH-.30)/9;cb(b,xc-.079,xc+.079,y-.065,y+.065,2.26,2.44,STONE,'Return merlons')
 def quad(points,material,tag):
  # Each tile has an exposed nose, real top and a continuous back.
  xs=[p[0] for p in points];ys=[p[1]for p in points];ring=list(zip(xs,ys))
  b.prism(Polygon(ring),-.029,0,lambda x,y,d:(x,y,roof_z(x,y)+d),material,label=tag)
 # Four continuous hipped planes underlie the individual tiles and close their seams.
 a=HALF-.18;x=a-2.18;y0=.16;y1=y0+1.49;y3=DEPTH-.14;y2=y3-1.49
 faces=[ [(-a,y0),(a,y0),(x,y1),(-x,y1)],[(a,y0),(a,y3),(x,y2),(x,y1)],
         [(-a,y3),(-x,y2),(x,y2),(a,y3)],[(-a,y0),(-x,y1),(-x,y2),(-a,y3)],
         [(-x,y1),(x,y1),(x,y2),(-x,y2)] ]
 for face in faces:
  b.prism(Polygon(face),-.073,-.039,lambda xx,yy,d:(xx,yy,roof_z(xx,yy)+d),'Roof bedding',label='Continuous bedding below the hipped roof')
 nx,ny=(25,17) if lod else (47,31)
 for j in range(ny):
  y0=.16+(DEPTH-.30)*j/ny;y1=.16+(DEPTH-.30)*(j+1)/ny
  for i in range(nx):
   x0=(-HALF+.18)+(2*HALF-.36)*i/nx;x1=(-HALF+.18)+(2*HALF-.36)*(i+1)/nx
   quad([(x0+.001,y0+.002),(x1-.001,y0+.002),(x1-.001,y1-.002),(x0+.001,y1-.002)],LIGHT if (7*i+11*j)%13<3 else TILE,'Slates of the red hipped roof')
 for sx in (-1,1):
  for yy,peak_y in ((.16,1.65),(DEPTH-.14,DEPTH-.14-1.49)):
   x0=sx*(HALF-.18);x1=sx*(HALF-.18-2.18)
   # Raised cap tile at each hip, independently checked against the two roof planes.
   for j in range(7 if lod else 14):
    count=7 if lod else 14;u0=j/count;u1=(j+1)/count
    xa=x0+(x1-x0)*u0;xb=x0+(x1-x0)*u1;ya=yy+(peak_y-yy)*u0;yb=yy+(peak_y-yy)*u1
    import math
    dx=xb-xa;dy=yb-ya;ln=math.hypot(dx,dy);ox=-.035*dy/ln;oy=.035*dx/ln
    ring=[(xa+ox,ya+oy),(xb+ox,yb+oy),(xb-ox,yb-oy),(xa-ox,ya-oy)]
    b.prism(Polygon(ring),.014,.066,lambda xx,yy,d:(xx,yy,roof_z(xx,yy)+d),RIDGE,label='Raised diagonal hip tiles')
 cb(b,-.82,.82,1.654,1.787,3.491,3.548,RIDGE,'High ridge capping')
 bricks_uv(b)
