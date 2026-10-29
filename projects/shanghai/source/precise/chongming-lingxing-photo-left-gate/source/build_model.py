"""Photo-left Lingxing side gate. 2021 reference, uncertain geographic orientation. MIT."""
import argparse,json,math
from pathlib import Path
import numpy as np
from common.photo_architecture import Builder
ID='chongming-lingxing-photo-left-gate'
PALETTE={
 'weathered stone':{'color':[.49,.48,.42],'roughness':.96},
 'stone raised edge':{'color':[.56,.55,.48],'roughness':.95},
 'stone inset':{'color':[.43,.42,.37],'roughness':.98},
 'red timber':{'color':[.25,.036,.022],'roughness':.72},
 'red timber edge':{'color':[.32,.048,.030],'roughness':.70},
 'red inset':{'color':[.14,.019,.013],'roughness':.85},
 'hinge iron':{'color':[.10,.11,.10],'roughness':.82,'metallic':.3}}
class SideGate:
 def __init__(self,lod=False):self.b=Builder(PALETTE);self.lod=lod;self.features=[]
 def box(self,c,s,material,label):self.b.box(c,s,material,label=label)
 def post(self,x,width,height,label):
  # Small authored chamfers avoid a razor edge; section is estimated from photo.
  r=width/2;c=.025;cross=[(-r+c,-r),(r-c,-r),(r,-r+c),(r,r-c),(r-c,r),(-r+c,r),(-r,r-c),(-r,-r+c)]
  vs=[(x+a,b,z) for z in [0,height] for a,b in cross];n=len(cross)
  faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  self.b.add(vs,faces,'weathered stone',label)
 def stone_frame(self):
  # Historic stone frame follows the 1990s two-tall-post photograph.
  # Door posture follows 2021; this is an explicit mixed-date candidate.
  self.post(-1.34,.38,3.8,'left-outer-stone-pier')
  self.post(1.32,.34,3.94,'right-inner-pier-estimated-section')
  self.box((-1.34,0,3.805),(.41,.41,.07),'stone inset','left-post-collar')
  self.b.lathe((-1.34,0),[(3.84,.19),(4.94,.19),(5.01,.17),(5.04,.12)],'weathered stone',16 if self.lod else 28,'left-tall-rounded-post-top')
  # Historical photograph supports a second tall extension; its carving is unresolved.
  self.b.lathe((1.32,0),[(3.94,.17),(4.96,.17),(5.02,.15),(5.04,.11)],'weathered stone',16 if self.lod else 28,'historic-right-upper-post-plain-estimated')
  for row,z in enumerate([4.03,4.32,4.61,4.84]):
   for theta in ([0] if self.lod else [-.7,0,.7]):
    pts=[]
    for t in np.linspace(0,1,10 if self.lod else 25):
     a=t*math.tau*1.2;rr=.085*(1-t*.82);angle=theta+(-1 if row%2 else 1)*rr*math.cos(a)/.205
     pts.append((-1.34+.205*math.sin(angle),-.205*math.cos(angle),z+rr*math.sin(a)))
    self.b.tube(pts,.016,'stone raised edge',6 if self.lod else 8,'left-post-stylized-cloud-scroll')
  self.box((0,0,3.49),(2.3,.34,.58),'weathered stone','unlettered-side-gate-lintel')
  self.box((0,-.178,3.35),(2.15,.025,.21),'stone inset','lower-lintel-panel')
  for z in [3.225,3.475]:self.box((0,-.198,z),(2.21,.035,.035),'stone raised edge','lintel-horizontal-border')
  for x in [-1.105,1.105]:self.box((x,-.198,3.35),(.035,.035,.25),'stone raised edge','lintel-vertical-border')
  self.features.append({'kind':'historical_two_post_stone_frame','clear_opening_m':[2.3,3.2],'left_top_m':5.04,'right_top_m':5.04,'right_upper_ornament_unresolved':True,'post_heights_estimated':True})
 def door(self,sign,angle_deg):
  # Both leaves appear nearly edge-on. Bar count/panels cannot be read in this view.
  a=math.radians(angle_deg);origin=np.array([sign*1.13,.035,0.]);u=np.array([-sign*math.cos(a),math.sin(a),0.]);n=np.array([-u[1],u[0],0.]);up=np.array([0,0,1.]);w=1.07
  def piece(t,z,width,height,depth,material,label,offset=0):
   self.b.box(origin+u*t+up*z+n*offset,(width,depth,height),material,basis=[u,n,up],label=label)
  for t in [.055,w-.055]:piece(t,1.60,.11,3.04,.11,'red timber','near-open-leaf-stile')
  for z,h in [(.15,.14),(.96,.10),(2.68,.10),(3.055,.13)]:piece(w/2,z,w,h,.11,'red timber','leaf-rail')
  piece(w/2,.56,w-.22,.72,.09,'red timber','estimated-solid-lower-board')
  piece(w/2,.56,w-.34,.54,.02,'red inset','estimated-lower-inset',-.056)
  for z in [.29,.83]:piece(w/2,z,w-.31,.025,.025,'red timber edge','lower-panel-edge',-.07)
  for t in [.155,w-.155]:piece(t,.56,.025,.54,.025,'red timber edge','lower-panel-edge',-.07)
  piece(w/2,2.87,w-.22,.28,.09,'red timber','estimated-head-board')
  for t in np.linspace(.19,w-.19,6):piece(float(t),1.82,.032,1.61,.065,'red timber edge','estimated-vertical-slat')
  for z in [.43,2.43]:
   p=origin+[0,0,z];self.b.tube([p-[0,0,.085],p+[0,0,.085]],.036,'hinge iron',8,'estimated-hinge')
  self.features.append({'kind':'near-open-door','side':sign,'angle_degrees':angle_deg,'width_m':w,'vertical_bars':6,'detail_status':'Unresolved in oblique low-resolution reference; authored approximation'})
 def finish(self):
  self.stone_frame();self.door(-1,82);self.door(1,84)
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(vol)>1e-10,p['label']
   if vol<0:p['triangles']=[(a,c,b) for a,b,c in t]
  return self
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 m=SideGate(a.lod).finish();role='lod' if a.lod else 'raw'
 r=m.b.save(a.out/f'{ID}-{role}.glb',metadata={'name':'崇明学宫棂星门照片左侧门','scope':'Photo-left side portal only; absolute geographic orientation unverified','status':'1990s frame with 2021 open-leaf posture; explicit mixed-date candidate; not map registered','documented':'Side-gate opening 2.3 m wide by 3.2 m high, interpreted as clear dimensions','observed':'Unlettered lintel, two tall post extensions in 1990s photo; 2021 inner upper shaft obscured, two near-open red leaves','estimated':'Post sections/heights, ornament, door angles/bar count/panels, hidden rear surfaces','omitted':'Central gate, opposite side gate, adjoining wall, canopy, access equipment, people, inner upper-post carving, exact carvings and ground'})
 (a.out/f'{role}-features.json').write_text(json.dumps(m.features,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
