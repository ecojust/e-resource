"""The ground-floor triple light beside the south portico, from the dated oblique and frontal photographs."""
from pathlib import Path
from math import sin,cos,pi
import numpy as np
from shapely.geometry import box,Polygon
from PIL import Image
HERE=Path(__file__).resolve().parent
WALL='Soft grey scored stucco';LIM='Ivory pilaster stone';CAP='Pale dressed cornice';SHADE='Moulding recess';FRAME='Blackened steel';GLASS='Muted green glass';GLASS2='Green-blue return glass';SHIELD='Shield relief';LEAF='Pale carved foliage';STEM='Leaf ridge'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(WALL,[.91,.91,.88],.95),(LIM,[.81,.82,.74],.93),(CAP,[.86,.86,.79],.83),(SHADE,[.57,.59,.55],.94),(FRAME,[.075,.090,.081],.57),(GLASS,[.29,.40,.39],.29),(GLASS2,[.24,.35,.35],.28),(SHIELD,[.88,.87,.78],.87),(LEAF,[.80,.80,.70],.91),(STEM,[.91,.91,.82],.85)]}
def X(u):return (u-351)*.0082
def Z(v):return (400-v)*.0082
OPEN=[(160,235),(277,426),(471,550)]
def tex():
 p=HERE/'lime-stucco.png'
 if not p.exists():
  rng=np.random.default_rng(864);a=rng.normal(224,3,(144,192));rgb=np.stack([a,a+.3,a-1.5],axis=2);Image.fromarray(np.uint8(np.clip(rgb,0,255))).quantize(72).save(p)
 PALETTE[WALL]['texture']=str(p)
def element(b,l,r,top,bottom,y0,y1,mat,label):
 b.box(((X(l)+X(r))/2,(y0+y1)/2,(Z(top)+Z(bottom))/2),((r-l)*.0082,y1-y0,(bottom-top)*.0082),mat,label=label)
def coat(b,geom,front,back,mat,label):
 b.prism(geom,-back,-front,lambda x,z,d:(x,-d,z),mat,label)
def relieflobe(b,uv,vec,size,front,height,mat,label,steps):
 # A raised almond-shaped leaf with a distinct central vein and pointed ends.
 u,v=uv;dx,dy=vec;norm=np.hypot(dx,dy);nx,ny=-dy/norm,dx/norm;verts=[];faces=[]
 for i in range(steps+1):
  t=i/steps;s=max(.005,sin(pi*t));half=s*size
  for side,y in [(-1,front),(0,front-height*s),(1,front)]:
   verts.append((X(u+dx*t+side*half*nx),y,Z(v+dy*t+side*half*ny)))
 for i in range(steps):
  q=i*3;faces.extend([[q,q+3,q+4,q+1],[q+1,q+4,q+5,q+2]])
 b.add(verts,faces,mat,label)
def shieldshape(b,far):
 # A pear-shaped tablet with a convex face, tapering to a pointed lower tip.
 n=20 if far else 38;data=[(17,.09),(20,.42),(25,.74),(34,1),(44,.93),(54,.65),(62,.31),(65,.05)];verts=[];faces=[]
 for v,w in data:
  for i in range(n+1):
   a=i/n*pi;verts.append((X(351+12*w*cos(a)),-.110-.061*w*sin(a),Z(v)))
 for j in range(len(data)-1):
  for i in range(n):q=j*(n+1)+i;faces.append([q,q+1,q+n+2,q+n+1])
 b.add(verts,faces,SHIELD,'Convex central shield')
 for sign in (-1,1):
  for j,(x,v,dx,dy) in enumerate([(2,65,8,-4),(8,60,7,-7),(13,52,6,-8),(15,44,5,-9),(15,34,2,-9),(12,26,-3,-8),(8,20,-4,-5)]):
   relieflobe(b,(351+sign*x,v),(sign*dx,dy),4.2,-.103,.042,LEAF,'Shield leaf chain '+str(sign),4 if far else 8)
  for j,(x,y) in enumerate([(16,27),(24,24),(34,24),(44,24),(54,25)]):
   relieflobe(b,(351+sign*x,y+5),(sign*10,-5+(j%2)*4),3.65,-.095,.031,LEAF,'Outward leaf spray '+str(sign),4 if far else 7)
  relieflobe(b,(351+sign*12,33),(sign*47,-7),1.42,-.109,.019,STEM,'Upper leaf stalk '+str(sign),5 if far else 10)
 for sign in (-1,1):relieflobe(b,(351,24),(sign*4,-11),3.2,-.121,.037,LEAF,'Shield crest',4 if far else 7)
