"""Check stone courses, true grille interstices, arch rails, door plates and wall coping."""
import numpy as np
from street_gate import *
def test(tri,names,hit):
 rows=[]
 def front(label,x,z,mat):
  o=np.array([x,-2.0,z]);v=np.array([0,1.,0]);r=hit(tri,names,o,v);m=r[0] if r else None
  assert m in mat,(label,x,z,m,mat)
  rows.append(dict(label=label,material=m,point=r[1]if r else None))
 for i,x in enumerate(CENTRES):
  for dx in [-.186,-.105,.113,.197]:
   for n,(low,high) in enumerate(zip(BOUNDARIES,BOUNDARIES[1:])):
    front('Stone block '+str(n),x+dx,(low+high)*.5,[FOOT if n<2 else LIME])
   for j in range(1,len(BOUNDARIES)-1):front('Recessed horizontal bed',x+dx,BOUNDARIES[j]+.007,[JOINT])
   front('Raised upper abacus',x+dx,2.249,[EDGE])
  for dx in [-.135,-.07,.11]:front('Finial block',x+dx,2.534,[TOP])
 for x in BARS:
  if abs(x)<.002:continue
  front('Iron upper bar',x,1.73,[IRON_EDGE]);front('Iron rib below rail',x,1.03,[IRON_EDGE])
  front('Curved gate head',x,crown(x),[IRON_EDGE])
 for a,c in zip(BARS,BARS[1:]):
  x=.5*(a+c)
  if abs(x)<.026:continue
  front('Open light between iron bars',x,1.727,[None]);front('Recessed iron bottom leaf',x,1.24,[IRON]);front('Transverse gate rail',x,1.538,[IRON_EDGE])
 for x in [-1.74,-1.60,-1.36,-1.18,1.18,1.29]:
  front('Garden brick facing',x,1.223,[RED,MORTAR]);front('Wall coping',x,1.887,[STONE_CAP])
 for dx,dz in [(-.066,-.033),(-.053,.031),(.058,-.021)]:front('Green number plate',CENTRES[0]+dx,1.735+dz,[PLAQUE])
 return rows
