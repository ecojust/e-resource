"""The photographed central length of the former Zhou residence's curved garden room."""
from pathlib import Path
from math import sqrt,cos,sin,pi,atan2
import numpy as np
WOOD='Fluted stained timber';RING='Polished column mouldings';FRAME='Cream window stiles';SASH='Thin cream glazing bars';LIGHT='Pale warm glass';COOL='Grey garden reflections';RAIL='Warm grey edge shadow';PLASTER='Buff plaster at window head';HARDWARE='Aged bronze transom fitting'
palette={WOOD:[255,255,255],RING:[143,85,54],FRAME:[205,183,135],SASH:[211,188,135],LIGHT:[210,217,191],COOL:[177,194,176],RAIL:[147,127,91],PLASTER:[205,176,119],HARDWARE:[109,94,63]}
PALETTE={name:dict(color=[(x/255)**2.2 for x in v],roughness=.72)for name,v in palette.items()}
PALETTE[WOOD]['texture']=str(Path(__file__).with_name('stained-timber.png'))
HALF=1.83;RADIUS=6.90;HINGES=[-HALF+i*(2*HALF/4)for i in range(5)];POST_X=1.96
def curve(x):return sqrt(RADIUS**2-x*x)-sqrt(RADIUS**2-HALF**2)
def sash_face(i,x):
 a,b=HINGES[i:i+2];return curve(a)+(curve(b)-curve(a))*(x-a)/(b-a)
def board(b,x0,x1,y0,y1,z0,z1,outside,mat,name):
 # Flat sash on a chord of the bow, with true front and back surfaces.
 verts=[(x0,outside(x0)+y0,z0),(x1,outside(x1)+y0,z0),(x1,outside(x1)+y1,z0),(x0,outside(x0)+y1,z0),(x0,outside(x0)+y0,z1),(x1,outside(x1)+y0,z1),(x1,outside(x1)+y1,z1),(x0,outside(x0)+y1,z1)]
 b.add(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,name)
def spindle(b,cx,cy,profile,n,mat,label,flutes=0):
 verts=[]
 for z,r,depth in profile:
  for i in range(n):
   a=2*pi*i/n;radius=r-depth*(.5+.5*cos(a*flutes)) if flutes else r
   verts.append((cx+radius*cos(a),cy+radius*sin(a),z))
 faces=[tuple(reversed(range(n))),tuple(range(len(verts)-n,len(verts)))]
 for j in range(len(profile)-1):
  for i in range(n):
   k=j*n;h=(i+1)%n;faces.append((k+i,k+h,k+n+h,k+n+i))
 b.add(verts,faces,mat,label)
 if mat==WOOD:
  part=b.parts[-1];rows=[];vs=[];uv=[];original=np.array(part['vertices'])
  for triangle in part['triangles']:
   pts=original[np.asarray(triangle)];u=[atan2(y-cy,x-cx)/(2*pi)+.5 for x,y,z in pts]
   if max(u)-min(u)>.5:u=[v+1 if v<.5 else v for v in u]
   ofs=len(vs);vs.extend(pts.tolist());rows.append([ofs,ofs+1,ofs+2]);uv.extend([(float(v),1-float(z/3.13)) for v,(_,_,z) in zip(u,pts)])
  part.update(vertices=vs,triangles=rows,texcoords=uv)
def model(b,lod=False):
 for i,(x0,x1)in enumerate(zip(HINGES,HINGES[1:])):
  fn=lambda x:sash_face(i,x)
  key='Leaf '+str(i+1)
  for c in range(3):
   xa=x0+(x1-x0)*c/3;xb=x0+(x1-x0)*(c+1)/3
   for row in range(5):
    lo=.03+row*.518;hi=lo+.518
    mat=COOL if row<2 and (c+i+row)%3==0 else LIGHT
    board(b,xa+.008,xb-.008,.034,.048,lo,hi,fn,mat,key+' five rows of glass')
  for x in (x0+.031,x1-.031):board(b,x-.031,x+.031,-.066,.048,0,2.67,fn,FRAME,key+' tall edge stiles')
  for c in (1,2):
   x=x0+c*(x1-x0)/3
   board(b,x-.013,x+.013,-.011,.044,.025,2.62,fn,SASH,key+' slender muntins')
  for j in range(1,5):
   z=.03+j*.518;board(b,x0+.045,x1-.045,-.021,.048,z-.013,z+.013,fn,SASH,key+' horizontal glass bars')
  board(b,x0,x1,-.069,.062,2.615,2.69,fn,FRAME,key+' upper sash rail')
  board(b,x0,x1,-.064,.061,0,.045,fn,FRAME,key+' lower sash rail')
 segments=16 if lod else 42
 for k in range(segments):
  lo=-2.04+4.08*k/segments;hi=-2.04+4.08*(k+1)/segments
  for a,c,d,e,mat,group in [(2.68,3.02,-.08,.13,PLASTER,'Curved head above French windows'),(3.015,3.058,-.13,.14,RAIL,'Curved cornice shadow'),(3.057,3.105,-.155,.14,FRAME,'Upper fillet around room')]:
   board(b,lo,hi,d,e,a,c,curve,mat,group)
 for sign in (-1,1):
  a=sign*POST_X;cy=-.238;name='Left'if sign<0 else'Right';n=88 if lod else 176
  spindle(b,a,cy,[(0,.213,.006),(.12,.214,.010),(2.78,.204,.010),(2.865,.201,0)],n,WOOD,name+' concave flutes continuing through cropped shaft',22)
  spindle(b,a,cy,[(2.835,.204,0),(2.855,.215,0),(2.886,.214,0),(2.894,.222,0)],n//2,RING,name+' neck collar')
  spindle(b,a,cy,[(2.89,.215,0),(2.910,.233,0),(2.944,.252,0),(2.964,.252,0),(2.988,.221,0),(3.015,.220,0),(3.038,.257,0),(3.067,.274,0),(3.098,.272,0),(3.111,.264,0)],n//2,RING,name+' stepped capital and rounded crown')
 board(b,-.145,.145,-.094,-.071,2.82,2.872,curve,HARDWARE,'Narrow fitting above central joint')
