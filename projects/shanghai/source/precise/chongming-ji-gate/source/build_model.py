"""Ji Gate candidate after museum text and 2005 photographs. Metres, z up. MIT."""
import argparse,json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point,box
from architecture import Architecture,Builder,PALETTE,Facade
ID='chongming-ji-gate'
class Gate(Architecture):
 def __init__(self,lod=False):
  self.b=Builder(PALETTE);self.lod=lod;self.features=[]
  self.hx=9.25;self.hy=4.05
 def roofpoint(self,side,s,t):
  x=(2*s-1)*self.hx;y=side*t*self.hy
  return np.array([x,y,5.15+2.35*(1-t)**1.35+.10*t**3*(abs(x)/self.hx)**10])
 def roofs(self):
  # The visible roof is continuous: the text's height differences concern beams.
  for side in [-1,1]:
   n=6 if self.lod else 18;nu=12 if self.lod else 36
   vs=[self.roofpoint(side,s,t) for t in np.linspace(0,1,n+1) for s in np.linspace(0,1,nu+1)]
   faces=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(n) for i in range(nu)]
   label=f'continuous-roof/side-{side}'
   self.shell(vs,faces,.085,'roof underlay',label+'/closed-shell')
   count=32 if self.lod else 86
   for i in range(count):
    s=(i+.5)/count
    pts=[self.roofpoint(side,s,t)+[0,0,.045] for t in np.linspace(0,1,7 if self.lod else 19)]
    self.b.tube(pts,.061,f'grey tile {i%3}',6 if self.lod else 10,label+f'/cap-course-{i}')
    out=pts[-1]-pts[-2];out/=np.linalg.norm(out)
    self.b.tube([pts[-1]-out*.01,pts[-1]+out*.05],.077,'ridge ceramic',8,label+f'/tile-end-{i}')
    if not self.lod:
     for k,t in enumerate(np.linspace(.12,.96,8)):
      p=self.roofpoint(side,s,t)+[0,0,.045];d=self.roofpoint(side,s,t+.001)-self.roofpoint(side,s,t-.001);d/=np.linalg.norm(d)
      self.b.tube([p-d*.011,p+d*.011],.065,'grey tile 2',8,label+f'/tile-lap-{i}-{k}')
   self.b.tube([self.roofpoint(side,s,1)-[0,0,.07] for s in np.linspace(0,1,25)],.08,'aged red brown timber',8,label+'/fascia')
   for i,s in enumerate(np.linspace(.02,.98,20 if self.lod else 42)):
    self.b.tube([self.roofpoint(side,s,t)-[0,0,.17] for t in np.linspace(.02,1,12)],.055,'aged red brown timber',8,label+f'/rafter-{i}')
   for x in [-self.hx,self.hx]:
    self.b.tube([self.roofpoint(side,(x/self.hx+1)/2,t)+[0,0,.09] for t in np.linspace(0,1,19)],.10,'ridge ceramic',8,label+'/gable-edge')
   self.mark('roof',side=side,cap_courses=count)
  # Simplified perforated ridge strip observed from the courtyard, without carving claims.
  shape=box(-9.25,7.57,9.25,7.94)
  for x in np.linspace(-9.02,9.02,60):shape=shape.difference(Point(float(x),7.76).buffer(.09,quad_segs=4 if self.lod else 8))
  f=Facade(self.b,[-9.25,0],[9.25,0],'ridge')
  f.prism(shape,-.13,.13,'ridge ceramic','estimated-circular-openwork')
  self.box((0,0,7.54),(18.5,.34,.12),'ridge ceramic','ridge-bottom-band')
  self.box((0,0,7.97),(18.5,.30,.06),'ridge ceramic','ridge-cap')
  # Side gables follow the actual curved roof underside, hidden from reference view.
  for x in [-8.55,8.55]:
   f=Facade(self.b,[x,-3.1] if x>0 else [x,3.1],[x,3.1] if x>0 else [x,-3.1],'estimated-side-gable')
   profile=Polygon([(-3.1,4.9),(3.1,4.9)]+[(y,self.roofpoint(1,(x/self.hx+1)/2,abs(y)/self.hy)[2]-.085) for y in np.linspace(3.1,-3.1,41)])
   f.prism(profile,-.12,.05,'white lime plaster','curved-gable-infill')
 def doorbay(self,f,center):
  for j in range(4):
   u=center+(j-1.5)*.86
   f.box(u,2.35,.84,4.25,.12,0,'aged red brown timber','solid-red-door-leaf')
   for z,h in [(1.0,1.26),(3.0,2.30)]:
    f.box(u,z,.66,h,.025,.073,'dark timber','recessed-door-panel')
    for du in [-.33,.33]:f.box(u+du,z,.035,h,.035,.095,'worn timber edges','door-panel-bead')
    for zz in [z-h/2,z+h/2]:f.box(u,zz,.66,.035,.035,.095,'worn timber edges','door-panel-bead')
 def walls(self):
  # Low common plinth only: no invented high terrace or bridge.
  self.box((0,0,.10),(17.5,6.6,.20),'granite base','documentary-envelope-endpoints-inferred')
  for side in [-1,1]:
   f=self.facade(8.55,3.1,0 if side<0 else 2,'front' if side<0 else 'estimated-rear')
   # Five bays: centre passage, two red door bays, two white outer bays.
   for center in [-7.15,7.15]:
    f.box(center,2.45,2.8,4.5,.20,0,'white lime plaster','outer-bay-plaster')
    f.box(center,.36,2.8,.32,.24,.02,'granite base','outer-bay-base')
   for center in [-3.8,3.8]:self.doorbay(f,center)
   f.box(0,4.78,11.4,.38,.34,0,'aged red brown timber','higher-central-three-bay-beam')
   for center in [-7.15,7.15]:f.box(center,4.55,2.8,.30,.30,0,'aged red brown timber','lower-outer-bay-beam')
   for x in [-8.55,-5.7,-1.9,1.9,5.7,8.55]:
    height=5.0 if abs(x)<6 else 4.82
    self.b.lathe((x,side*3.1),[(.2,.23),(.35,.25),(.5,.20)],'granite base',12,'column-foot')
    self.b.lathe((x,side*3.1),[(.48,.18),(height,.16)],'aged red brown timber',12,'timber-column')
   roofheight=self.roofpoint(side,.5,3.1/self.hy)[2]-.085
   f.box(0,(4.9+roofheight)/2,17.1,roofheight-4.9,.18,0,'dark timber','under-eave-closure')
  for edge in [1,3]:
   f=self.facade(8.55,3.1,edge,'estimated-side-wall');f.wall(.2,4.95,[],.20,'white lime plaster')
  # Keep the central passage genuinely open through the building.
  for x in [-1.85,1.85]:
   self.box((x,0,2.35),(.14,6.2,4.3),'dark timber','estimated-passage-side-closure')
   self.box((x+(-.10 if x>0 else .10),-1.5,2.32),(.12,2.9,4.24),'aged red brown timber','estimated-open-door-leaf')
  for y in [-2.7,0,2.7]:
   z=self.roofpoint(1,.5,abs(y)/self.hy)[2]-.28
   self.b.tube([(-8.6,y,z),(8.6,y,z)],.12,'aged red brown timber',12,'roof-underside-purlin')
  # Photo-observed blue plaque and warm outline; original calligraphy omitted.
  self.box((0,-3.32,4.45),(.68,.11,.92),'blue plaque','unlettered-blue-plaque')
  for x in [-.37,.37]:self.box((x,-3.39,4.45),(.055,.055,1.02),'gilt lettering','plaque-edge')
  for z in [3.94,4.96]:self.box((0,-3.39,z),(.79,.055,.055),'gilt lettering','plaque-edge')
  self.mark('five_bays',central_passage_clear_width_m=3.38,plaque_calligraphy_omitted=True)
 def finish(self):
  self.walls();self.roofs()
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(vol)>1e-10,p['label']
   if vol<0:p['triangles']=[(a,c,b) for a,b,c in t]
  return self
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 m=Gate(a.lod).finish();role='lod' if a.lod else 'raw'
 r=m.b.save(a.out/f'{ID}-{role}.glb',metadata={'name':'崇明学宫戟门','status':'2005 photo / museum text guided candidate; not map registered','documented':'Five bays; 17.5 x 6.6 x 8 m; middle three internal beams higher','observed':'Continuous grey tiled roof, open centre, red side doors, white outer bays, blue plaque and red rafters','estimated':'Dimensions endpoints, roof section, hidden faces, door subdivisions, ridge motifs','omitted':'Pool, bridge, trees, adjacent buildings, exact calligraphy/carvings, interiors beyond visible passage'})
 (a.out/f'{role}-features.json').write_text(json.dumps(m.features,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
