"""Photographed portion of the tiled gable at 2374 Hongqiao Road."""
from math import sin,cos,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

ID='changning-hongqiao-2374-diamond-vent-gable'
WALL='Off-white mineral render'; SHADE='Weathered soffit'; MORTAR='Brown bedding mortar'
CLAY='Terracotta with age variation'; DARK_CLAY='Dark terracotta'; LIGHT_CLAY='Faded terracotta'
FRAME='Deep olive steel'; GLASS='Blue grey window glass'; SHADOW='Shaded window rebate'
PALETTE={n:{'color':c,'roughness':r} for n,c,r in [
 (WALL,[1,1,1],.96),(SHADE,[.57,.54,.47],.96),(MORTAR,[.39,.28,.20],.95),
 (CLAY,[1,1,1],.87),(DARK_CLAY,[.76,.64,.60],.90),(LIGHT_CLAY,[1,.96,.92],.87),
 (FRAME,[.24,.26,.23],.77),(GLASS,[.35,.42,.43],.34),(SHADOW,[.088,.108,.093],.94)]}
X0=-1.66;RIDGE=.42;CUT=1.06;ZRIDGE=3.02;ZLOW=2.04;DEPTH=1.57
VENT=(.41,2.52);VR=.151;VH=.177
WIN=(-1.035,.19,.04,1.31)
def texture():
 f=Path(__file__).with_name('weathered-terracotta.png')
 if not f.is_file():
  rng=np.random.default_rng(483);y,x=np.mgrid[0:200,0:256]
  blot=np.array(Image.fromarray(rng.integers(0,255,(11,16),dtype='u1')).resize((256,200),Image.Resampling.BICUBIC),float)/255
  shade=26*(blot-.5)+rng.normal(0,5.,x.shape)+2.6*np.cos(x*.15+.04*y)
  rgb=np.clip(np.array([169,94,69])[None,None,:]+shade[:,:,None],0,255).astype('u1')
  plaster=np.clip(np.array([226,221,215])[None,None,:]+(.48*shade)[:,:,None],0,255).astype('u1')
  Image.fromarray(np.concatenate([rgb,plaster],axis=1)).quantize(160).save(f)
 for m in (CLAY,DARK_CLAY,LIGHT_CLAY,WALL):PALETTE[m]['texture']=str(f)
def roof_z(x):return ZRIDGE-abs(x-RIDGE)*(ZRIDGE-ZLOW)/(RIDGE-X0)
def face(b,p,front,back,mat,label):b.prism(p,-back,-front,lambda x,z,d:(x,-d,z),mat,label)
def block(b,x0,x1,y0,y1,z0,z1,mat,label):
 b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def shell(b,verts,fac,mat,label):
 b.add(verts,fac,mat,label);b.parts[-1]['texcoords']=[[.025+.095*(x-X0)+.018*z,.14+.35*y+.06*z]for x,y,z in verts]
def tile(b,xa,xb,cy,r,up,n,mat,label):
 # Each cap or channel is a thin ceramic shell. Its downhill lip remains open.
 verts=[]
 for x in (xa,xb):
  for offset in (0,-.012):
   for j in range(n+1):
    a=j*pi/n
    verts.append((x,cy+r*cos(a),roof_z(x)+.046+offset+(.063 if up else .012)*sin(a)*(1 if up else -1)+(.010 if abs(x-RIDGE)>abs((xa+xb)/2-RIDGE) else 0)))
 ring=n+1;faces=[]
 for j in range(n):
  faces.extend(([j,j+1,2*ring+j+1,2*ring+j],[ring+j,3*ring+j,3*ring+j+1,ring+j+1],[j,ring+j,ring+j+1,j+1],[2*ring+j,2*ring+j+1,3*ring+j+1,3*ring+j]))
 faces.extend(([0,2*ring,3*ring,ring],[n,ring+n,3*ring+n,2*ring+n]))
 shell(b,verts,faces if xb>xa else [list(reversed(f)) for f in faces],mat,label)
def sash(b,hinge,span,angle,side):
 # Project the outward opening frame, bars and glass into the same inclined leaf plane.
 c,s=cos(angle),sin(angle)
 def part(lo,hi,depth,back,bottom,top,mat,name):
  p=Polygon([(hinge+side*(u*c-d*s),-.032-u*s-d*c)for u,d in ((lo,depth),(hi,depth),(hi,back),(lo,back))])
  b.prism(p,bottom,top,lambda x,y,z:(x,y,z),mat,name)
 for u in (0,span):part(u-.018,u+.018,.018,-.021,.06,1.29,FRAME,'Opening casement stile')
 for z in (.075,.438,.838,1.275):part(.015,span-.015,.014,-.016,z-.014,z+.014,FRAME,'Steel casement rail')
 for lo,hi in zip((.09,.453,.854),(.423,.823,1.26)):part(.018,span-.018,-.009,-.016,lo,hi,GLASS,'Glass held behind casement bars')
