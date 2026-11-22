"""Model the indented portion of the elevation identified in the district's dance-campus courtyard photograph."""
from pathlib import Path
from math import sin,cos,pi
from shapely.geometry import box
from shapely.ops import unary_union
import numpy as np
from PIL import Image
ID='changning-dance-campus-recessed-court-window-bay'
PLASTER='Light warm-grey plaster'; JOINT='Recessed stucco band'; MORTAR='Deep blue-grey joints'; STONE='Cool grey facing'; LIGHT='Silver grey facing'; DARK='Weathered grey block'
CAP='Warm pale moulded surround';SOFFIT='Grey shadow below projected mouldings';FRAME='Deep painted window frame';DRIP='Shaded sill arris';GLASS='Shadowed lower glass';SKY='Light reflected in high panes';CURTAIN='Curtains behind the low window';RAIL='Dark internal bead'
PALETTE={n:dict(color=c,roughness=r)for n,c,r in [(PLASTER,[1,1,1],.94),(JOINT,[.65,.62,.57],.98),(MORTAR,[.35,.382,.405],.96),(STONE,[1,1,1],.94),(LIGHT,[1,1,.99],.94),(DARK,[.82,.86,.9],.95),(CAP,[.88,.847,.73],.9),(SOFFIT,[.55,.55,.51],.94),(FRAME,[.235,.269,.24],.73),(DRIP,[.35,.36,.32],.89),(GLASS,[.177,.203,.168],.38),(SKY,[.42,.51,.54],.32),(CURTAIN,[.64,.68,.62],.89),(RAIL,[.31,.32,.27],.63)]}
BASE=2.01;HEIGHT=4.77
# At the back of the photograph the grey lower storey changes plane between the two bays.
PANELS=[(-2.05,-.20,.0),(-.20,1.69,.33),(1.69,2.13,.03)]
WINDOWS=[(-1.48,-.64,2.63,3.83,0.,'upper'),(.225,1.065,2.63,3.84,.33,'upper'),(-1.49,-.94,.82,1.69,0.,'narrow'),(-.135,1.48,.335,1.25,.33,'low')]
def texture():
 f=Path(__file__).with_name('stone-and-plaster.png')
 if not f.exists():
  rng=np.random.default_rng(487);w,h=256,224;g=rng.normal(0,1,(h,w));c=np.asarray(Image.fromarray(rng.integers(0,255,(16,21),dtype='u1')).resize((w,h),Image.Resampling.BICUBIC),float)/255-.5
  a=np.array([123,134,143])[None,None,:]+(14*c+7*g)[:,:,None]
  b=np.array([230,218,197])[None,None,:]+(7*c+2.5*g)[:,:,None]
  Image.fromarray(np.clip(np.concatenate([a,b],axis=1),0,255).astype('u1')).quantize(160).save(f)
 for m in (PLASTER,STONE,LIGHT,DARK):PALETTE[m]['texture']=str(f)
def flat(b,profile,a,c,m,label):
 b.prism(profile,-c,-a,lambda x,z,d:(x,-d,z),m,label)
def slab(b,l,r,lo,hi,a,c,m,label):
 if r<=l or hi<=lo:return
 b.box(((l+r)/2,(a+c)/2,(lo+hi)/2),(r-l,c-a,hi-lo),m,label=label)
def coat(b,l,r,front,openings,lower,far):
 boxes=[box(x,z,i,t)for x,i,z,t,y,kind in openings];holes=unary_union(boxes)
 def field(poly,back,body,mat,name):
  geom=poly.difference(holes)
  for sh in getattr(geom,'geoms',[geom]):
   if sh.geom_type!='Polygon' or sh.area<=.00001:continue
   flat(b,sh,front+back,front+body,mat,name)
   if lower and not far and mat in (STONE,LIGHT,DARK) and sh.area>.005:
    inner=sh.buffer(-.004,join_style=2)
    outer=list(sh.exterior.coords)[:-1];core=list(inner.exterior.coords)[:-1]
    if len(outer)==len(core) and len(outer)==4:
     outer=sorted(outer);core=sorted(core)
     order=[0,2,3,1];points=[(outer[i][0],front+back-.0004,outer[i][1])for i in order]+[(core[i][0],front+back-.006,core[i][1])for i in order]
     faces=[[4,5,6,7]]+[[i,(i+1)%4,4+(i+1)%4,4+i]for i in range(4)]
     b.add(points,faces,mat,'Shallow dressed arrises on stone')
 if lower:
  field(box(l,0,r,BASE),.011,.14,MORTAR,'Mortar backing cut at lower windows')
  height=BASE/13;length=.43
  for course in range(13):
   z0=course*height;col=0;a=l-(course%2)*length*.51
   while a<r:
    x0=max(a+.007,l);x1=min(a+length-.007,r-.002)
    if x1>x0:
     mat=(STONE,LIGHT,STONE,DARK,STONE)[(course*11+col*3)%5]
     field(box(x0,z0+.006,x1,z0+height-.006),-.002*(1+(course+col)%3),.018,mat,'Grey ashlar courses')
    a+=length;col+=1
 else:
  field(box(l,BASE,r,HEIGHT),.018,.16,JOINT,'Stucco backing to incised courses')
  for z0,z1 in zip([BASE,2.49,2.94,3.40,3.85,4.30],[2.49,2.94,3.40,3.85,4.30,HEIGHT]):
   field(box(l,z0+.008,r,z1-.008),-.008,.033,PLASTER,'Broad horizontal plaster courses')
