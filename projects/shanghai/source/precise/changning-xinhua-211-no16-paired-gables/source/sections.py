"""Intersect the final meshes to check recessed glass, painted bars, roof courses and shadow gaps."""
import numpy as np
from street_dormers import *
def test(tri,names,hit):
 rows=[]
 def ray(label,origin,direction,allowed):
  h=hit(tri,names,np.array(origin),np.array(direction));m=h[0] if h else None
  assert m in allowed,(label,origin,m,allowed)
  rows.append(dict(label=label,material=m,point=h[1] if h else None))
 for is_big,spec in [(False,SMALL),(True,LARGE)]:
  cx,half,y,base,eave,apex,depth=spec;lo=base+(.336 if is_big else .093);hi=eave-.134;li=cx-half*.74;ri=cx+half*.74
  cols=5 if is_big else 3; centers=np.linspace(li,ri,cols+1)
  for i,(a,c)in enumerate(zip(centers,centers[1:])):
   for z in np.linspace(lo+.07,hi-.1,8):
    if abs(z-(lo+.74*(hi-lo)))>.025: ray('Recessed glass',[(a+c)/2,-2,z],[0,1,0],[PALE_GLASS if is_big and i in (0,2,3) else GLASS])
   ray('Glazing horizontal line',[(a+c)/2,-2,lo+.74*(hi-lo)],[0,1,0],[CAME])
  for x in centers[1:-1]:
   for z in [lo+.11,lo+.32,hi-.25]:ray('Window mullion',[x,-2,z],[0,1,0],[CAME])
  for x in [li+.014,ri-.014]:
   for z in [lo+.03,lo+.19,hi-.12]:ray('Window jamb',[x,-2,z],[0,1,0],[FRAME])
  for x in [cx-half,cx+half]:
   for z in [base+.07,base+.38,eave-.19]:ray('Red vertical stripe',[x,-2,z],[0,1,0],[STRIPE])
  for x in np.linspace(li+.02,ri-.02,7):ray('Projecting hood',[x,-2,hi+.112],[0,1,0],[DARK])
  for x in np.linspace(li+.07,ri-.07,6):ray('Window sill',[x,-2,lo+.016],[0,1,0],[FRAME])
  for x in np.linspace(cx-half*.6,cx+half*.6,6):
   for yy in [y+.332,y+.521]:ray('Gable roof tile',[x,yy,4.],[0,0,-1],[TILE, DARK])
 for x in [-2.49,-2.40,-.43,-.26,.01,.17]:
  for y in [.10,.47,.833,1.371]:ray('Main red-tiled slope',[x,y,4],[0,0,-1],[TILE,ROOF])
 return rows
