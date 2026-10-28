"""Photo-informed Pan Pool and Dengyun Bridge component candidate; MIT.
Local x=east, y=north, z=up. No geographic registration or walk collision.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
from shapely.geometry import Polygon, box
sys.path.insert(0,str(Path(__file__).parent/'common'))
from photo_architecture import Builder

ID='chongming-pan-pool-bridge'
PALETTE={'granite':{'color':[.54,.53,.49],'roughness':.87},
 'granite edges':{'color':[.65,.63,.58],'roughness':.8},
 'granite recess':{'color':[.38,.38,.35],'roughness':.94},
 'pool lining':{'color':[.28,.30,.25],'roughness':.96},
 'water display':{'color':[.09,.24,.19],'roughness':.22,'metallic':.12}}
class PoolBridge(Builder):
 def __init__(self,lod=False):
  super().__init__(PALETTE);self.lod=lod;self.features=[]
 def ball(self,center,radii,label,material='granite edges'):
  n=8 if self.lod else 16; rings=6 if self.lod else 10
  # Distinct poles prevent duplicate vertices and zero-area triangles.
  v=[np.array(center)+[0,0,-radii[2]]]
  for i in range(1,rings):
   a=-math.pi/2+math.pi*i/rings
   for j in range(n):
    t=j*math.tau/n;v.append(np.array(center)+np.array(radii)*[math.cos(a)*math.cos(t),math.cos(a)*math.sin(t),math.sin(a)])
  top=len(v);v.append(np.array(center)+[0,0,radii[2]]);f=[]
  for j in range(n):f.append((0,1+(j+1)%n,1+j));f.append((top,1+(rings-2)*n+j,1+(rings-2)*n+(j+1)%n))
  for i in range(rings-2):
   for j in range(n):
    a=1+i*n+j;b=1+i*n+(j+1)%n;f.append((a,b,b+n,a+n))
  self.add(v,f,material,label)
 def pool(self):
  n=64 if self.lod else 192
  # Half ellipse follows the official half-moon plan; precise curve is estimated.
  pts=[(5.8*math.cos(t),3.08-6.16*math.sin(t)) for t in np.linspace(0,math.pi,n+1)]
  shape=Polygon(pts);outer=shape.buffer(.30,join_style=2)
  self.plan_prism(outer.difference(shape),-2.1,0,'pool lining','retaining wall; official depth, estimated thickness')
  self.plan_prism(shape,-2.16,-2.1,'pool lining','estimated flat basin bed')
  self.plan_prism(shape,-.812,-.8,'water display','illustrative water surface; level unmeasured')
  self.plan_prism(outer.buffer(.07).difference(shape.buffer(-.07)),0,.12,'granite edges','perimeter coping')
  # Architectural railing only on the pool perimeter, interrupted for bridge.
  arc=[(5.97*math.cos(t),3.08-6.33*math.sin(t)) for t in np.linspace(0,math.pi,17)]
  back=[(-5.97+11.94*i/8,3.25) for i in range(9)]
  for curve in [arc,back]:
   for i,(a,b) in enumerate(zip(curve,curve[1:])):
    if min(abs(a[0]),abs(b[0]))<1.38 or a[0]*b[0]<0:continue
    self.rail(a,b,.12,.12,f'pool rail {i}',.74)
  for p in arc+back:
   if abs(p[0])>1.38:self.post(*p,.12,.81,'pool post')
  self.features.append({'kind':'basin','plan_m':[11.6,6.16],'documented_depth_m':2.1,'water_level_m':-.8,'water_level_measured':False,'curve':'estimated half ellipse'})
 def post(self,x,y,z,h,label):
  self.box((x,y,z+h/2),(.20,.20,h),'granite edges',label=label)
  self.box((x,y,z+h-.18),(.23,.23,.06),'granite',label=label+' collar')
  self.box((x,y,z+h+.015),(.24,.24,.07),'granite edges',label=label+' cap')
 def rail(self,a,b,za,zb,label,h=.92):
  ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay;L=math.hypot(dx,dy);ux,uy=dx/L,dy/L
  mapper=lambda u,z,d:(ax+ux*u+uy*d,ay+uy*u-ux*d,z)
  slope=(zb-za)/L
  # Solid lower panel; genuine open slot below the top beam.
  poly=Polygon([(0,za+.10),(L,zb+.10),(L,zb+h-.24),(0,za+h-.24)])
  self.prism(poly,-.055,.055,mapper,'granite',label+' panel')
  self.tube([(ax,ay,za+h),(bx,by,zb+h)],.055,'granite edges',sides=4,label=label+' top beam')
  for u in [0,L/2,L]:
   x,y,_=mapper(u,0,0);z=za+slope*u
   self.box((x,y,z+h-.12),(.065,.065,.24),'granite edges',label=label+' slot support')
  if not self.lod:
   # Recess borders and a restrained medallion, not a scan of carved motifs.
   for side in [-1,1]:
    points=[mapper(u,z,side*.059) for u,z in [(0.10,za+.17),(L-.10,zb+.17),(L-.10,zb+h-.31),(.10,za+h-.31),(.10,za+.17)]]
    self.tube(points,.008,'granite recess',sides=6,label=label+' inset border')
 def bridge(self):
  run=(10.1-3.38)/24;rise=.14;landing=12*rise
  points=[(-5.05,-2.1),(5.05,-2.1),(5.05,0)]
  # Walk from north end toward the south end along the stepped top boundary.
  for i in range(12):
   y=5.05-i*run;points.extend([(y,(i+1)*rise),(y-run,(i+1)*rise)])
  points.append((-1.69,landing))
  for i in range(12):
   y=-1.69-i*run;points.extend([(y,(11-i)*rise),(y-run,(11-i)*rise)])
  outer=Polygon(points)
  opening=[(-3.08,-2.5),(3.08,-2.5)]
  opening.extend((3.08*math.cos(t),-.85+2.06*math.sin(t)) for t in np.linspace(0,math.pi,49 if self.lod else 129))
  arch=Polygon(opening);solid=outer.difference(arch)
  assert solid.is_valid
  self.prism(solid,-1.25,1.25,lambda y,z,d:(d,y,z),'granite','stepped arch bridge with real through opening')
  self.features.append({'kind':'bridge','dimensions_m':[10.1,2.5],'steps_each_end':12,'rise_m':rise,'run_m':run,'rise_measured':False,'arch_crown_m':1.21,'arch_profile_measured':False})
  # Voussoirs on both sides; arch ring has explicit inner opening.
  n=16 if self.lod else 32
  for side in [-1,1]:
   for i in range(n):
    a=math.pi*i/n+.002;b=math.pi*(i+1)/n-.002
    poly=Polygon([(3.08*math.cos(a),-.85+2.06*math.sin(a)),(3.08*math.cos(b),-.85+2.06*math.sin(b)),(3.25*math.cos(b),-.85+2.25*math.sin(b)),(3.25*math.cos(a),-.85+2.25*math.sin(a))]).intersection(outer)
    self.prism(poly,side*1.25-.025,side*1.25+.025,lambda y,z,d:(d,y,z),'granite edges','arch voussoir')
   # Step nosings preserve all 24 risers in LOD.
  for side in [-1,1]:
   for i in range(12):
    y=side*(5.05-i*run-run/2);z=(i+1)*rise
    self.box((0,y,z+.012),(2.12,run-.012,.024),'granite edges',label='step tread')
    if not self.lod:
     for x in [-.68,0,.68]:self.box((x,y,z+.025),(.008,run-.018,.004),'granite recess',label='tread stone joint')
  self.box((0,0,landing+.012),(2.12,3.38,.024),'granite edges',label='central landing')
  for x in [-1.14,1.14]:
   ys=[-5.05,-3.37,-1.69,1.69,3.37,5.05]
   heights=[0,.84,1.68,1.68,.84,0]
   for i in range(5):self.rail((x,ys[i]),(x,ys[i+1]),heights[i],heights[i+1],'bridge parapet')
   for y,z in zip(ys,heights):self.post(x,y,z,1.0,'bridge post')
   for y in [-1.69,1.69]:self.lion(x,y,2.76)
  # Low carved scroll silhouettes at four ends, simplified from the photo.
  for x in [-1.14,1.14]:
   for sign in [-1,1]:
    pts=[(sign*5.35,.04),(sign*5.35,.19),(sign*5.16,.25),(sign*5.08,.67),(sign*4.86,.84),(sign*4.69,.70),(sign*4.63,.04)]
    self.prism(Polygon(pts),x-.09,x+.09,lambda y,z,d:(d,y,z),'granite edges','estimated scroll end')
    if not self.lod:
     for face in [-1,1]:
      ts=np.linspace(0,math.tau*1.5,48)
      curve=[(x+face*.095,sign*(4.94+(.13-.09*t/ts[-1])*math.cos(t)),.59+(.13-.09*t/ts[-1])*math.sin(t)) for t in ts]
      self.tube(curve,.013,'granite recess',sides=6,label='scroll relief approximation')
 def lion(self,x,y,z):
  self.box((x,y,z+.015),(.23,.25,.03),'granite edges',label='lion plinth')
  self.ball((x,y,z+.13),(.09,.08,.12),'simplified seated lion body')
  self.ball((x,y-.015,z+.275),(.105,.09,.10),'simplified lion head')
  self.ball((x,y-.09,z+.26),(.065,.045,.04),'simplified lion muzzle')
  for side in [-1,1]:
   self.ball((x+side*.073,y,z+.35),(.028,.03,.035),'lion ear approximation')
   self.tube([(x+side*.05,y-.06,z+.04),(x+side*.05,y-.07,z+.18)],.027,'granite edges',sides=8,label='lion front leg')
  if not self.lod:
   for i in range(9):
    a=i*math.tau/9;self.ball((x+.097*math.cos(a),y+.03,z+.275+.097*math.sin(a)),(.024,.024,.024),'lion mane approximation')
 def finish(self):
  self.pool();self.bridge()
  for p in self.parts:
   v=np.asarray(p['vertices']);f=np.asarray(p['triangles']);t=v[f]
   volume=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
   if volume<0:p['triangles']=[(a,c,b) for a,b,c in p['triangles']]
   assert abs(volume)>1e-10,p['label']
  # Adjacent rail panels share end supports; retain each complete solid once.
  unique=[];seen=set()
  for part in self.parts:
   vertices=np.asarray(part['vertices'],dtype='<f4')
   triangles=vertices[np.asarray(part['triangles'])]
   signature=(part['material'],tuple(sorted(tuple(sorted(tuple(float(c) for c in v) for v in tri)) for tri in triangles)))
   if signature not in seen:seen.add(signature);unique.append(part)
  self.parts=unique
  return self

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 b=PoolBridge(a.lod).finish();name=ID+('-lod' if a.lod else '-raw')
 report=b.save(a.out/(name+'.glb'),metadata={'name':'崇明学宫泮池与登云桥（历史照片外观候选）','status':'standalone unregistered component candidate','documented_pool_m':[11.6,6.16,2.1],'documented_bridge_m':[10.1,2.5,3.1],'height_endpoint':'3.1m endpoint unspecified; authored rise/arch/water level estimated','unreconstructed':'Exact sculptural motifs, arch inscription, bed stratigraphy, present condition, geographic registration, walk collision','copyright':'Original geometry MIT; Joshua Wickerham reference CC BY-SA 2.0 not embedded'})
 (a.out/(name+'-features.json')).write_text(json.dumps(b.features,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='part_summary'},ensure_ascii=False))
if __name__=='__main__':main()
