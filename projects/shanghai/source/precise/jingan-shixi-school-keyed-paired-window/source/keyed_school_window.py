"""Fayhoo's paired recessed sash in Building 2, Shixi Middle School, photographed 26 December 2015."""
from pathlib import Path
from math import sin, cos, pi
from shapely.geometry import box
from PIL import Image
import numpy as np

ID='jingan-shixi-school-keyed-paired-window'
WALL='Pebbled grey wall';LIMESTONE='Warm pale stone';REVEAL='Inner sloping stone';LIP='Stone sill edge';FRAME='Dark sash';GLASS='Reflected blue glass';DARK='Shaded lower glass';MULLION='Pale central divider'
PALETTE={n:dict(color=c,roughness=r) for n,c,r in [(WALL,[1,1,1],.97),(LIMESTONE,[.70,.68,.60],.91),(REVEAL,[.572,.558,.494],.96),(LIP,[.714,.689,.60],.88),(FRAME,[.11,.14,.139],.65),(GLASS,[.256,.388,.438],.36),(DARK,[.153,.246,.27],.4),(MULLION,[.726,.701,.625],.9)]}
def texture():
 p=Path(__file__).with_name('pebbled-wall.png')
 if not p.exists():
  rng=np.random.default_rng(595);f=rng.random((512,512));c=np.array([157,151,134])[None,None,:]+(f-.5)[:,:,None]*41
  for _ in range(14000):
   x,y=rng.integers(0,510,2);v=rng.uniform(-31,30);c[y:y+2,x:x+2]+=v
  Image.fromarray(c.clip(0,255).astype('u1')).quantize(112).save(p)
 PALETTE[WALL]['texture']=str(p)
def add_building(b,far=False):
 texture()
 def xyz(x,z,d):return x,-d,z
 def part(x0,x1,z0,z1,d0,d1,mat,label):b.prism(box(x0,z0,x1,z1),d0,d1,xyz,mat,label)
 # All sizes are relative to a 215 by 219 pixel excerpt, whose outer sill spans about 148 pixels.
 clear=box(-.665,.36,.665,2.23)
 b.prism(box(-1.17,0,1.17,2.69).difference(clear),-.37,0,xyz,WALL,'Pebbled render around the two leaves')
 frame=box(-.838,.247,.838,2.345).difference(clear)
 b.prism(frame,-.042,.072,xyz,LIMESTONE,'Flat stone head and straight outer frame')
 for hand in [-1,1]:
  for mid in [.638,1.164,1.732]:
   x=.869*hand
   part(x-.044,x+.044,mid-.104,mid+.104,-.015,.052,LIMESTONE,'Three alternate projecting stone keys at each jamb')
 outer=[(-.665,.36),(.665,.36),(.665,2.23),(-.665,2.23)]
 inset=[(-.59,.425),(.59,.425),(.59,2.13),(-.59,2.13)]
 for i in range(4):
  j=(i+1)%4;points=[xyz(*outer[i],.072),xyz(*outer[j],.072),xyz(*inset[j],-.113),xyz(*inset[i],-.113)]
  b.add(points,[(0,1,2,3)],REVEAL,'Splayed face of the four jamb returns')
 part(-.843,.843,.226,.282,.044,.102,LIP,'Projecting sill and thin shadow line')
 for left,right in [(-.59,-.054),(.054,.59)]:
  part(left,right,.425,1.291,-.159,-.151,DARK,'Shaded glass in lower sash')
  part(left,right,1.291,2.13,-.159,-.151,GLASS,'Upper light reflecting the sky')
  for x in (left,(left+right)/2,right):
   thick=.014 if x in (left,right) else .007
   part(x-thick,x+thick,.421,2.132,-.16,-.116,FRAME,'Outer window stile or fine inner muntin')
  for z in (.426,1.29,1.795,2.123):
   thick=.019 if z==1.29 else .011
   part(left,right,z-thick,z+thick,-.162,-.111,FRAME,'Continuous meeting rail or narrow transom')
  for z in (.69,.942):
   part(left,right,z-.004,z+.004,-.148,-.136,FRAME,'Fine subdivisions below meeting rail')
 part(-.050,.050,.374,2.208,-.123,.015,MULLION,'Stone mullion falling between the dark sashes')
 for hand in [-1,1]:
  x=.05*hand;z=[.398,2.176];profile=[(x,.009),(x+.015*hand,-.013),(x+.011*hand,-.06)] if not far else [(x,.009),(x+.011*hand,-.06)]
  b.tube([(a,-d,z[0]) for a,d in profile]+[(profile[-1][0],-profile[-1][1],z[1])],.0055,LIMESTONE,sides=5 if far else 9,label='Narrow bead at the edge of the central mullion')
 for p in b.parts:
  if p['material']==WALL:p['texcoords']=[[(x+.55*y+1.18)/2.61,z/2.69]for x,y,z in p['vertices']]
