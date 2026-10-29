"""Lingxing Gate CENTRAL portal, 2005-photo-guided partial candidate. MIT, z-up metres."""
import argparse,json,math
from pathlib import Path
import numpy as np
from common.photo_architecture import Builder
ID='chongming-lingxing-gate'
PALETTE={
 'granite':{'color':[.47,.49,.43],'roughness':.96},
 'granite relief':{'color':[.54,.56,.50],'roughness':.94},
 'granite shadow':{'color':[.40,.42,.37],'roughness':.98},
 'red wood':{'color':[.22,.034,.021],'roughness':.66},
 'red wood edge':{'color':[.30,.052,.033],'roughness':.67},
 'dark red recess':{'color':[.12,.018,.012],'roughness':.82},
 'iron hinge':{'color':[.10,.11,.10],'roughness':.80,'metallic':.35}}
class Portal:
 def __init__(self,lod=False):self.b=Builder(PALETTE);self.lod=lod;self.features=[]
 def box(self,c,s,mat,label):self.b.box(c,s,mat,label=label)
 def stone(self):
  # Museum gives central opening dimensions, interpreted here as clear span/rise.
  # Ground plane is z=0. The photo crops the feet: no fabricated historic plinth.
  for sign in [-1,1]:
   x=sign*1.925
   # Lower piers are near-square; chamfered corners remain solid.
   n=8;cross=[(-.21,-.25),(.21,-.25),(.25,-.21),(.25,.21),(.21,.25),(-.21,.25),(-.25,.21),(-.25,-.21)]
   vs=[(x+u,y,z) for z in [0,4.42] for u,y in cross]
   faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
   self.b.add(vs,faces,'granite',f'central-pier-{sign}')
   self.box((x,0,4.39),(.54,.54,.10),'granite shadow','collar')
   # Rounded upper stone shaft; profile and relief are estimates, no dragon claim.
   self.b.lathe((x,0),[(4.44,.25),(5.74,.25),(5.82,.23),(5.85,.18)],'granite',16 if self.lod else 32,'estimated-carved-post-top')
   if not self.lod:
    self.clouds(x,sign)
   else:
    for z in [4.65,5.02,5.39,5.66]:self.spiral(x,0,z,.12,sign,10)
  self.box((0,0,4.00),(3.35,.48,.80),'granite','lintel-unlettered')
  # Original lower panel is bounded by stone mouldings, modeled as shallow relief.
  self.box((0,-.249,3.80),(3.20,.025,.29),'granite shadow','lower-panel-inset-tone')
  for z in [3.635,3.965]:self.box((0,-.274,z),(3.29,.045,.045),'granite relief','lintel-panel-horizontal-moulding')
  for x in [-1.6225,1.6225]:self.box((x,-.274,3.80),(.045,.045,.33),'granite relief','lintel-panel-vertical-moulding')
  self.box((0,-.255,3.62),(3.38,.05,.04),'granite shadow','lintel-drip-edge')
 def spiral(self,x,theta,z,r,sign,n):
  # A relief tube follows a cloud-like spiral on the curved stone surface.
  pts=[]
  for t in np.linspace(0,1,n):
   a=t*math.tau*1.35;rr=r*(1-t*.85);u=theta+sign*rr*math.cos(a)/.268;zz=z+rr*math.sin(a)
   pts.append((x+.268*math.sin(u),-.268*math.cos(u),zz))
  self.b.tube(pts,.018 if self.lod else .021,'granite relief',6 if self.lod else 8,'stylized-cloud-scroll')
 def clouds(self,x,sign):
  for theta in [-.85,0,.85]:
   for j,z in enumerate([4.65,5.02,5.39,5.66]):self.spiral(x,theta,z,.12 if j<3 else .10,sign*(-1 if j%2 else 1),30)
  for phase in [-.35,.35]:
   pts=[]
   for t in np.linspace(0,1,45):
    a=phase+.48*math.sin(t*math.tau*1.5)
    pts.append((x+.264*math.sin(a),-.264*math.cos(a),4.52+t*1.18))
   self.b.tube(pts,.025,'granite relief',8,'stylized-cloud-stem')
 def door(self,sign,angle):
  # Partly open leaves preserve the observed asymmetry. Exact swing is unmeasured.
  origin=np.array([sign*1.65,.04,0.]);u=np.array([-sign*math.cos(angle),math.sin(angle),0.]);normal=np.array([-u[1],u[0],0.]);up=np.array([0,0,1.]);w=1.57
  def block(a,z,width,height,depth,material,label,d=0):
   self.b.box(origin+u*a+up*z+normal*d,(width,depth,height),material,basis=[u,normal,up],label=label)
  for a in [.065,w-.065]:block(a,1.84,.13,3.44,.13,'red wood','door-stile')
  for z,h in [(.18,.16),(1.19,.10),(2.97,.11),(3.48,.12)]:block(w/2,z,w,h,.13,'red wood','door-rail')
  block(w/2,3.225,w-.26,.40,.10,'red wood','door-head-board')
  block(w/2,3.225,w-.38,.28,.025,'dark red recess','door-head-recess',-.064)
  for z in [3.085,3.365]:block(w/2,z,w-.35,.025,.03,'red wood edge','door-head-bead',-.083)
  for a in [.175,w-.175]:block(a,3.225,.025,.28,.03,'red wood edge','door-head-bead',-.083)
  # 2021 supplemental view shows solid lower boards; position remains 2005-inspired.
  block(w/2,.70,w-.26,1.0,.10,'red wood','supplementary-lower-board')
  block(w/2,.70,w-.40,.76,.025,'dark red recess','estimated-lower-panel',-.064)
  for z in [.32,1.08]:block(w/2,z,w-.37,.025,.03,'red wood edge','lower-panel-bead',-.083)
  for a in [.185,w-.185]:block(a,.70,.025,.76,.03,'red wood edge','lower-panel-bead',-.083)
  for a in np.linspace(.24,w-.24,8):block(float(a),2.04,.035,1.67,.07,'red wood edge','vertical-open-slat')
  for z in [.55,2.65]:
   pt=origin+[0,0,z]
   self.b.tube([pt-[0,0,.10],pt+[0,0,.10]],.045,'iron hinge',8,'estimated-hinge-pin')
  self.features.append({'kind':'open_door_leaf','side':sign,'angle_degrees':math.degrees(angle),'width_m':w,'vertical_bars':8,'door_bottom_reference':'2021 supplement; detail estimated'})
 def finish(self):
  self.stone();self.door(-1,math.radians(18));self.door(1,math.radians(67))
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(vol)>1e-10,p['label']
   if vol<0:p['triangles']=[(a,c,b) for a,b,c in t]
  return self
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 m=Portal(a.lod).finish();role='lod' if a.lod else 'raw'
 r=m.b.save(a.out/f'{ID}-{role}.glb',metadata={'name':'崇明学宫棂星门中央石门框与门扇','scope':'Central portal only; two lateral gates omitted','status':'2005 and 2021 photos / museum text guided partial candidate; not map registered','documented':'Central opening width 3.35 m, height 3.6 m; tall stone frame with cloud ornament','estimated':'Opening endpoints, overall height 5.85 m, pier section, door angles/bars and lower panel subdivisions','omitted':'Side gates, adjoining wall, lions, original inscription, exact dragon/carved motifs, courtyard'})
 (a.out/f'{role}-features.json').write_text(json.dumps(m.features,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
