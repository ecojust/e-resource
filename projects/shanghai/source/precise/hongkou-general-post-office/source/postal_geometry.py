"""Original General Post Office geometric vocabulary; author east/north/up metres.

Only closed-prism/export primitives come from the vendored generic helper.
Column profiles, copper crown, sculpture silhouettes and clock are original
parameterized interpretations, not surveyed ornament or third-party meshes.
"""
import math
import numpy as np
from shapely.geometry import Polygon,Point,LineString,box
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
from common.photo_architecture import Facade


def transform_plan(points,center,tangent=(1,0),fluted=True):
 t=np.asarray(tangent,float);n=np.array([t[1],-t[0]])
 return Polygon([np.asarray(center)+t*u+n*v for u,v in points])


def loft(builder,polygons,heights,material,label):
 points=[list(p.exterior.coords)[:-1] for p in polygons]
 if len(set(map(len,points)))!=1:raise ValueError('loft loops differ')
 # Keep identical direction and correspondence on all rings.
 if polygons[0].exterior.is_ccw is False:points=[list(reversed(x))for x in points]
 n=len(points[0]);v=[(x,y,float(z) if np.isscalar(z) else float(z[j])) for ring,z in zip(points,heights) for j,(x,y) in enumerate(ring)]
 f=[]
 for level,reverse in [(0,True),(len(points)-1,False)]:
  lookup={tuple(q):level*n+j for j,q in enumerate(points[level])}
  for tri in constrained_delaunay_triangles(Polygon(points[level])).geoms:
   ring=list(orient(tri,sign=1.).exterior.coords)[:3]
   indices=tuple(lookup[tuple(q)] for q in ring);f.append(tuple(reversed(indices)) if reverse else indices)
 for k in range(len(points)-1):
  for j in range(n):a=k*n+j;c=k*n+(j+1)%n;f.append((a,c,c+n,a+n))
 builder.add(v,f,material,label)


def fluted_column(b,center,bottom,top,r=.55,lod=False,label='fluted giant column',tangent=(1,0),fluted=True):
 h=top-bottom;segments=32 if lod else 64;flutes=16
 profile=[(bottom,r*1.35,0),(bottom+.17,r*1.35,0),(bottom+.28,r*1.1,0),(bottom+.43,r,.075),(top-.78,r*.87,.075),(top-.68,r*1.02,0),(top-.28,r*1.22,0),(top-.14,r*1.30,0),(top,r*1.30,0)]
 v=[]
 for z,radius,depth in profile:
  for j in range(segments):
   a=j*math.tau/segments;rr=radius*(1-(depth if fluted else 0)*(.5+.5*math.cos(a*flutes)))
   v.append((center[0]+rr*math.cos(a),center[1]+rr*math.sin(a),z))
 faces=[tuple(reversed(range(segments))),tuple((len(profile)-1)*segments+j for j in range(segments))]
 for k in range(len(profile)-1):
  for j in range(segments):a=k*segments+j;c=k*segments+(j+1)%segments;faces.append((a,c,c+segments,a+segments))
 b.add(v,faces,'dressed limestone',label)
 tt=np.array([*tangent,0.]);nn=np.array([tt[1],-tt[0],0.]);b.box([*center,top-.08],[r*2.85,r*2.85,.16],'dressed limestone',basis=[tt,nn,[0,0,1]],label=label+' capital abacus')
 if not lod:
  for a in np.arange(8)*math.tau/8:
   p=np.array([*center,top-.55]);rad=np.array([math.cos(a),math.sin(a),0]);side=np.array([-math.sin(a),math.cos(a),0]);
   tip=p+rad*(r*1.14)+np.array([0,0,.20]);base=p+rad*(r*.91)+np.array([0,0,-.12]);w=.13
   b.add([base-side*w,base+side*w,tip+side*.06,tip-side*.06,p+rad*(r*.84)+np.array([0,0,.12])],[(0,1,2,3),(0,4,1),(1,4,2),(2,4,3),(3,4,0)],'dressed limestone',label+' simplified capital leaf')


def sphere(b,center,scale,material,label,lod=False):
 # Ellipsoid with actual pole vertices: all components closed and nondegenerate.
 seg=8 if lod else 12;rings=5 if lod else 8;v=[(center[0],center[1],center[2]-scale[2])]
 for k in range(1,rings):
  phi=-math.pi/2+k*math.pi/rings
  for j in range(seg):
   a=j*math.tau/seg;v.append((center[0]+scale[0]*math.cos(phi)*math.cos(a),center[1]+scale[1]*math.cos(phi)*math.sin(a),center[2]+scale[2]*math.sin(phi)))
 v.append((center[0],center[1],center[2]+scale[2]));top=len(v)-1;f=[]
 for j in range(seg):f.append((0,1+(j+1)%seg,1+j));f.append((top,1+(rings-2)*seg+j,1+(rings-2)*seg+(j+1)%seg))
 for k in range(rings-2):
  for j in range(seg):a=1+k*seg+j;c=1+k*seg+(j+1)%seg;f.append((a,c,c+seg,a+seg))
 b.add(v,f,material,label)


