"""Probe window recesses, shaft flutes, capital tablets and both continuous borders of the spandrel."""
import numpy as np
from court_bay import *
def test(mesh,names,hit):
 out=[]
 def ray(x,y,m,label,lo=None,hi=None):
  q=hit(mesh,names,np.array([X(x),-2.,Z(y)]),np.array([0.,1.,0.]));assert q and q[0] in m,(x,y,m,label,q)
  if lo is not None:assert lo<=q[1][1]<=hi,(x,y,lo,hi,q)
  out.append(dict(label=label,material=q[0],point=q[1]))
 for c in (66,426):
  for y in (226,293,386,522,679,760):
   for dx in (-28,-20,-12,-4,4,12,20,28):ray(c+dx,y,[STONE],'Bottom of recessed pilaster flute',-.105,-.092)
   for dx in (-32,-24,-16,-8,0,8,16,24,32):ray(c+dx,y,[STONE],'Shaft face between flutes',-.135,-.13)
  for dx in (-18,-6,6,18):ray(c+dx,169,[SHADOW],'Short groove in hanging neck tablet')
  for dx in (-12,0,12):ray(c+dx,163,[STONE],'Raised face between short grooves')
  for sig in (-1,1):
   for t in (.175,.375,.575,.775,.947):
    x=c+sig*(38+(15-12*t)*cos(-pi/2-t*2.12*pi));y=106+(15-12*t)*sin(-pi/2-t*2.12*pi)
    ray(x,y,[STONE],'Round volute curl',-.225,-.184)
  for dx in (-45,-26,0,25,45):ray(c+dx,54,[STONE],'Projecting abacus')
 for y0,y1,mat in [(79,265,LOW),(455,711,UP)]:
  for j in range(4):
   x=127+(364-127)*(j+.5)/4
   for t in (.18,.50,.80):ray(x,y0+t*(y1-y0),[SKY,GREY,LIGHT],'Glazed lights behind sash',.116,.12)
  for i in range(1,4):ray(127+(364-127)*i/4,y0+(y1-y0)*.61,[mat],'Window upright')
 for y in [299+i*7.6 for i in range(5)]+[381+i*8.2 for i in range(5)]:
  for x in [136,166,205,247,297,333,359]:ray(x,y-.9,[STONE],'Continuous raised border fillet',-.059,-.053)
 ray(241,357,[DEEP],'Inset square socket',.043,.047)
 for x in (230.5,256):ray(x,357,[STONE],'Raised square surround',-.055,-.041)
 for sig in (-1,1):
  for ix in range(3):
   x=242+sig*(28+31*ix)
   for delta in (0,5.3):
    x0=x+sig*(delta+8.5)
    if 126<x0<365 and not 225<x0<261:ray(x0,357.5,[STONE],'Chevrons in the window spandrel',-.077,-.057)
 return out
