"""Dacheng Hall exterior candidate, local x east/y north/z up. Original geometry MIT."""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from architecture import Architecture,Builder,PALETTE,Facade
ID='chongming-dacheng-hall'
class Hall(Architecture):
 def __init__(self,lod=False):
  self.b=Builder(PALETTE);self.lod=lod;self.features=[]
  self.hx=11.9;self.hy=9.8;self.lowerInner=(9.0,6.7)
  self.ux=10.0;self.uy=7.7;self.ridge=5.8;self.breaky=3.5
 def lower(self,field,s,t):
  u=2*s-1;ix,iy=self.lowerInner
  if field<2:x=u*(ix+(self.hx-ix)*t);y=(-1 if field==0 else 1)*(iy+(self.hy-iy)*t)
  else:x=(-1 if field==2 else 1)*(ix+(self.hx-ix)*t);y=u*(iy+(self.hy-iy)*t)
  return np.array([x,y,6.15+1.85*(1-t)**1.55+.58*t**3*abs(u)**8])
 def upper(self,field,s,t):
  u=2*s-1
  if field<2:
   y=self.uy*t;w=self.ridge+(self.ux-self.ridge)*max(0,(y-self.breaky)/(self.uy-self.breaky));x=u*w;y*=(-1 if field==0 else 1)
  else:
   x=(-1 if field==2 else 1)*(self.ridge+(self.ux-self.ridge)*t);w=self.breaky+(self.uy-self.breaky)*t;y=u*w
  q=abs(y)/self.uy if field<2 else w/self.uy
  return np.array([x,y,9.0+4.6*(1-q)**1.55+.70*(abs(x)/self.ux)**8*(abs(y)/self.uy)**8])
 def roofs(self):
  for tier,fn in [('lower',self.lower),('upper',self.upper)]:
   for field in range(4):self.roof_patch(lambda s,t:fn(field,s,t),tier,field)
  base=self.upper(0,.5,self.breaky/self.uy)[2]-.075
  for side in [-1,1]:
   a=[side*self.ridge,-self.breaky];b=[side*self.ridge,self.breaky]
   f=Facade(self.b,a if side>0 else b,b if side>0 else a,'estimated-gable')
   outline=Polygon([(-self.breaky,base),(self.breaky,base)]+[(y,self.upper(0,.5,abs(y)/self.uy)[2]-.075) for y in np.linspace(self.breaky,-self.breaky,33)])
   f.prism(outline,-.07,.01,'dark timber','gable-infill')
  for z in [13.72,14.02,14.28]:self.box((0,0,z),(11.6,.24,.085),'ridge ceramic','ridge-horizontal-band')
  for x in np.arange(-5.65,5.7,.25 if self.lod else .14):
   self.box((x,0,13.86),(.045,.16,.24),'ridge ceramic','ridge-openwork')
   self.box((x,0,14.15),(.035,.15,.20),'ridge ceramic','ridge-upper-openwork')
  for sign in [-1,1]:
   self.b.tube([(sign*(5.8+dx),0,z) for dx,z in [(0,13.65),(.13,14.1),(.15,14.5),(.30,14.9),(.24,15.24)]],.06,'ridge ceramic',8,'estimated-ridge-finial')
 def column(self,x,y):
  self.b.lathe((x,y),[(1,.32),(1.10,.34),(1.28,.28),(1.35,.25)],'granite base',16,'column-stone-foot')
  self.b.lathe((x,y),[(1.3,.25),(5.6,.22),(6.05,.21)],'aged red brown timber',16,'tapered-column')
 def walls(self):
  self.box((0,0,.5),(21.3,17.3,1),'granite base','documented-hall-footprint-interpretation')
  # The platform is documented; its attachment and stair layout are inferred.
  self.box((0,-13.435,.5),(16.2,9.57,1),'granite base','documented-moon-platform')
  for i in range(7):
   length=(7-i)*.30;self.box((0,-18.22-length/2,(i+1)/14),(5,length,(i+1)/7),'granite base','estimated-platform-step')
  # Ramp slab reserves the photographed central carved flight; carving omitted.
  self.b.prism(Polygon([(-20.32,0),(-18.22,1),(-18.22,.85),(-20.32,-.08)]),-.70,.70,lambda y,z,d:(d,y,z),'granite base','central-carved-ramp-unornamented')
  # Eight front posts documented, with unequal outer spans observed in photo.
  for y in [-8.35,8.35]:
   for x in [-10.3,-8.35,-5.4,-1.8,1.8,5.4,8.35,10.3]:self.column(x,y)
  for x in [-10.3,10.3]:
   for y in [-4.18,0,4.18]:self.column(x,y)
  for edge in range(4):
   f=self.facade(10.3,8.35,edge,'gallery')
   f.box(0,5.75,f.length,.40,.34,0,'aged red brown timber','gallery-tie')
   for u in np.arange(-f.length/2+.25,f.length/2,.68):
    for j in range(3):f.box(float(u),6.0+j*.12,.28+j*.18,.10,.40+j*.11,0,'aged red brown timber','estimated-bracket')
  front=self.facade(8.35,6.7,0,'front-five-bays')
  for center in [-6.68,-3.34,0,3.34,6.68]:
   for j in range(4):
    u=center+(j-1.5)*.79
    front.box(u,1.68,.75,1.36,.13,0,'aged red brown timber','door-lower-board')
    front.box(u,1.68,.60,1.15,.03,.08,'dark timber','inset-panel')
    for dx in [-.30,.30]:front.box(u+dx,1.68,.025,1.15,.03,.105,'worn timber edges','panel-border')
    for z in [1.105,2.255]:front.box(u,z,.60,.025,.03,.105,'worn timber edges','panel-border')
    self.lattice(front,u,2.40,.75,2.65,'front-lattice',cols=6,rows=16)
   front.box(center,5.25,3.25,.30,.24,0,'aged red brown timber','door-head')
  for x in [-8.35,-5.01,-1.67,1.67,5.01,8.35]:front.box(x,3.15,.16,4.3,.25,.02,'aged red brown timber','bay-post')
  for edge in [1,2,3]:
   f=self.facade(8.35,6.7,edge,'unobserved-wall');f.wall(1,7.95,[],.10,'white lime plaster')
   f.box(0,1.20,f.length,.40,.28,-.10,'granite base','wall-base')
  for edge in range(4):
   f=self.facade(9,6.7,edge,'intertier-band');f.wall(7.95,9.0,[],.18,'dark timber')
   f.box(0,8.75,f.length,.16,.24,.04,'worn timber edges','intertier-beam')
  # Front plaque retained without invented calligraphy.
  plaque=self.facade(9,7.75,0,'plaque');plaque.box(0,8.35,.80,1.0,.10,.15,'dark timber','unlettered-plaque')
  for x in [-.40,.40]:plaque.box(x,8.35,.025,1.04,.04,.22,'gilt lettering','plaque-border')
  for z in [7.83,8.87]:plaque.box(0,z,.80,.025,.04,.22,'gilt lettering','plaque-border')
  # Open perimeter railing, interrupted for the central stair.
  for side in [-1,1]:
   for x in np.linspace(2.7,7.95,5):
    self.box((side*x,-18.1,1.52),(.20,.22,1.04),'granite base','platform-railing-post')
   for x in np.linspace(3.35,7.30,4):
    self.box((side*x,-18.1,1.43),(1.15,.12,.40),'granite base','platform-railing-panel')
    self.box((side*x,-18.1,1.96),(1.20,.15,.10),'granite base','platform-railing-open-slot')
 def finish(self):
  # Adjacent roof patches must agree at their shared hip, before tessellation.
  for t in np.linspace(0,1,101):
   q=(self.breaky+(self.uy-self.breaky)*t)/self.uy
   for field,side,s in [(0,3,0),(0,2,0),(1,3,1),(1,2,1)]:
    u=1 if side==3 else 0
    assert np.allclose(self.upper(field,u,q),self.upper(side,s,t),atol=1e-10)
  self.walls();self.roofs()
  seen=set();parts=[]
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);volume=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(volume)>1e-10,p['label']
   if volume<0:p['triangles']=[(a,c,b) for a,b,c in t]
   key=(p['material'],v.astype('<f4').tobytes(),np.asarray(p['triangles']).tobytes())
   if key not in seen:seen.add(key);parts.append(p)
  self.b.parts=parts;return self
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 model=Hall(a.lod).finish();role='lod' if a.lod else 'raw'
 r=model.b.save(a.out/f'{ID}-{role}.glb',metadata={'name':'崇明学宫大成殿外观候选','status':'Unregistered; not accepted photo reconstruction','dimensions':'21.3 x 17.3 x 15.3m documentary constraints; wall/eave endpoint inferred','omitted':'Statues, inscriptions, exact carvings, interior, surveyed alignment','unobserved':'Rear and sides estimated; not photo verified'})
 (a.out/f'{role}-features.json').write_text(json.dumps(model.features,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
