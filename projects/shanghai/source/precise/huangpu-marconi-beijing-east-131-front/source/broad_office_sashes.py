"""Four outward-opening leaves in the neighboring broad bay, as photographed in 2017."""
import math
import numpy as np
from scipy.optimize import minimize_scalar
from marconi_photo_plane import pixel,on_wall
from marconi_street_fabric import WOOD,GLASS,DARK,block,plain_window
# Source is 2017_front-metres at 70px per metre. This annotated close-up starts at (139,346), enlarged 2x.
def marked(x,y):return pixel([-11.5+(139+x/2)/70,0,21.5-(346+y/2)/70])
depth=.91
panes=[{'jambs':[58,242],'head':83,'transom':193,'sill':428,'free':[[(99,160),(103,408)],[(146,181),(145,411)]]},
       {'jambs':[455,631],'head':84,'transom':190,'sill':421,'free':[[(518,161),(517,399)],[(546,195),(548,414)]]}]
def layout():
 out=[]
 for n,row in enumerate(panes):
  low0=on_wall(*marked(row['jambs'][0],row['sill']),depth);high1=on_wall(*marked(row['jambs'][1],row['transom']),depth)
  low,high=low0[2],high1[2];l,r=low0[0],high1[0];w=(r-l)/2
  for j,free in enumerate(row['free']):
   sign=1 if j==0 else -1;x=l if j==0 else r
   def pt(a,h):return np.array([x+sign*w*math.cos(a),depth-w*math.sin(a),h])
   target=[np.array(marked(*q))for q in free]
   def residual(a):return np.mean([np.sum((np.array(pixel(pt(a,h)))-obs)**2)for h,obs in zip((high,low),target)])
   rr=minimize_scalar(residual,bounds=(.015,2.6),method='bounded');angle=float(rr.x)
   out.append(dict(bay=n+1,leaf=j+1,hinge=[x,depth],direction=(sign*math.cos(angle),-math.sin(angle)),width=w,angle_deg=math.degrees(angle),z=[low,high],free_witnesses=free,rms_px=math.sqrt(rr.fun),frame=[l,r]))
 return out
def add_broad_sashes(b):
 for k,row in enumerate(panes):
  r=layout()[k*2];l,rt=r['frame'];low,high=r['z'];top=on_wall(*marked(row['jambs'][0],row['head']),depth)[2]
  block(b,l-.11,rt+.11,1.25,1.29,low-.15,top+.09,DARK,'Wide bay | dark interior behind four open leaves')
  plain_window(b,(l,high,rt,top),depth,3,1,'Wide bay | three-light transom')
 for r in layout():
  x,y=r['hinge'];dx,dy=r['direction'];low,high=r['z'];width=r['width'];label='Wide window '+str(r['bay'])+' leaf '+str(r['leaf'])
  def oriented(a,t,z,w,d,h,m,name):
   b.box([x+a*dx-t*dy,y+a*dy+t*dx,z],[w,d,h],m,basis=[[dx,dy,0],[-dy,dx,0],[0,0,1]],label=label+' | '+name)
  for a in (0.,width):oriented(a,0,(low+high)/2,.041,.059,high-low,WOOD,'stile')
  for z in np.linspace(low,high,4):
   oriented(width/2,0,z,width+.04,.061,.038,WOOD,'rail')
  for lo,hi in zip(np.linspace(low,high,4)[:-1],np.linspace(low,high,4)[1:]):
   oriented(width/2,.01,(lo+hi)/2,width-.035,.011,hi-lo-.032,GLASS,'glass')
