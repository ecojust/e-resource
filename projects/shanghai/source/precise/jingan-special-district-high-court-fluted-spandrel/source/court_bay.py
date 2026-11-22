"""Two fluted pilasters and the carved window spandrel on the Special District High Court, after the 2016 Fayhoo photograph."""
from pathlib import Path
from math import pi,sin,cos
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,LineString,box,Point
from shapely.affinity import affine_transform
ID='jingan-special-district-high-court-fluted-spandrel'
STONE='Weathered ochre cement render'; EDGE='Lighter carved arris';SHADOW='Dark undercut';RENDER='Coarse wall finish'
LOW='Dark aged sash';UP='Pale metal sash';SKY='Blue-grey glazing';GREY='Shadowed glazing';DEEP='Recessed central socket';LIGHT='Glazed reflection'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(STONE,[1,1,1],.92),(EDGE,[.72,.61,.45],.91),(SHADOW,[.22,.151,.089],.95),(RENDER,[.9,.88,.80],.96),(LOW,[.30,.234,.175],.73),(UP,[.73,.67,.52],.69),(SKY,[.38,.49,.53],.33),(GREY,[.28,.34,.36],.39),(LIGHT,[.44,.54,.56],.32),(DEEP,[.115,.095,.073],1)]}
S=.009
def X(x):return (x-245)*S
def Z(y):return (790-y)*S
def texture():
 f=Path(__file__).with_name('ochre-render.png')
 if not f.exists():
  r=np.random.default_rng(491);noise=r.normal(0,7.1,(810,640));arr=r.integers(65,192,(18,17),dtype='u1')
  stains=(np.asarray(Image.fromarray(arr).resize((640,810),Image.Resampling.BICUBIC),float)-128)*.22
  Image.fromarray(np.clip(np.array([186,163,130])[None,None,:]+(stains+noise)[:,:,None],0,255).astype('u1')).quantize(175).save(f)
 for m in (STONE,RENDER):PALETTE[m]['texture']=str(f)
def prism(b,p,front,back,mat,label):
 if p.is_empty:return
 for part in getattr(p,'geoms',[p]):
  if part.geom_type!='Polygon' or part.area<.005:continue
  shape=affine_transform(part,[S,0,0,-S,-245*S,790*S])
  b.prism(shape,-back,-front,lambda x,z,d:(x,-d,z),mat,label)
def rect(b,l,t,r,base,front,back,mat,label):prism(b,box(l,t,r,base),front,back,mat,label)
def carving(b,p,base,relief,mat,label,far):
 prism(b,p,base-relief*.62,base,mat,label)
 inner=p.buffer(-.65,join_style=1,quad_segs=1 if far else 3)
 if not inner.is_empty:prism(b,inner,base-relief,base-relief*.615,mat,label+' crest')
def cord(b,xy,w,y,relief,mat,label,far):
 p=LineString(xy).buffer(w/2,join_style=1,cap_style=1,quad_segs=2 if far else 5);carving(b,p,y,relief,mat,label,far)
def scrolls(b,c,far):
 f=-.147
 rect(b,c-58,65,c+58,137,f,.13,STONE,'Capital block')
 for k,(y,th,depth,mat)in enumerate([(48,5,-.216,SHADOW),(51,6,-.249,STONE),(57,4,-.207,EDGE),(61,5,-.186,SHADOW),(66,4,-.16,STONE),(129,5,-.165,EDGE),(135,4,-.16,SHADOW)]):
  rect(b,c-61,y,c+61,y+th,depth,.11,mat,'Abacus and neck moulding '+str(k))
 # The two roll ends spiral inward and enclose the shallow half-disc shown between them.
 angles=np.linspace(0,1,16 if far else 36);u=np.linspace(0,1,12 if far else 26)
 for sig in (-1,1):
  pts=[(c+sig*(38+(15-12*t)*cos(-pi/2-t*2.12*pi)),106+(15-12*t)*sin(-pi/2-t*2.12*pi))for t in angles]
  cord(b,pts,7.5,f,.024,SHADOW,'Volute undercut',far)
  b.tube([(X(x),f-.044,Z(y))for x,y in pts],.023,STONE,6 if far else 12,'Rounded scroll of capital')
 crown=[(c-38,90.7),(c+38,90.7)]+[(c+38*cos(t*pi),91+16*sin(t*pi))for t in u]
 carving(b,Polygon(crown).buffer(0),f,.056,STONE,'Shallow bow between paired volutes',far)
 b.tube([(X(c-38),f-.05,Z(90.7)),(X(c+38),f-.05,Z(90.7))],.013,STONE,6 if far else 10,'Upper rim of capital')
 # Four short hanging channels descend from a U-shaped tablet.
 a=box(c-29,136,c+29,208).buffer(0);prism(b,a,-.149,.091,SHADOW,'Recess behind the hanging capital tablet')
 p=Polygon([(c-29,133),(c+29,133),(c+29,195),(c+26,204),(c+17,209),(c-20,209),(c-27,205),(c-29,199)])
 for dx in [-18,-6,6,18]:
  channel=LineString([(c+dx,148),(c+dx,195)]).buffer(2.2,quad_segs=2 if far else 6);p=p.difference(channel)
 carving(b,p,-.143,.043,STONE,'Four-cut tablet with rounded lower corners',far)
