"""Minghuan Shrine: documentary dimensions / three bays, roof and openings assumed. MIT."""
import argparse,json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from common.photo_architecture import Builder,Facade
ID='chongming-minghuan-shrine'
PALETTE={
 'plaster':{'color':[.77,.76,.70],'roughness':.96},
 'stone base':{'color':[.45,.46,.43],'roughness':.97},
 'red brown timber':{'color':[.22,.045,.028],'roughness':.78},
 'timber edges':{'color':[.29,.067,.043],'roughness':.76},
 'panel recess':{'color':[.13,.025,.017],'roughness':.87},
 'inset shadow':{'color':[.018,.024,.020],'roughness':1},
 'roof bedding':{'color':[.19,.21,.20],'roughness':.97},
 'grey tile 0':{'color':[.29,.30,.28],'roughness':.94},
 'grey tile 1':{'color':[.23,.25,.24],'roughness':.94},
 'grey tile 2':{'color':[.34,.35,.31],'roughness':.93},
 'plain ridge':{'color':[.33,.34,.31],'roughness':.94}}
class Shrine:
 def __init__(self,lod=False):self.b=Builder(PALETTE);self.lod=lod;self.features=[]
 def cube(self,c,s,mat,label):self.b.box(c,s,mat,label=label)
 def facade(self,edge,label):
  # Front/rear meet the inside edge of the 0.20m side walls; no coplanar overlap.
  if edge==0:return Facade(self.b,[-4.0,-3.1],[4.0,-3.1],label)
  if edge==2:return Facade(self.b,[4.0,3.1],[-4.0,3.1],label)
  pts=[[-4.2,-3.1],[4.2,-3.1],[4.2,3.1],[-4.2,3.1]]
  return Facade(self.b,pts[edge],pts[(edge+1)%4],label)
 def roofz(self,y):return 6.25-1.75*abs(y)/3.7
 def roof(self):
  # No individually verified roof photograph is used in this candidate. This simple two-slope roof is an assumption.
  for side in [-1,1]:
   end=side*3.7
   poly=Polygon([(0,6.25),(end,4.5),(end,4.42),(0,6.17)])
   self.b.prism(poly,-4.7,4.7,lambda y,z,x:(x,y,z),'roof bedding','assumed-gable-roof-closed-slope')
   count=18 if self.lod else 40
   for i,x in enumerate(np.linspace(-4.58,4.58,count)):
    p=np.array([x,0,6.295]);q=np.array([x,end,4.545]);direction=q-p;direction/=np.linalg.norm(direction)
    self.b.tube([p,q],.056,f'grey tile {i%3}',6 if self.lod else 10,'assumed-parallel-tile-course')
    self.b.tube([q-direction*.012,q+direction*.045],.071,'plain ridge',8,'round-tile-end')
    if not self.lod:
     for t in np.linspace(.12,.96,8):
      mid=p+(q-p)*t;self.b.tube([mid-direction*.010,mid+direction*.010],.060,'grey tile 2',8,'tile-lap-band')
   self.b.tube([(-4.7,end,4.43),(4.7,end,4.43)],.065,'red brown timber',8,'under-eave-fascia')
   for x in np.linspace(-4.4,4.4,12 if self.lod else 24):
    self.b.tube([(x,side*2.8,self.roofz(2.8)-.14),(x,end,4.36)],.035,'red brown timber',6,'estimated-visible-rafter-end')
   for x in [-4.7,4.7]:self.b.tube([(x,0,6.28),(x,end,4.53)],.075,'plain ridge',8,'plain-gable-edge-cap')
  self.cube((0,0,6.39),(9.4,.25,.22),'plain ridge','plain-main-ridge-no-finials')
  self.features.append({'kind':'assumed_roof','type':'simple planar two-slope gable','ridge_total_height_m':6.5,'source_type_unverified':True})
 def doors(self,f):
  # Central entrance is documentary; double leaves, sections and panels are authored.
  for sign in [-1,1]:
   c=sign*.5725;w=1.125
   for x in [c-w/2+.055,c+w/2-.055]:f.box(x,1.845,.11,3.25,.12,-.06,'red brown timber','assumed-door-stile')
   for z,h in [(.28,.14),(1.30,.12),(3.40,.14)]:f.box(c,z,w,h,.11,-.08,'red brown timber','door-rail')
   for z,h in [(.78,.88),(2.35,1.94)]:
    f.box(c,z,w-.22,h,.10,-.09,'red brown timber','solid-door-panel')
    f.box(c,z,w-.36,h-.15,.018,-.031,'panel recess','panel-inset-tone')
    if not self.lod:
     for zz in [z-(h-.15)/2,z+(h-.15)/2]:f.box(c,zz,w-.34,.024,.018,-.017,'timber edges','simple-panel-edge')
   self.features.append({'kind':'estimated-door-leaf','side':sign,'width_m':w,'source':'Central entrance only documented; two-leaf panel design estimated'})
  f.box(0,1.845,.035,3.25,.025,.015,'red brown timber','closing-batten')
  for x in [-1.19,1.19]:f.box(x,1.84,.12,3.28,.23,-.04,'timber edges','door-jamb')
  f.box(0,3.51,2.5,.16,.23,-.04,'timber edges','door-lintel')
 def walls(self):
  self.cube((0,0,.10),(8.8,6.6,.20),'stone base','documented-base-envelope-interpretation')
  # Window holes are declared assumptions, not evidence of these actual openings.
  front=self.facade(0,'assumed-front')
  windows=[box(c-.8,1.4,c+.8,3.05) for c in [-2.8,2.8]]
  front.wall(.2,self.roofz(3.1)-.08,[box(-1.15,.2,1.15,3.45),*windows],.20,'plaster')
  self.doors(front)
  for i,w in enumerate(windows):
   front.window(w,columns=3,rows=4,frame='red brown timber',trim=False,glass='inset shadow',label=f'estimated-window-{i}')
   c=(-2.8,2.8)[i];front.box(c,1.32,1.76,.12,.28,-.02,'stone base','estimated-window-sill')
   self.features.append({'kind':'estimated-window','center_x_m':c,'opening_m':[1.6,1.65],'grid':[3,4],'backing_depth_m':.33})
  rear=self.facade(2,'unobserved-rear');rear.wall(.2,self.roofz(3.1)-.08,[],.20,'plaster')
  for edge in [1,3]:
   f=self.facade(edge,'unobserved-side-gable')
   profile=Polygon([(-3.1,.2),(3.1,.2),(3.1,self.roofz(3.1)-.08),(0,6.17),(-3.1,self.roofz(3.1)-.08)])
   f.wall(.2,6.17,[],.20,'plaster',outline=profile)
  # Butt joints keep side-strip caps inside the front/rear strip footprint,
  # instead of exposing caps coplanar with the plaster wall at y = +/-3.1.
  for x in [-4.14,4.14]:self.cube((x,0,.33),(.24,5.84,.26),'stone base','wall-skirting')
  self.cube((0,3.04,.33),(8.52,.24,.26),'stone base','wall-skirting')
  # Two front skirt segments leave the central doorway unobstructed.
  for x in [-2.73,2.73]:self.cube((x,-3.04,.33),(3.06,.24,.26),'stone base','front-side-skirting')
 def finish(self):
  self.walls();self.roof()
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(vol)>1e-10,p['label']
   if vol<0:p['triangles']=[(a,c,b) for a,b,c in t]
  return self
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 m=Shrine(a.lod).finish();role='lod' if a.lod else 'raw'
 r=m.b.save(a.out/f'{ID}-{role}.glb',metadata={'name':'崇明学宫名宦祠（文字尺寸参照候选）','status':'Text-dimension-guided candidate; individual photographic identity unverified; not map registered','documented':'Three bays, central entrance, east-west 8.8 m / north-south 6.6 m / height 6.5 m; east of Ji Gate by official text','endpoints':'8.8 x 6.6 interpreted as base envelope; wall/eave endpoints not documented; roof overhang increases model bounds','estimated':'Simple gable roof, two windows, double doors, materials, plinth, rear/side walls and local front direction','omitted':'Exact bracket sets, inscriptions, sculpture, interior, courtyard and adjacent buildings'})
 (a.out/f'{role}-features.json').write_text(json.dumps(m.features,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
