"""Two rendered gables in the district's Tangshan Village photograph."""
from pathlib import Path
from shapely.geometry import Polygon,box,LineString
from profile_tools import BRICK,cb,slab,bricks_uv
IRON='Blue grey window timber';GLASS='Muted blue glass';VERGE='Deep green painted verge';UNDER='Pale gutter edge';TILE='Dark fired pantiles';LIGHT='Weathered tiles';SILL='Stone sill';MOULD='Ochre ridge ornament'
rgb={BRICK:(255,255,255),IRON:(78,89,90),GLASS:(95,119,124),VERGE:(73,91,77),UNDER:(214,205,180),TILE:(119,105,93),LIGHT:(149,132,113),SILL:(142,132,120),MOULD:(121,90,71)}
PALETTE={k:{'color':[(q/255)**2.2 for q in c],'roughness':.83}for k,c in rgb.items()}
PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))
# Fronts and separate roofs. The smaller left gable is set behind the higher right one.
GABLES=[('Left lower gable',-2.01,1.10,2.03,3.38,.78,.25,.93,2.38),('Right upper gable',.43,1.50,2.92,4.59,0,.40,1.96,3.26)]
def profile(c):
 # Relative spans follow the photograph. The rising left verge disappears under a
 # shallow clipped head. The main bargeboards break outward at their feet.
 if c<0:return [(-1.,0.),(-.84,.03),(-.39,.95),(-.12,.99),(.41,1.),(1.,.79)]
 return [(-1.,0.),(-.79,.045),(-.72,.22),(0.,1.),(.73,.22),(.81,.045),(1.,0.)]
def roof(x,c,w,e,t):
 import numpy as np
 u=(x-c)/w
 return e+(t-e)*float(np.interp(u,*zip(*profile(c))))
def model(b,lod=False):
 for name,c,w,e,t,y,half,low,high in GABLES:
  rim=[(c+u*w,e+h*(t-e))for u,h in profile(c)];wall=Polygon([(c-w,0),(c+w,0),*reversed(rim)])
  holes=box(c-half,low,c+half,high)
  if y==0:holes=holes.union(box(c-.42,.02,c+.42,1.05))
  slab(b,wall.difference(holes),y,y+.25,BRICK,name+' painted render')
  ranges=[(half,low,high)]
  if y==0:ranges.append((.42,.02,1.05))
  for j,(r,z0,z1)in enumerate(ranges):
   x0=c-r;x1=c+r;label=name+' window '+str(j+1)
   cb(b,x0,x1,y+.138,y+.155,z0,z1,GLASS,label+' glass')
   for x in [x0+.022,c,x1-.022]:cb(b,x-.017,x+.017,y+.074,y+.145,z0,z1,IRON,label+' sash')
   splits=9 if y==0 else 4
   bar_top=z0+.65*(z1-z0) if y==0 and j==0 else z1-.035
   for i in range(1,splits):
    x=x0+(x1-x0)*i/splits;cb(b,x-.010,x+.010,y+.055,y+.129,z0+.056,bar_top,IRON,label+' close bars')
   for z in ([z0+.023,bar_top,z1-.023] if y==0 and j==0 else [z0+.023,z1-.023]):cb(b,x0,x1,y+.046,y+.143,z-.017,z+.017,IRON,label+' rails')
   cb(b,x0-.066,x1+.066,y-.056,y+.142,z0-.052,z0+.008,SILL,label+' projecting sill')
  for (ax,az),(bx,bz) in zip(rim,rim[1:]):
   width=.19 if y==0 else .13
   slab(b,Polygon([(ax,az+.03),(bx,bz+.03),(bx,bz-width),(ax,az-width)]),y-.077,y+.22,VERGE,name+' jointed bargeboard')
   slab(b,Polygon([(ax,az-width),(bx,bz-width),(bx,bz-width-.045),(ax,az-width-.045)]),y-.068,y+.081,UNDER,name+' pale edge below the board')
   steps=max(1,round((bx-ax)/.125))
   for k in range(steps):
    xa=ax+(bx-ax)*k/steps;xb=ax+(bx-ax)*(k+1)/steps;za=roof(xa,c,w,e,t)+.063;zb=roof(xb,c,w,e,t)+.063
    tile=Polygon([(xa,za),(xb,zb),(xb,zb-.050),(xa,za-.062)])
    pieces=5 if lod else 10
    for j in range(pieces):
     v=y-.070+j*1.65/pieces;slab(b,tile,v+.001,v+1.65/pieces-.001,TILE if (k+j)%5 else LIGHT,name+' short tile courses')
  if y==0:
   for sign in (-1,1):
    pipe=LineString([(c+sign*w,e-.16),(c+sign*w*.69,e-.58),(c+sign*w*.68,.00)]).buffer(.026,join_style=2)
    slab(b,pipe,y-.072,y-.008,UNDER,name+' sloping rainwater pipe')
  for x in (c-w+.031,c+w-.031):cb(b,x-.026,x+.026,y-.034,y+.027,.00,e-.09,UNDER,name+' narrow drip at outer edge')
  if y==0:
   for zz,rr in [(3.76,.038),(3.86,.063),(3.96,.042)]:
    slab(b,Polygon([(c,zz+rr),(c+rr*.65,zz),(c,zz-rr),(c-rr*.65,zz)]),y-.043,y+.006,MOULD,name+' small apex ornament')
 bricks_uv(b)
