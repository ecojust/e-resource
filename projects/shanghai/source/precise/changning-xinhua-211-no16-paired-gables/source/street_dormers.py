"""Two adjoining, unequal roof windows photographed at 16, Lane 211 Xinhua Road."""
from math import pi,cos,sin
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon, LineString
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
ID='changning-xinhua-211-no16-paired-gables'
PLASTER='Cream stucco';FRAME='Weathered red window frame';STRIPE='Narrow reddish facade band';DARK='Shaded roof board';EDGE='Weathered eave edge';TILE='Red and umber roof tiles';ROOF='Dark tile undercourse';GLASS='Dark muted window glass';PALE_GLASS='Sky-lit gable glass';CAME='Narrow glazing bar';CAP='Pale projecting cornice';WHITE='Soffit in shade';GUTTER='Dull metal rain gutter';METAL='Dark awning supports'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [
 (PLASTER,[.94,.90,.79],.95),(FRAME,[.39,.157,.097],.82),(STRIPE,[.55,.233,.129],.94),(DARK,[.245,.157,.111],.93),(EDGE,[.37,.34,.28],.92),(TILE,[1,1,1],.9),(ROOF,[.28,.226,.182],.95),(GLASS,[.247,.282,.264],.29),(PALE_GLASS,[.467,.493,.456],.25),(CAME,[.36,.19,.126],.72),(CAP,[.79,.766,.66],.92),(WHITE,[.66,.622,.535],.94),(GUTTER,[.567,.551,.490],.72),(METAL,[.234,.234,.218],.75)]}
SMALL=(-1.37,.685,.256,.59,1.955,2.352,1.56)
LARGE=(1.355,1.035,-.324,.414,2.065,2.723,1.96)
def texture():
 p=HERE/'clay-roof.png'
 if not p.exists():
  rng=np.random.default_rng(475);y,x=np.mgrid[:224,:280]
  cloud=np.array(Image.fromarray(rng.integers(0,255,(13,19),dtype=np.uint8)).resize((280,224),Image.Resampling.BICUBIC))/255
  d=21*(cloud-.5)+5*np.sin(x*.24)+rng.normal(0,2.7,x.shape)
  img=np.array([132,82,58])[None,None,:]+d[:,:,None]
  Image.fromarray(np.uint8(np.clip(img,0,255))).quantize(96).save(p)
 PALETTE[TILE]['texture']=str(p)
def rect(b,x0,x1,z0,z1,y0,y1,mat,label):
 b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def face(b,poly,y0,y1,mat,label):
 b.prism(poly,-y1,-y0,lambda x,z,t:(x,-t,z),mat,label)
def band(b,x0,z0,x1,z1,y0,y1,width,mat,label):
 face(b,LineString([(x0,z0),(x1,z1)]).buffer(width/2,cap_style=2),y0,y1,mat,label)
def slab(b,points,thick,mat,label):
 vert=list(points)+[(x,y,z-thick) for x,y,z in points]
 b.add(vert,[[0,1,2,3],[7,6,5,4],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]],mat,label)
 if mat==TILE:
  b.parts[-1]['texcoords']=[[.24*x+.105*y+.48,.173*y+.087*x+.23*z]for x,y,z in vert]
def glazed(b,left,right,lo,hi,y,columns,n_transoms,label):
 prism_edges=np.linspace(left,right,columns+1)
 for index,(a,c) in enumerate(zip(prism_edges,prism_edges[1:])):
  material=PALE_GLASS if label=='Broad gable' and index in (0,2,3) else GLASS
  rect(b,a,c,lo,hi,y+.024,y+.06,material,label+' recessed glass')
 for xx in [left,right]:rect(b,xx-.026,xx+.026,lo-.025,hi+.025,y-.035,y+.08,FRAME,label+' outer jamb')
 for zz in [lo,hi]:rect(b,left-.035,right+.035,zz-.032,zz+.032,y-.038,y+.074,FRAME,label+' rails')
 for x in np.linspace(left,right,columns+1)[1:-1]:
  rect(b,x-.018,x+.018,lo,hi,y-.026,y+.045,CAME,label+' mullions')
 for z in n_transoms:
  rect(b,left,right,z-.011,z+.011,y-.022,y+.043,CAME,label+' glazing bars')
def tiled(b,x0,x1,y0,y1,zfunc,n_rows,n_cols,axis,far,exclude,label):
 def put(a,c,d,e,zadd,h,mat):
  p=[(a,d),(c,d),(c,e),(a,e)]
  slab(b,[(x,y,zfunc(x,y)+zadd)for x,y in p],h,mat,label)
 # All courses follow the pitch. Individual overlapping tiles leave visible butt edges at near range.
 for row in range(n_rows):
  for col in range(n_cols):
   if axis=='y':
    a=x0+(x1-x0)*col/n_cols;c=x0+(x1-x0)*(col+1)/n_cols
    d=y0+(y1-y0)*row/n_rows;e=y0+(y1-y0)*(row+1)/n_rows
   else:
    a=x0+(x1-x0)*row/n_rows;c=x0+(x1-x0)*(row+1)/n_rows
    d=y0+(y1-y0)*col/n_cols;e=y0+(y1-y0)*(col+1)/n_cols
   if exclude and exclude(a,c,d,e):continue
   inset=.004 if not far else .003
   put(a+inset,c-inset,d,e-inset,.023+.004*((row*5+col*11)%3),.042,TILE)
