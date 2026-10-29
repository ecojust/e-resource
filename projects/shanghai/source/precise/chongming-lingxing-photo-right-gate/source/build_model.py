"""Photo-right Lingxing side gate, low-resolution 1990s reference candidate. MIT."""
import argparse,json
from pathlib import Path
import numpy as np
from common.photo_architecture import Builder
ID='chongming-lingxing-photo-right-gate'
PALETTE={
 'stone':{'color':[.50,.50,.45],'roughness':.97},
 'stone edge':{'color':[.55,.55,.49],'roughness':.95},
 'stone recess':{'color':[.43,.43,.38],'roughness':.99},
 'red wood':{'color':[.25,.034,.022],'roughness':.76},
 'wood recess':{'color':[.14,.018,.012],'roughness':.87},
 'wood edge':{'color':[.31,.043,.028],'roughness':.73},
 'dark iron':{'color':[.10,.10,.09],'roughness':.82,'metallic':.30}}
class RightGate:
 def __init__(self,lod=False):self.b=Builder(PALETTE);self.lod=lod;self.features=[]
 def box(self,c,s,material,label):self.b.box(c,s,material,label=label)
 def shaft(self,x,width,z0,z1,label):
  # Plain chamfered square shafts, with no unsupported ornamental copying.
  r=width/2;c=.025
  cross=[(-r+c,-r),(r-c,-r),(r,-r+c),(r,r-c),(r-c,r),(-r+c,r),(-r,r-c),(-r,-r+c)]
  n=len(cross);vs=[(x+a,b,z) for z in [z0,z1] for a,b in cross]
  faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  self.b.add(vs,faces,'stone',label)
 def frame(self):
  for x in [-1.33,1.33]:
   self.shaft(x,.36,0,3.78,'estimated-square-lower-pier')
   self.box((x,0,3.79),(.39,.39,.06),'stone recess','plain-post-collar')
   self.shaft(x,.33,3.82,4.82,'historically-visible-upper-post-no-carving')
   self.box((x,0,4.85),(.30,.30,.06),'stone','estimated-plain-top-cap')
  self.box((0,0,3.475),(2.3,.34,.55),'stone','unlettered-horizontal-lintel')
  self.box((0,-.179,3.345),(2.16,.022,.20),'stone recess','estimated-lower-lintel-panel')
  for z in [3.23,3.46]:self.box((0,-.196,z),(2.22,.032,.03),'stone edge','lintel-horizontal-bead')
  for x in [-1.11,1.11]:self.box((x,-.196,3.345),(.03,.032,.23),'stone edge','lintel-end-bead')
  self.features.append({'kind':'historical_stone_frame','clear_opening_m':[2.3,3.2],'overall_height_m':4.88,'overall_height_estimated':True,'upper_post_carving_omitted':True})
 def leaf(self,sign):
  # Closed position is a conservative interpretation of the distant dark red facade.
  center=sign*.5715;width=1.131
  for x in [center-width/2+.05,center+width/2-.05]:self.box((x,-.015,1.61),(.10,.12,3.10),'red wood','closed-leaf-stile')
  for z,h in [(.13,.14),(1.03,.10),(2.72,.10),(3.105,.11)]:self.box((center,0,z),(width,.12,h),'red wood','closed-leaf-rail')
  self.box((center,.01,.58),(width-.20,.10,.80),'red wood','estimated-solid-lower-panel')
  self.box((center,-.046,.58),(width-.34,.018,.62),'wood recess','lower-panel-inset')
  self.box((center,.01,2.915),(width-.20,.10,.28),'red wood','estimated-upper-board')
  if not self.lod:
   for z in [.27,.89]:self.box((center,-.061,z),(width-.31,.018,.022),'wood edge','lower-panel-horizontal-bead')
   for x in [center-(width-.31)/2,center+(width-.31)/2]:self.box((x,-.061,.58),(.022,.018,.62),'wood edge','lower-panel-vertical-bead')
   self.box((center,-.046,2.915),(width-.34,.018,.16),'wood recess','upper-board-inset')
   for z in [2.825,3.005]:self.box((center,-.061,z),(width-.31,.018,.022),'wood edge','upper-board-bead')
  for x in np.linspace(center-width/2+.19,center+width/2-.19,6):
   self.box((float(x),-.015,1.875),(.034,.065,1.56),'wood edge','estimated-vertical-slat')
  for z in [.42,2.44]:
   x=sign*1.137
   self.b.tube([(x,-.015,z-.08),(x,-.015,z+.08)],.035,'dark iron',6 if self.lod else 12,'estimated-hinge-pin')
  self.features.append({'kind':'closed_door_leaf','side':sign,'width_m':width,'vertical_bars':6,'pose_and_divisions':'Estimated from low-resolution historical facade, not precisely verified'})
 def finish(self):
  self.frame();self.leaf(-1);self.leaf(1)
  self.box((0,-.087,1.61),(.04,.025,3.10),'red wood','estimated-central-closing-batten')
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(vol)>1e-10,p['label']
   if vol<0:p['triangles']=[(a,c,b) for a,b,c in t]
  return self
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 m=RightGate(a.lod).finish();role='lod' if a.lod else 'raw'
 r=m.b.save(a.out/f'{ID}-{role}.glb',metadata={'name':'崇明学宫棂星门照片右侧门（1990年代参照）','scope':'Photo-right historical side portal only; absolute geographic orientation unverified','status':'Low-resolution 1990s reference candidate; not geographically registered','documented':'Side opening 2.3 m wide by 3.2 m high, interpreted as clear frame','observed':'Two tall upper stone posts, lower lintel and red timber below, partly cropped/obscured','estimated':'Overall height 4.88 m, sections, plain upper shafts/caps, closed pose, slat count, panels and hidden back','omitted':'Exact relief, adjoining wall/lattice panel, central and left portals, ground, shrubs and repair-date reconstruction'})
 (a.out/f'{role}-features.json').write_text(json.dumps(m.features,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
