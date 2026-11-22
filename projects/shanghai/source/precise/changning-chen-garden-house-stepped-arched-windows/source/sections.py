"""Measure the frames, recessed panes, open arch surround, spiral surface and plinths in the delivered GLBs."""
import numpy as np
from stair_windows import *
def test(tri,names,hit):
 rows=[]
 def front(label,x,z,allowed):
  res=hit(tri,names,np.array([x,-2,z]),np.array([0,1,0]));mat=res[0] if res else None
  assert mat in allowed,(label,x,z,mat,allowed);rows.append(dict(label=label,material=mat,point=res[1]if res else None))
 for i,(x,bot) in enumerate(zip(CENTERS,LEVELS)):
  sp=bot+SPRING;rr=R-.032
  for off in [-.182,-.077,.079,.186]:
   for frac in [.072,.188,.319,.435,.591,.674,.817,.924]:
    front('Recessed rectangular glass',x+off,bot+frac*SPRING,[GLASS])
  for z in np.linspace(bot+.14,sp-.18,8):front('Centre glazing bar',x,z,[CAME])
  for frac in [.25,.50,.75]:
   z=bot+.040+(SPRING-.069)*frac
   for off in [-.17,.07,.18]:front('Horizontal steel line',x+off,z,[CAME])
  for off in [-.19,-.095,.135,.17]:
   front('Arch main transom',x+off,sp,[GREY]);front('Sill',x+off,bot-.042,[SILL])
  for off in [-.18,0,.19]:
   front('Fanlight crown',x+off,sp+np.sqrt((R-.032)**2-off**2),[GREY])
  for t in [pi*.315,pi*.685]:
   for step in [.54,.79]:front('Radial fanlight bar',x+rr*step*np.cos(t),sp+.010+step*((rr-.012)*np.sin(t)-.010),[CAME])
  for t in [pi*.2,pi*.40,pi*.55,pi*.8]:
   front('Glass between radial bars',x+.197*np.cos(t),sp+.197*np.sin(t),[FAN])
  for off in [-.30,-.19,.08,.245]:
   front('Outside arch head',x+off,sp+np.sqrt((R+.023)**2-off**2),[TRIM])
 for i in [0,1]:
  x=(CENTERS[i]+CENTERS[i+1])/2;z0=LEVELS[i+1]-.027;z1=LEVELS[i]+SPRING+.017;lo=z0+.054;hi=z1-.111
  for n in range(2,21):
   u=n/23;theta=pi/2+u*2*pi*TURNS
   # Determine the frontmost of the two twisting strands before locating the probe.
   if np.sin(theta)>0:theta+=pi
   xat=x+(.0615-.005*u)*np.cos(theta)
   front('Twisting raised rib',xat,lo+u*(hi-lo),[RIDGE,WEATHER])
  for dx in [-.110,-.046,0,.061,.108]:
   front('Square plinth',x+dx,z0-.058,[CAP]);front('Capital abacus',x+dx,z1+.009,[CAP_HI])
 for x in [-1.37,-.53,.45,1.39]:
  for z in [.105,3.92]:front('Stucco ground',x,z,[PLASTER])
 return rows