def roof(b,spec,far,label):
 cx,half,y,base,eave,apex,depth=spec
 xl=cx-half-.066;xr=cx+half+.066;yf=y-.157;yb=y+depth
 for side,xa,xb in [(0,xl,cx),(1,cx,xr)]:
  zf=lambda x,yy:apex+.071-abs(x-cx)*(apex-eave)/half
  slab(b,[(xa,yf,zf(xa,yf)),(xb,yf,zf(xb,yf)),(xb,yb,zf(xb,yb)),(xa,yb,zf(xa,yb))],.078,DARK,label+' roof boarding')
  tiled(b,xa,xb,yf-.011,yb,zf,4 if far else 7,5 if far else 10,'x',far,None,label+' overlapping clay tiles')
  band(b,xa,zf(xa,yf)-.041,xb,zf(xb,yf)-.041,yf-.025,yf+.07,.076,STRIPE,label+' red verge')
  band(b,xa,zf(xa,yf)+.012,xb,zf(xb,yf)+.012,yf-.04,yf+.04,.026,EDGE,label+' upper verge lip')
 b.tube([(cx,yf-.03,apex+.105),(cx,yb,apex+.105)],.045,TILE,7 if far else 12,label+' ridge tile')
 # The tubular ridge needs a longitudinal UV instead of relying on a guessed map.
 part=b.parts[-1];part['texcoords']=[[.5+(x-cx)*4,(yy-yf)/depth]for x,yy,z in part['vertices']]
def gable(b,spec,far,big):
 cx,half,y,base,eave,apex,depth=spec;left=cx-half;right=cx+half
 label='Broad gable' if big else 'Narrow dormer'
 opening=(cx-half*.74,cx+half*.74,base+(.336 if big else .093),eave-.134)
 a,c,l,h=opening
 outline=Polygon([(left,base),(right,base),(right,eave),(cx,apex),(left,eave)])
 face(b,outline.difference(box(a,l,c,h)),y,y+.185,PLASTER,label+' face with cut opening')
 face(b,outline,y+depth-.045,y+depth,PLASTER,label+' rear section cut')
 for side,x in [(-1,left),(1,right)]:
  rect(b,x-.031,x+.031,base,eave+.009,y-.023,y+.059,STRIPE,label+' side band')
  rect(b,x-.04,x+.04,base,eave,y+.14,y+depth,PLASTER,label+' return wall')
  if big:
   for distance in [.22,.50]:
    face_x=x+side*.044
    rect(b,face_x-.015,face_x+.015,base+.015,eave-.02,y+distance,y+distance+.061,STRIPE,'Raised vertical band on gable return')
 rect(b,left-.035,right+.035,base-.051,base+.022,y-.092,y+.19,CAP if big else FRAME,label+' projecting sill')
 glazed(b,a,c,l,h,y+.105,5 if big else 3,[l+.74*(h-l)],label)
 # Slender darker marks show beneath the five-light gable sill in the side photograph.
 if big:
  for k in range(6):
   x=a+(c-a)*k/5
   rect(b,x-.019,x+.019,base+.063,l-.036,y-.018,y+.044,STRIPE,'Lower red panels')
 for x,z in [(cx,apex-.09),(cx-.34*half,eave+.25*(apex-eave))]:
  band(b,x,eave+.018,x,z,y-.019,y+.026,.039,STRIPE,label+' peak upright')
 band(b,cx-.64*half,eave+.23*(apex-eave),cx-.3*half,eave+.028,y-.019,y+.029,.046,STRIPE,label+' upper diagonal')
 # The shadow line just above the glass is a distinct projecting shallow awning.
 yf=y-.278 if big else y-.205
 slab(b,[(a-.09,yf,h+.045),(c+.09,yf,h+.045),(c+.09,y+.021,h+.193),(a-.09,y+.021,h+.193)],.044,DARK,label+' shallow projecting window hood')
 for x in np.linspace(a+.08,c-.08,4 if big else 3):
  b.tube([(x,y-.01,h-.038),(x,yf+.057,h+.013)],.009,METAL,5 if far else 9,label+' small hood brackets')
 roof(b,spec,far,label)
def add_building(b,far=False):
 texture()
 # This is the section of larger roof in front of and between the two projections.
 slope=lambda x,y:.349+.89*y
 xs=[-2.58,SMALL[0]-SMALL[1]-.035,SMALL[0]+SMALL[1]+.035,LARGE[0]-LARGE[1]-.045]
 ys=[-.04,SMALL[2]+.054,1.81]
 for i,(a,c) in enumerate(zip(xs,xs[1:])):
  for j,(d,e) in enumerate(zip(ys,ys[1:])):
   if (i,j)==(1,1):continue
   slab(b,[(a,d,slope(a,d)),(c,d,slope(c,d)),(c,e,slope(c,e)),(a,e,slope(a,e))],.073,ROOF,'Main tiled roof undercourse')
   cols=max(2,int((c-a)/(.36 if far else .19)))
   rows=max(2,int((e-d)/(.29 if far else .146)))
   tiled(b,a,c,d,e,slope,rows,cols,'y',far,None,'Main pitch tile courses')
 rect(b,xs[0],xs[-1],.035,.284,-.013,.255,PLASTER,'Short wall band under the main roof')
 b.tube([(xs[0],-.081,.283),(xs[-1],-.081,.283)],.04,GUTTER,7 if far else 12,'Main rearward roof eave gutter')
 gable(b,SMALL,far,False)
 gable(b,LARGE,far,True)
