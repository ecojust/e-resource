"""The upper Taiyuan Road elevation of the double dwelling at No. 50 Lane."""
from math import ceil,cos,sin,pi
from random import Random
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
PLASTER='Warm-grey coarse plaster';SILL='Pale cement sill';BAND='Lime cornice';SHADE='Dark eave shadow';WOOD='Oxblood timber sash';GLASS='Muted blue-grey glazing';PANE='Cool glazed highlight';METAL='Weathered rainwater pipe';TILE='Earthen red roof tiles';DARK_TILE='Maroon firing variation';MORTAR='Tile bedding';LEAD='Folded sheet-metal hood';PANEL='Mineral grey high opening';REAR='Section cut'
PALETTE={m:dict(color=color,roughness=r) for m,color,r in [(PLASTER,[.657,.606,.548],.94),(SILL,[.68,.64,.53],.90),(BAND,[.724,.705,.664],.89),(SHADE,[.23,.193,.16],.94),(WOOD,[.262,.120,.082],.82),(GLASS,[.17,.213,.242],.33),(PANE,[.241,.268,.289],.38),(METAL,[.132,.132,.112],.78),(TILE,[.404,.354,.342],.91),(DARK_TILE,[.370,.315,.309],.91),(MORTAR,[.277,.250,.245],.96),(LEAD,[.263,.244,.225],.77),(PANEL,[.394,.411,.403],.93),(REAR,[.42,.38,.315],.98)]}
FLOOR=4.27; HI=7.97; LO=6.49; XL=-5.18; XR=2.60; STEP=-2.035; DEPTH=1.50
WINDOWS=[('High sash',-4.12,.98,6.30,7.49),('Small high opening',-2.42,.448,6.65,7.45),('South low sash',-1.278,.90,4.76,5.63),('North low sash',1.278,.94,4.74,5.63)]
def block(b,name,m,x0,x1,y0,y1,z0,z1):
 b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=name)
def rod(b,name,m,start,end,radius,sides):
 import numpy as np
 p,q=np.array(start,float),np.array(end,float);a=q-p;a/=np.linalg.norm(a)
 side=np.cross(a,[1,0,0] if abs(a[0])<.8 else [0,1,0]);side/=np.linalg.norm(side);normal=np.cross(a,side)
 ring=[radius*(cos(2*pi*i/sides)*side+sin(2*pi*i/sides)*normal)for i in range(sides)]
 b.add([v+o for o in [p,q] for v in ring], [tuple(reversed(range(sides))),tuple(range(sides,2*sides)),*[(i,(i+1)%sides,sides+(i+1)%sides,sides+i) for i in range(sides)]],m,name)