def add_building(b,far=False):
 tex();panel=box(X(126),Z(416),X(574),Z(1))
 for l,r in OPEN:panel=panel.difference(box(X(l),Z(379),X(r),Z(78)))
 coat(b,panel,.001,.32,WALL,'Recessed triple-window wall')
 pts=b.parts[-1]['vertices'];b.parts[-1]['texcoords']=[[(x-X(126))/(X(574)-X(126)),(Z(1)-z)/(Z(1)-Z(416))]for x,y,z in pts]
 for ix,(l,r) in enumerate(OPEN):
  name=['Left sidelights','Paired center casements','Right sidelights'][ix]
  element(b,l,r,77,380,.14,.153,GLASS if ix!=2 else GLASS2,name+' glass')
  for u in (l+2,r-2):element(b,u-2,u+2,77,379,.065,.15,FRAME,name+' outer stiles')
  for v in (80,376):element(b,l,r,v-2,v+2,.062,.145,FRAME,name+' outer rails')
  element(b,l,r,172,181,.055,.147,FRAME,name+' transom')
  # The central paired steel casements carry a heavier meeting stile.
  divs=2 if ix==1 else 1
  for u in [l+(r-l)*j/(2*divs)for j in range(1,2*divs)]:
   width=3.15 if ix==1 and abs(u-(l+r)/2)<1 else 1.40
   element(b,u-width,u+width,82,375,.076,.143,FRAME,name+' vertical divisions')
  for j in range(divs*2):
   x0=l+(r-l)*j/(divs*2)+3.8;x1=l+(r-l)*(j+1)/(divs*2)-3.8
   for z in (159,309):element(b,x0,x1,z-.62,z+.62,.101,.148,FRAME,name+' slender inner rails')
 for l,r in [(140,160),(235,277),(426,471),(549,570)]:
  mid=(l+r)/2;w=(r-l)*.65
  element(b,mid-w/2,mid+w/2,99,367,-.074,.025,LIM,'Flat pilaster shaft')
  element(b,mid-w*.41,mid+w*.41,105,363,-.085,-.073,CAP,'Shallow pilaster face')
  for y0,y1,rat,y in [(78,83,.96,-.114),(83,89,.89,-.104),(89,98,.76,-.09),(98,101,.70,-.084),(365,371,.72,-.095),(371,379,.94,-.116),(379,384,1,-.122)]:
   element(b,mid-(r-l)*rat/2,mid+(r-l)*rat/2,y0,y1,y,.045,CAP,'Pilaster capital' if y1<120 else 'Pilaster foot')
 for top,bottom,x0,x1,y,mat,n in [(66,77,140,570,-.04,SHADE,'Head shadow'),(56,65,140,570,-.060,CAP,'Window head'),(35,55,140,570,-.062,LIM,'Plaque face'),(28,34,140,570,-.086,CAP,'Upper stringcourse'),(14,27,140,570,-.071,LIM,'Cornice frieze'),(7,14,136,573,-.113,CAP,'Cornice lip'),(383,390,137,571,-.131,CAP,'Sill lip'),(390,399,140,570,-.094,LIM,'Sill fascia')]:
  element(b,x0,x1,top,bottom,y,.034,mat,n)
 shieldshape(b,far)