def statue_group(b,center,tangent,z,lod=False,label='three figure copper statuary'):
 t=np.asarray([*tangent,0.]);n=np.array([t[1],-t[0],0.]);c=np.array([*center,z]);mat='verdigris bronze'
 def p(u,v,h):return c+t*u+n*v+np.array([0,0,h])
 def ell(u,v,h,s,name):sphere(b,p(u,v,h),s,mat,label+'/'+name,lod)
 # Two reclining figures and a centrally seated draped figure; facial details
 # are deliberately generalized and cannot authenticate the historic casts.
 for j,u in enumerate([-1.45,0,1.45]):
  central=j==1;torso=1.34 if central else .91
  ell(u,0,torso,(.42,.26,.60 if central else .44),'torso')
  ell(u+(.10 if j==0 else -.08 if j==2 else 0),.01,torso+.76,(.25,.24,.31),'head')
  ell(u,.02,torso+.95,(.27,.25,.13),'hair silhouette')
  for side in [-1,1]:
   shoulder=p(u+side*.37,.0,torso+.35);elbow=p(u+side*.55,.12,torso-.12);hand=p(u+side*.40,.43,torso-.34)
   b.tube([shoulder,elbow,hand],.12,mat,6 if lod else 10,label+'/bent arm')
  if central:
   # Folded seated skirt and two bent knees, no solid triangular screen.
   for side in [-1,1]:
    b.tube([p(u+side*.20,0,.85),p(u+side*.27,.52,.65),p(u+side*.25,.59,.12)],.24,mat,8 if lod else 12,label+'/draped seated leg')
   if not lod:
    for du in np.linspace(-.4,.4,7):b.tube([p(du,.26,1.15),p(du*.8,.53,.65),p(du*.9,.65,.10)],.035,mat,5,label+'/skirt fold')
  else:
   outward=-1 if j==0 else 1
   for side in [-1,1]:b.tube([p(u+side*.17,.04,.55),p(u+outward*.45,.45,.4),p(u+outward*.87,.70,.15)],.17,mat,7 if lod else 10,label+'/reclining bent leg')
   ell(u+outward*.91,.77,.13,(.27,.19,.10),'foot')
 # Two groups are distinguishable by symbolic low props; approximate, not
 # detailed reproduction of the original locomotive/telegraph/ship objects.
 if 'east' in label:
  b.box(p(2.64,.28,.42),(.72,.58,.72),mat,[t,n,[0,0,1]],label+'/locomotive block')
  f=Facade(b,p(2.25,.60,0)[:2],p(3.04,.60,0)[:2],label+'/locomotive round front')
  f.prism(Point(0,z+.5).buffer(.24,resolution=10),-.05,.10,mat,'engine circle')
 else:
  b.tube([p(-2.6,.18,.25),p(-2.6,.18,1.75)],.055,mat,6,label+'/symbolic staff')
  b.tube([p(-2.78,.18,1.45),p(-2.43,.18,1.65)],.055,mat,6,label+'/staff crosspiece')


def clock_face(f,z,r=1.8,lod=False):
 b=f.builder;segments=24 if lod else 48
 face=Point(0,z).buffer(r,resolution=segments//4)
 f.prism(face,.07,.13,'ivory clock face','single southeast clock dial')
 for rad,w,depth,mat in [(r+.43,.17,.12,'dressed limestone'),(r+.19,.11,.20,'dark bronze'),(r-.08,.045,.22,'dark bronze')]:
  ring=Point(0,z).buffer(rad,resolution=segments//4).difference(Point(0,z).buffer(rad-w,resolution=segments//4));f.prism(ring,.10,depth+.11,mat,'circular clock moulding')
 # Roman numeral strokes are generated as geometry from I,V,X tokens.
 numerals=['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']
 for i,text in enumerate(numerals):
  a=i*math.tau/12;cx=math.sin(a)*r*.77;cz=z+math.cos(a)*r*.77
  cw=.13;gap=.045;total=len(text)*(cw+gap)-gap
  paths=[]
  for j,ch in enumerate(text):
   x=cx-total/2+j*(cw+gap)
   strokes={'I':[[(x+cw/2,cz-.14),(x+cw/2,cz+.14)]],'V':[[(x,cz+.14),(x+cw/2,cz-.14),(x+cw,cz+.14)]],'X':[[(x,cz+.14),(x+cw,cz-.14)],[(x,cz-.14),(x+cw,cz+.14)]]}[ch]
   for s in strokes:f.prism(LineString(s).buffer(.025,cap_style=2,join_style=2),.135,.18,'dark bronze','Roman clock numeral')
 for angle,length,width in [(-math.pi/3,r*.56,.065),(math.pi*.27,r*.68,.045)]:
  end=(math.sin(angle)*length,z+math.cos(angle)*length);f.prism(LineString([(0,z),end]).buffer(width,cap_style=2),.19,.23,'dark bronze','fixed illustrative clock hand')
 f.prism(Point(0,z).buffer(.13,resolution=10),.20,.26,'dark bronze','clock hand hub')


def curve_square_points(radius,amount=1.,segments=10):
 # Four corners with concave sides, matching the inward-curving tower canopy.
 points=[]
 for side in range(4):
  for k in range(segments):
   u=-radius+2*radius*k/segments;v=radius-amount*(1-(u/radius)**2)
   if side==0:p=(u,v)
   elif side==1:p=(v,-u)
   elif side==2:p=(-u,-v)
   else:p=(-v,u)
   points.append(p)
 return points
