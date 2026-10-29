"""Text-guided Chongsheng Shrine candidate. Metres; x east, y north, z up. MIT."""
import argparse,json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from architecture import Architecture,Builder,PALETTE,Facade
ID='chongming-chongsheng-shrine'
class Shrine(Architecture):
 def __init__(self,lod=False):
  self.b=Builder(PALETTE);self.lod=lod;self.features=[]
  self.ux=7.05;self.uy=6.675;self.ridge=3.8;self.breaky=2.7
 def roof(self,field,s,t):
  u=2*s-1
  if field<2:
   y=self.uy*t;x=u*(self.ridge+(self.ux-self.ridge)*max(0,(y-self.breaky)/(self.uy-self.breaky)));y*=(-1 if field==0 else 1)
  else:
   x=(-1 if field==2 else 1)*(self.ridge+(self.ux-self.ridge)*t);y=u*(self.breaky+(self.uy-self.breaky)*t)
  q=abs(y)/self.uy if field<2 else (self.breaky+(self.uy-self.breaky)*t)/self.uy
  return np.array([x,y,5.8+4.85*(1-q)**1.5+.42*(abs(x)/self.ux)**8*(abs(y)/self.uy)**8])
 def walls(self):
  self.box((0,0,.225),(12.5,11.75,.45),'granite base','documented-base-endpoints-inferred')
  for i in range(3):
   run=(3-i)*.3;self.box((0,-5.875-run/2,(i+1)*.075),(3.6,run,(i+1)*.15),'granite base','estimated-entry-step')
  for edge in [1,2,3]:
   f=self.facade(6,5.625,edge,'unobserved-wall');f.wall(.45,5.85,[],.18,'white lime plaster')
   f.box(0,.65,f.length,.4,.24,-.03,'granite base','wall-base')
  for y in [-5.625,5.625]:
   for x in [-6,-2,2,6]:
    self.b.lathe((x,y),[(.45,.25),(.57,.27),(.72,.21)],'granite base',16,'estimated-column-foot')
    self.b.lathe((x,y),[(.70,.21),(5.6,.18)],'aged red brown timber',16,'estimated-timber-column')
  # Close the attic perimeter up to the authored roof underside.
  for edge in range(4):
   f=self.facade(6,5.625,edge,"estimated-attic")
   if edge in [0,2]:
    top=lambda u: self.roof(0,.5,5.625/self.uy)[2]-.08
   else:
    t=(6-self.ridge)/(self.ux-self.ridge)
    top=lambda u: self.roof(2,.5,t)[2]-.08
   outline=Polygon([(-f.length/2,5.20),(f.length/2,5.20)]+[(u,top(u)) for u in np.linspace(f.length/2,-f.length/2,33)])
   f.prism(outline,-.10,.02,"dark timber","estimated-attic-closure")
  for x in [-6,6]:
   for y in [-1.875,1.875]:
    self.b.lathe((x,y),[(.45,.22),(5.6,.18)],'aged red brown timber',16,'side-column')
  for edge in range(4):
   f=self.facade(6,5.625,edge,'eave-timber')
   f.box(0,5.36,f.length,.32,.32,0,'aged red brown timber','tie-beam')
   f.box(0,5.69,f.length,.14,.26,0,'worn timber edges','upper-tie')
   for u in np.linspace(-f.length/2+.2,f.length/2-.2,13):
    for j in range(3):f.box(float(u),5.55+j*.12,.20+j*.14,.12,.30+j*.14,.04,'aged red brown timber','estimated-bracket-step')
  f=self.facade(6,5.625,0,'three-bay-front')
  for center in [-4,0,4]:
   for j in range(4):
    u=center+(j-1.5)*.91
    f.box(u,1.24,.87,1.56,.13,0,'aged red brown timber','estimated-door-bottom')
    f.box(u,1.24,.65,1.25,.025,.08,'dark timber','door-inset')
    for dx in [-.325,.325]:f.box(u+dx,1.24,.025,1.25,.025,.105,'worn timber edges','panel-bead')
    for z in [.615,1.865]:f.box(u,z,.65,.025,.025,.105,'worn timber edges','panel-bead')
    self.lattice(f,u,2.08,.87,2.65,'estimated-door-lattice',cols=4,rows=8)
   f.box(center,4.94,3.8,.25,.20,0,'aged red brown timber','door-lintel')
   f.box(center,.50,3.8,.10,.30,.08,'granite base','threshold')
 def roofs(self):
  for field in range(4):self.roof_patch(lambda s,t:self.roof(field,s,t),'single',field)
  z=self.roof(0,.5,self.breaky/self.uy)[2]-.075
  for side in [-1,1]:
   a=[side*self.ridge,-self.breaky];b=[side*self.ridge,self.breaky]
   f=Facade(self.b,a if side>0 else b,b if side>0 else a,'estimated-gable')
   outline=Polygon([(-self.breaky,z),(self.breaky,z)]+[(y,self.roof(0,.5,abs(y)/self.uy)[2]-.075) for y in np.linspace(self.breaky,-self.breaky,33)])
   f.prism(outline,-.07,.01,'dark timber','gable-closure')
  self.box((0,0,10.78),(7.6,.27,.26),'ridge ceramic','plain-ridge')
  self.box((0,0,10.955),(7.6,.20,.09),'ridge ceramic','plain-ridge-cap')
 def finish(self):
  # Independently compare matching hip coordinates before mesh generation.
  for t in np.linspace(0,1,101):
   q=(self.breaky+(self.uy-self.breaky)*t)/self.uy
   for field,side,s in [(0,3,0),(0,2,0),(1,3,1),(1,2,1)]:
    assert np.allclose(self.roof(field,1 if side==3 else 0,q),self.roof(side,s,t),atol=1e-10)
  self.walls();self.roofs()
  # No evidence for sculptural ridge beasts: remove helper-generated estimates.
  self.b.parts=[p for p in self.b.parts if '/estimated-figure-' not in p['label']]
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(vol)>1e-10,p['label']
   if vol<0:p['triangles']=[(a,c,b) for a,b,c in t]
  return self
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 m=Shrine(a.lod).finish();role='lod' if a.lod else 'raw'
 r=m.b.save(a.out/f'{ID}-{role}.glb',metadata={'name':'崇明学宫崇圣祠正殿','status':'Text-guided exterior candidate; not photo verified; not map registered','documented':'Three bays; 12.5 x 11.75 x 11 m; single-eave xieshan','estimated':'Measurement endpoints, doors, roof curves, brackets, color, steps, hidden faces','omitted':'Front gate, interior, inscriptions, sculptures, exact carvings'})
 (a.out/f'{role}-features.json').write_text(json.dumps(m.features,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