def shaft(b,c,far):
 # The profile is a solid, with eight concave channels, not a texture of vertical lines.
 front=-.133;rear=.12;y0=211;xs=[(c-55,front),(c-34,front)]
 for off in [-28,-20,-12,-4,4,12,20,28]:
  for phase in np.linspace(0,pi,4 if far else 10):
   xs.append((c+off-3*cos(phase),front+.036*sin(phase)))
 xs +=[(c+35,front),(c+55,front),(c+55,rear),(c-55,rear)]
 shape=Polygon([(X(x),y)for x,y in xs]);b.prism(shape,Z(781),Z(y0),lambda x,y,z:(x,y,z),STONE,'Pilaster shaft with eight concave flutes')
 rect(b,c-55,139,c+55,211,-.13,.13,STONE,'Pilaster neck around suspended tablet')
 for o in (-53,53):rect(b,c+o-.6,141,c+o+.6,781,-.14,-.10,EDGE,'Pilaster corner arris')
def windows(b,y0,y1,low,far):
 l,r=127,364;frame=UP if low else LOW;depth=.118
 for k,(top,bot)in enumerate(zip([y0+3,y0+(y1-y0)*.365,y0+(y1-y0)*.696],[y0+(y1-y0)*.365,y0+(y1-y0)*.696,y1-4])):
  for j in range(4):
   a=l+(r-l)*j/4+2;v=l+(r-l)*(j+1)/4-1.8
   rect(b,a,top,v,bot,depth,.15,(SKY,LIGHT,GREY,SKY)[(k+2*j)%4],'Glazed light in historic steel sash')
 for i in range(5):
  x=l+(r-l)*i/4;rect(b,x-1.85,y0,x+1.85,y1,.074 if i not in (0,4) else .052,.148,frame,'Steel sash upright')
 for j,py in enumerate([y0,y0+(y1-y0)*.365,y0+(y1-y0)*.696,y1]):
  th=3.2 if j in (0,3) else 2;rect(b,l,py-th,r,py+th,.058 if j==1 else .073,.15,frame,'Sash horizontal rail')
 for lgt,py in [(1.5,y1),(3.6,y1+4),(2.3,y1+7)]:
  rect(b,l-3,py,r+4,py+lgt,-.07,.162,STONE,'Window sill drip')
def spandrel(b,far):
 l,r=121.5,369
 prism(b,box(l,270,r,452).difference(box(235,347,251,367)),.013,.245,STONE,'Pierced window apron and head to lower opening')
 for i in range(5):
  for y in (299+i*7.6,381+i*8.2):
   rect(b,l,y,r,y+2.5,-.039,.025,SHADOW,'Under-cut of horizontal spandrel line')
   rect(b,l,y-1.9,r,y+.5,-.056,.025,STONE,'Raised horizontal spandrel fillet')
 panel=box(l,337,r,379);socket=box(235,347,251,367)
 prism(b,panel.difference(socket),-.025,.06,STONE,'Decorative cheek and square recess')
 rect(b,235,347,251,367,.045,.073,DEEP,'Dark back of square central socket')
 frame=box(227,337.5,259,377).difference(socket)
 carving(b,frame,-.026,.025,STONE,'Raised surround to square socket',far)
 for sig in (-1,1):
  side=box(l if sig<0 else 261,339,225 if sig<0 else r,378)
  # Short paired cuts form a run of herringbone groups and stop at the square surround.
  for ix in range(3):
   x=242+sig*(28+31*ix)
   for offset in (0,5.3):
    pts=[(x+sig*offset,345),(x+sig*(17+offset),370),(x+sig*(30+offset),345)]
    g=LineString(pts).buffer(1.5,join_style=2,cap_style=2).intersection(side)
    if not g.is_empty:
     prism(b,g.buffer(.84,quad_segs=2),-.040,-.025,SHADOW,'Cut alongside the herringbone')
     carving(b,g,-.043,.027,STONE,'Bevelled herringbone face',far)
def add_building(b,far=False):
 texture()
 apertures=box(127,79,364,265).union(box(127,455,364,711))
 prism(b,box(11,38,486,781).difference(apertures),.085,.31,RENDER,'Retained wall around both recessed openings')
 for c in [66,426]:shaft(b,c,far);scrolls(b,c,far)
 windows(b,79,265,False,far);windows(b,455,711,True,far);spandrel(b,far)
 for y,th,fr in [(39,6,-.076),(44,3,-.108),(47,3,-.15)]:
  rect(b,9,y,486,y+th,fr,.25,STONE,'Continuous line of cornice above capitals')
 for y in [731,737,743]:
  rect(b,121,y,370,y+2,-.01,.096,SHADOW,'Top of lower spandrel at section boundary')
 for part in b.parts:
  if part['material'] in (STONE,RENDER):
   part['texcoords']=[[.5+v[0]*.20+v[1]*.03,.035+v[2]*.131-v[1]*.018] for v in part['vertices']]