def tiles(b,label,left,right,front,back,height,slope,lod):
 def map_(x,y,d):return (x,y,height+slope*(y-front)+d)
 b.prism(box(left,front,right,back),-.105,0,map_,MORTAR,label+' tile bed')
 rng=Random(39);pitch=.19 if not lod else .30;width=.16 if not lod else .27
 for j in range(ceil((back-front)/pitch)):
  y=front+j*pitch;end=min(y+pitch,back)
  for i in range(-1,ceil((right-left)/width)+1):
   x=left+width*(i+(.5 if j%2 else 0));l=max(x+.005,left);r=min(x+width-.005,right)
   if r-l<.015:continue
   top=[(l,y,.024),(r,y,.024),(r,end-.005,.009),(l,end-.005,.009)]
   base=[(a,c,.002)for a,c,z in top]
   b.add([map_(*p)for p in base+top],[(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],TILE if rng.random()<.71 else DARK_TILE,label+' staggered tiles')
def window(b,f,name,c,width,sill,head,panel,lod):
 h=head-sill
 f.box(c,(sill+head)/2,width+.008,h+.008,.035,-.169,SHADE,name+' reveal')
 f.box(c,sill-.040,width+.20,.080,.26,.040,SILL,name+' projecting sill')
 if panel:
  f.box(c,(sill+head)/2,width-.076,h-.065,.024,-.088,PANEL,name+' closed face')
  for x in [c-width/2+.020,c+width/2-.020]:f.box(x,(sill+head)/2,.035,h,.068,-.025,METAL,name+' jamb')
  for z in [sill+.015,head-.015]:f.box(c,z,width,.03,.068,-.025,METAL,name+' frame')
  return
 t=.052;gap=.038
 for col in range(2):
  for row in range(2):
   # The fanlights above the meeting rail are shallower than the casements.
   x0=c-width/2+t+col*(width-2*t)/2;x1=x0+(width-2*t)/2
   z0,z1=(sill+t,sill+.65*h) if row==0 else (sill+.65*h,head-t)
   f.box((x1+x0)/2,(z1+z0)/2,x1-x0-.016,z1-z0-.016,.028,-.083,GLASS if (col+row)%2 else PANE,name+' glazing')
 for x in [c-width/2+t/2,c+width/2-t/2]:f.box(x,(sill+head)/2,t,h,.098,-.014,WOOD,name+' outer jamb')
 for z in [sill+t/2,head-t/2]:f.box(c,z,width,t,.108,-.010,WOOD,name+' outer rail')
 f.box(c,(sill+head)/2,gap,h-.08,.060,-.050,WOOD,name+' meeting stile')
 f.box(c,sill+h*.65,width-.09,.044,.066,-.043,WOOD,name+' transom')
 if 'low' in name:
  block(b,name+' hood flashing',METAL,c-width/2-.12,c+width/2+.12,-.020,.072,head+.101,head+.171)
  # 2015 oblique views show a folded, dark leading edge with light on its ridge.
  half=width/2+.154
  front=-.390
  back=-.015
  def hood_top(y):return head+.157+.16*y
  b.prism(box(c-half,front,c+half,back),-.018,0,lambda x,y,d:(x,y,hood_top(y)+d),LEAD,name+' sloping hood')
  block(b,name+' folded hood nose',LEAD,c-half,c+half,front-.008,front+.008,hood_top(front)-.056,hood_top(front)+.005)
  for x in [c-half+.008,c+half-.008]:
   b.prism(box(x-.008,front,x+.008,back),-.043,.005,lambda x,y,d:(x,y,hood_top(y)+d),LEAD,name+' folded hood end')
  # Raised narrow seams run down the pitch; their spacing is an exterior approximation.
  for i in range(1,8):
   x=c-half+2*half*i/8
   b.prism(box(x-.006,front+.018,x+.006,back-.018),-.004,.011,lambda x,y,d:(x,y,hood_top(y)+d),LEAD,name+' hood seam')
  for x in [c-width/2+.025,c+width/2-.025]:
   rod(b,name+' hood stay',METAL,[x,-.026,head-.045],[x,front+.044,hood_top(front)-.027],.014,5 if lod else 8)
def add_building(b,lod):
 f=Facade(b,(-6,0),(6,0),'Taiyuan east upper wall')
 outline=Polygon([(XL,FLOOR),(XR,FLOOR),(XR,LO-.16),(STEP,LO-.16),(STEP,HI-.16),(XL,HI-.16)])
 holes=[box(c-w/2,sill,c+w/2,top)for _,c,w,sill,top in WINDOWS]
 f.wall(FLOOR,HI,holes,thickness=.31,material=PLASTER,outline=outline)
 for name,c,w,sill,head in WINDOWS:window(b,f,name,c,w,sill,head,'Small' in name,lod)
 for left,right,z,prefix in [(XL,STEP,HI,'Higher southern eave'),(STEP,XR,LO,'Northern lower eave')]:
  block(b,prefix+' bedding',SHADE,left-.04,right+.04,-.219,.16,z-.216,z-.164)
  block(b,prefix+' projecting fascia',BAND,left-.056,right+.056,-.266,.15,z-.164,z-.055)
  block(b,prefix+' cap',SILL,left-.065,right+.065,-.287,.15,z-.055,z-.005)
  tiles(b,prefix,left-.074,right+.074,-.30,DEPTH,z,.40,lod)
  block(b,prefix+' underside',SHADE,left,right,.15,DEPTH,z-.16,z-.105)
  b.prism(box(left,0,right,DEPTH),-.015,0,lambda x,y,d:(x,y,FLOOR+d),REAR,prefix+' section base')
  b.prism(box(left,FLOOR,right,z+.40*(DEPTH+.3)),0,.03,lambda x,zz,d:(x,DEPTH-d,zz),REAR,prefix+' section back')
 for x,low,high,label in [(XL,FLOOR,HI,'South crop return'),(XR,FLOOR,LO,'North crop return'),(STEP,LO-.025,HI,'Step return')]:
  poly=Polygon([(0,low),(DEPTH,low),(DEPTH,high+.72),(0,high+.085)])
  b.prism(poly,0 if x==XL else -.07,.07 if x==XL else 0,lambda y,z,d:(x+d,y,z),PLASTER,label)
 for z,h,depth in [(FLOOR+.025,.048,.066),(FLOOR+.100,.052,.11),(FLOOR+.193,.042,.072)]:
  f.box((XL+XR)/2,z,XR-XL,h,depth,.008,BAND,'Horizontal floor mouldings')
 for x,z in [(-3.18,HI-.19),(-.013,LO-.16)]:
  rod(b,'Rainwater stack',METAL,[x,-.060,FLOOR+.21],[x,-.060,z-.18],.045,8 if lod else 12)
  rod(b,'Gutter outlet elbow',METAL,[x,-.060,z-.18],[x,-.199,z-.050],.052,8 if lod else 12)
  for a in [FLOOR+.60,(FLOOR+z)/2,z-.38]:
   rod(b,'Rainwater pipe collar',METAL,[x,-.060,a],[x,-.060,a+.037],.057,8 if lod else 14)

 b.palette[PLASTER]['texture']=str(Path(__file__).with_name('wall-aggregate.png'))
 for part in b.parts:
  if part['material']!=PLASTER:continue
  side='return' in part['label'].lower()
  part['texcoords']=[[(y+.01)/(DEPTH+.035) if side else (x-XL+.02)/(XR-XL+.04),1.-(z-FLOOR+.025)/(HI+.755-FLOOR)]for x,y,z in part['vertices']]