def add_building(b,far=False):
 texture();vx,vz=VENT;diamond=Polygon([(vx,vz+VH),(vx+VR,vz),(vx,vz-VH),(vx-VR,vz)])
 x0,x1,z0,z1=WIN
 outline=Polygon([(X0,0),(CUT,0),(CUT,roof_z(CUT)),(RIDGE,ZRIDGE),(X0,ZLOW)])
 face(b,outline.difference(unary_union([diamond,box(x0,z0,x1,z1)])),0,.155,WALL,'Gable wall with open diamond and window')
 # The dark interior around the diamond is set back from the clear aperture.
 outer=Polygon([(vx,vz+VH+.018),(vx+VR+.018,vz),(vx,vz-VH-.018),(vx-VR-.018,vz)])
 face(b,outer.difference(diamond),.145,.62,SHADOW,'Recess inside diamond vent')
 face(b,box(vx-.61,vz-.40,vx+.58,vz+.39),.62,.63,SHADOW,'Deep unlit interior behind open vent')
 block(b,X0,X0+.13,.155,DEPTH,0,ZLOW-.02,WALL,'Visible whitewashed side wall')
 block(b,X0-.070,X0+.02,-.055,DEPTH, ZLOW-.089,ZLOW-.043,SHADE,'Projected eave fascia')
 block(b,X0-.036,X0+.022,-.043,DEPTH,ZLOW-.136,ZLOW-.085,WALL,'Pale lower fascia return')
 for x in (x0,x1):block(b,x-.015,x+.014,.087,.181,z0,z1,FRAME,'Fixed steel jamb')
 for z in (z0,z1):block(b,x0,x1,.082,.185,z-.019,z+.020,FRAME,'Fixed steel head or sill')
 block(b,(x0+x1)/2-.018,(x0+x1)/2+.018,.108,.18,z0,z1,FRAME,'Meeting mullion')
 face(b,box(x0-.16,z0,x1+.21,z1+.14),.52,.54,SHADOW,'Deep window shadow behind open leaves')
 for x in (x0+.019,x1-.019):
  for z in (.33,1.07):
   block(b,x-.022,x+.022,-.049,.124,z-.047,z+.047,FRAME,'Hinge connection to fixed jamb')
 sash(b,x0+.019,(x1-x0)/2-.04,2.08,1);sash(b,x1-.019,(x1-x0)/2-.04,1.90,-1)
 for l,r in ((X0-.077,RIDGE),(RIDGE,CUT)):
  surf=Polygon([(l,roof_z(l)-.035),(r,roof_z(r)-.035),(r,roof_z(r)+.006),(l,roof_z(l)+.006)])
  face(b,surf,-.078,DEPTH+.018,MORTAR,'Bedding below field tiles')
 n=4 if far else 8
 for side,t in ((-1,X0-.081),(1,CUT)):
  length=abs(t-RIDGE);nc=max(2,round(length/.385))
  for ci in range(nc):
   a=RIDGE+side*length*ci/nc;e=RIDGE+side*length*(ci+1)/nc
   for j in range(9):
    cy=-.001+j*.189;tile(b,a,e,cy,.081,True,n,(CLAY,CLAY,DARK_CLAY,CLAY,LIGHT_CLAY)[(ci*7+j*11)%5],'Convex terracotta cover tiles')
    if j<8:tile(b,a,e,cy+.0945,.077,False,n,CLAY,'Concave pan tiles')
 for j in range(7):
  # Ridge caps run crosswise to the cover tiles and lap one another.
  start=-.083+j*.245;stop=min(start+.266,DEPTH+.028);v=[]
  for y,drop in ((start,0),(stop,-.012)):
   for off in (0,-.012):
    for i in range(n+1):
     angle=i*pi/n;v.append((RIDGE+.095*cos(angle),y,ZRIDGE+.04+.087*sin(angle)+drop+off))
  k=n+1;faces=[]
  for i in range(n):faces.extend(([i,i+1,2*k+i+1,2*k+i],[k+i,3*k+i,3*k+i+1,k+i+1],[i,k+i,k+i+1,i+1],[2*k+i,2*k+i+1,3*k+i+1,3*k+i]))
  shell(b,v,[list(reversed(f)) for f in faces],CLAY,'Transverse rounded ridge cap')
 for part in b.parts:
  if part['material']==WALL:
   part['texcoords']=[[.535+.12*(x-X0)+.013*y,.085+.24*z+.026*y] for x,y,z in part['vertices']]
