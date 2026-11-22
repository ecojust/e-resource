"""Compare actual intersections with the relative storey heights, setbacks and fenestration visible in the district photograph."""
import numpy as np
from court_bay import *
def test(mesh,n,hit):
 rows=[]
 def check(x,z,mat,name,depth=None):
  o=np.array([x,-2.,z]);d=np.array([0.,1.,0.]);v=hit(mesh,n,o,d);assert v and v[0] in mat,(name,x,z,v,mat)
  if depth:assert depth[0]<=v[1][1]<=depth[1],(name,v,depth)
  rows.append(dict(label=name,material=v[0],point=v[1]))
 for i,(l,r,y)in enumerate(PANELS):
  open_= [s for s in WINDOWS if s[0]>=l and s[1]<=r]
  for j in range(13):
   z=BASE*(j+.5)/13
   for x in np.linspace(l+.088,r-.077,7):
    if any(a-.12<x<b+.12 and lo-.09<z<hi+.1 for a,b,lo,hi,*_ in open_):continue
    check(x,z,[STONE,LIGHT,DARK,MORTAR],'Grey facing at photographed wall plane',(y-.015,y+.018))
  for z in (2.245,2.72,3.69,4.08,4.37):
   for x in np.linspace(l+.087,r-.077,5):
    if any(a-.13<x<b+.13 and lo-.09<z<hi+.09 for a,b,lo,hi,*_ in open_):continue
    check(x,z,[PLASTER],'Upper stucco at photographed wall plane',(y-.011,y+.001))
  for x in np.linspace(l+.14,r-.14,4):
   for z,m in [(BASE-.017,CAP),(HEIGHT-.202,SOFFIT),(HEIGHT-.074,CAP),(HEIGHT-.016,CAP)]:check(x,z,[m],'Stone and cornice return')
 for l,r,z,t,y,kind in WINDOWS:
  for x in (l,(r+l)/2,r):check(x,z-.035,[DRIP],'Dark sill front')
  check(l,(z+t)/2,[CAP],'Pale jamb')
  check((l+r)/2,t+.015,[CAP],'Pale window head')
  if kind=='upper':
   for x in [l+.21,r-.21]:
    check(x,z+.23,[GLASS],'Darker lower pane');check(x,t-.23,[SKY],'Light upper pane')
   check((l+r)/2,t-.24,[FRAME],'Central upper frame')
  if kind=='narrow':check((l+r)/2,t-.24,[GLASS],'Narrow dark ground-floor window')
  if kind=='low':
   for x in [l+.18,l+.49,r-.23]:check(x,z+.35,[CURTAIN],'Curtained low window')
 return rows