def window(b,s,far):
 l,r,z,t,y,kind=s;lwd=.047 if kind=='narrow' else .06
 for x in (l,r):
  slab(b,x-lwd,x+lwd,z-.042,t+.050,y-.067,y+.18,CAP,'Pale raised window reveal')
 for zz in (z,t):slab(b,l-lwd,r+lwd,zz-.045,zz+.047,y-.082,y+.14,CAP,'Window head or sill rim')
 slab(b,l-lwd-.022,r+lwd+.022,z-.060,z-.021,y-.135,y+.05,DRIP,'Projected dark sill lip')
 for x in (l+lwd,r-lwd):slab(b,x-.018,x+.018,z+.04,t-.02,y+.067,y+.117,FRAME,'Dark inset jamb')
 low=z+.035;top=t-.043;left=l+lwd+.014;right=r-lwd-.014
 if kind=='low':
  for j in range(14 if not far else 9):
   parts=14 if not far else 9;a=left+(right-left)*j/parts;e=left+(right-left)*(j+1)/parts
   d=.128 if j%2 else .142
   slab(b,a,e,low+.035,top-.055,y+d,y+d+.014,CURTAIN,'Curtains behind garden window')
  for i in range(1,4):slab(b,left+(right-left)*i/4-.015,left+(right-left)*i/4+.015,low,top,y+.048,y+.085,FRAME,'Low window mullions')
 elif kind=='upper':
  p=(top+low)/2-.035;mid=(left+right)/2
  for x0,x1 in [(left,mid),(mid,right)]:
   slab(b,x0,x1,low,p,y+.157,y+.17,GLASS,'Shaded lower pane')
   slab(b,x0,x1,p,top,y+.155,y+.17,SKY,'Reflected sky in upper pane')
  slab(b,mid-.016,mid+.016,low,top,y+.044,y+.084,FRAME,'Upper sash meeting stile')
  slab(b,left,right,p-.018,p+.018,y+.043,y+.082,RAIL,'Upper opening cross rail')
 else:slab(b,left,right,low,top,y+.153,y+.17,GLASS,'Single narrow lower light')
def add_building(b,far=False):
 texture()
 for l,r,y in PANELS:
  openings=[s for s in WINDOWS if s[0]>=l and s[1]<=r]
  coat(b,l,r,y,openings,True,far);coat(b,l,r,y,openings,False,far)
  slab(b,l,r,BASE-.059,BASE+.038,y-.088,y+.17,CAP,'Continuous lower-storey band')
  slab(b,l,r,HEIGHT-.23,HEIGHT-.113,y-.095,y+.21,SOFFIT,'Stepped cornice shadow')
  slab(b,l-.013,r+.013,HEIGHT-.113,HEIGHT-.042,y-.156,y+.21,CAP,'Deep projecting eave course')
  slab(b,l-.020,r+.020,HEIGHT-.042,HEIGHT+.007,y-.20,y+.23,CAP,'Cornice cover edge')
 for x,depth1,depth2 in [(-.20,0.,.33),(1.69,.03,.33)]:
  for lo,hi,m in [(0,BASE,MORTAR),(BASE,HEIGHT,PLASTER)]:
   slab(b,x-.010,x+.010,lo,hi,depth1,depth2+.044,m,'Recess return between adjacent wall planes')
  for z in [BASE-.059,HEIGHT-.112,HEIGHT-.042]:slab(b,x-.114,x+.113,z,z+.046,depth1-.08,depth2,CAP,'Moulded return across the setback')
 for s in WINDOWS:window(b,s,far)
 # Near level also models the narrow dark band below each projecting cornice separately.
 if not far:
  for l,r,y in PANELS:slab(b,l,r,HEIGHT-.161,HEIGHT-.145,y-.105,y-.087,DRIP,'Fine cornice shadow joint')
 for t in b.parts:
  m=t['material']
  if m in (STONE,LIGHT,DARK,PLASTER):
   off=.525 if m==PLASTER else .025
   t['texcoords']=[[off+.10*(x+2.10)+.019*y,.08+.173*z+.015*y]for x,y,z in t['vertices']]
