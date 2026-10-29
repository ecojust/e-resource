"""Original Yimen form candidate, with independently stated documentary and modeled dimensions. MIT."""
import argparse,json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from common.photo_architecture import Builder
ID='chongming-yimen'
P={'base_width':10.6,'base_depth':9.7,'base_height':.22,'wall_width':10.24,'wall_depth':9.3,'roof_half_depth':5.0,'roof_half_width':4.98,'roof_ridge':6.45,'roof_eave':4.70,'end_wall_top':6.93,'total_height':7.0,'window_bottom':1.2,'window_top':3.55,'curtain_width':1.18,'curtain_bottom':.4,'curtain_top':3.75}
PALETTE={'plaster':{'color':[.83,.81,.74],'roughness':.96},'stone':{'color':[.48,.46,.39],'roughness':.97},'timber':{'color':[.18,.075,.046],'roughness':.83},'wood trim':{'color':[.24,.105,.063],'roughness':.80},'grille backing':{'color':[.48,.46,.36],'roughness':1},'tile0':{'color':[.24,.25,.22],'roughness':.97},'tile1':{'color':[.30,.30,.26],'roughness':.96},'roof bed':{'color':[.16,.18,.16],'roughness':1},'cap':{'color':[.30,.31,.28],'roughness':.97},'curtain':{'color':[.69,.54,.33],'roughness':.95},'plaque':{'color':[.04,.25,.25],'roughness':.8},'blank inset':{'color':[.22,.25,.22],'roughness':1}}
class Yimen:
 def __init__(self,lod=False):self.b=Builder(PALETTE);self.lod=lod;self.features=[];self.grilles=[]
 def cube(self,c,s,m,label):self.b.box(c,s,m,label=label)
 def roofz(self,y):
  t=abs(y)/P['roof_half_depth'];return P['roof_ridge']-(P['roof_ridge']-P['roof_eave'])*(2*t-t*t)
 def wallz(self,y):
  t=abs(y)/P['roof_half_depth'];return P['end_wall_top']-2.0*(2*t-t*t)+.12*t**12
 def front_prism(self,poly,back,front,mat,label):self.b.prism(poly,back,front,lambda x,z,d:(x,-4.65-d,z),mat,label)
 def grille(self,x0,x1,label,lower_panel=False):
  z0,z1=P['window_bottom'],P['window_top'];outer=box(x0,z0,x1,z1);inner=outer.buffer(-.045,join_style=2);columns,rows=(2,7) if self.lod else (4,14)
  bars=[box(x0+(x1-x0)*i/columns-.012,z0,x0+(x1-x0)*i/columns+.012,z1) for i in range(1,columns)]
  bars += [box(x0,z0+(z1-z0)*i/rows-.013,x1,z0+(z1-z0)*i/rows+.013) for i in range(1,rows)]
  holes=inner.difference(unary_union(bars));self.front_prism(outer.difference(holes),-.035,.055,'timber',label+'-true-grid');self.front_prism(inner,-.16,-.14,'grille backing',label+'-recessed-backing')
  self.cube(((x0+x1)/2,-4.72,z1+.09),(x1-x0,.14,.16),'wood trim',label+'-upper-rail')
  if lower_panel:
   self.cube(((x0+x1)/2,-4.62,.70),(x1-x0,.13,.96),'timber',label+'-lower-panel')
   self.cube(((x0+x1)/2,-4.70,.70),(x1-x0-.09,.025,.80),'wood trim',label+'-lower-panel-inset')
  self.grilles.append({'label':label,'x0':x0,'x1':x1,'bottom':z0,'top':z1,'grid':[columns,rows]})
 def walls(self):
  self.cube((0,0,.11),(10.6,9.7,.22),'stone','interpreted-base')
  # Two authored estimated steps; count not established by the partly occluded photo.
  stair=Polygon([(-5.7,0),(-4.65,0),(-4.65,.15),(-5.2,.15),(-5.2,.08),(-5.7,.08)])
  self.b.prism(stair,-1.85,1.85,lambda y,z,x:(x,y,z),'stone','estimated-two-step-closed-profile')
  ys=np.linspace(-5,5,41 if not self.lod else 17);profile=[(float(y),self.wallz(y)) for y in ys]
  outline=Polygon([(-4.65,.22),(4.65,.22),(4.65,4.25),(5,4.50),*reversed(profile),(-5,4.50),(-4.65,4.25)])
  cap=Polygon(profile+[(y,z+.07) for y,z in reversed(profile)])
  for sign in [-1,1]:
   lo,hi=sign*5.0-.12,sign*5.0+.12
   self.b.prism(outline,lo,hi,lambda y,z,x:(x,y,z),'plaster','observed-form-curved-end-wall')
   self.b.prism(cap,lo-.025,hi+.025,lambda y,z,x:(x,y,z),'cap','curved-end-wall-cap')
   self.cube((sign*5,-4.78,4.18),(.34,.26,.18),'plaster','front-end-wall-band')
   self.cube((sign*5,-4.78,3.62),(.30,.07,.43),'blank inset','simplified-end-wall-inset')
  # Back side unknown: plain closed wall follows estimated rear eave height.
  self.cube((0,4.55,2.35),(9.76,.2,4.26),'plaster','estimated-plain-rear')
  self.cube((0,-4.56,3.98),(9.76,.18,.44),'timber','observed-front-upper-timber-zone')
  for lo,hi in [(-4.88,-2.05),(2.05,4.88)]:
   self.cube(((lo+hi)/2,-4.55,.71),(hi-lo,.20,.98),'plaster','estimated-side-window-plinth')
   for k in range(6):
    a=lo+(hi-lo)*k/6+.018;b=lo+(hi-lo)*(k+1)/6-.018;self.grille(a,b,f'side-{lo:g}-visible-field-{k+1}')
  for lo,hi in [(-1.83,-.62),(.62,1.83)]:
   for k in range(2):
    a=lo+(hi-lo)*k/2+.018;b=lo+(hi-lo)*(k+1)/2-.018;self.grille(a,b,f'curtain-flank-{lo:g}-field-{k+1}',True)
  for x in [-1.95,1.95]:
   self.b.tube([(x,-4.76,.28),(x,-4.76,4.22)],.105,'wood trim',12 if self.lod else 20,'observed-inner-upright')
   self.cube((x,-4.77,.29),(.28,.30,.14),'stone','estimated-column-foot')
  # Curtain is a closed corrugated solid. Its hidden door arrangement is not invented.
  xs=np.linspace(-P['curtain_width']/2,P['curtain_width']/2,57 if not self.lod else 25)
  points=[(float(x),-4.91+.035*np.cos((x+.59)/1.18*12*np.pi)) for x in xs]
  curtain=Polygon(points+[(x,y+.035) for x,y in reversed(points)])
  self.b.plan_prism(curtain,P['curtain_bottom'],P['curtain_top'],'curtain','observed-curtain-estimated-folds-no-hidden-door')
  self.cube((0,-4.90,3.80),(1.28,.09,.07),'timber','curtain-head-rail')
  # Blue-green sign field, intentionally no copied calligraphy.
  self.cube((0,-4.94,4.26),(.47,.08,.82),'wood trim','vertical-plaque-frame')
  self.cube((0,-4.99,4.26),(.36,.035,.70),'plaque','blank-vertical-plaque')
  self.features += [{'kind':'visible-grille-fields','side_fields_each':6,'curtain_flank_fields_each':2,'total_visible_fields':16,'small_pane_counts_estimated':True},{'kind':'curtain','hidden_door_leaf_count':None,'geometry':'closed corrugated slab'},{'kind':'end-walls','observed_form':True,'profile_coordinates_estimated':True}]
 def roof(self):
  half=P['roof_half_width'];n=21 if not self.lod else 9
  for sign in [-1,1]:
   ys=np.linspace(0,sign*5,n);profile=[(float(y),self.roofz(y)) for y in ys]
   shell=Polygon(profile+[(y,z-.085) for y,z in reversed(profile)])
   self.b.prism(shell,-half,half,lambda y,z,x:(x,y,z),'roof bed','curved-roof-closed-shell')
   for i,x in enumerate(np.linspace(-half+.09,half-.09,49 if not self.lod else 25)):
    path=[(float(x),float(y),self.roofz(y)+.04) for y in ys];self.b.tube(path,.055,f'tile{i%2}',8 if not self.lod else 6,'estimated-tile-course')
    y=sign*5;self.b.tube([(x,y-sign*.025,self.roofz(y)+.03),(x,y+sign*.045,self.roofz(y)+.03)],.070,'cap',8,'round-eave-tile-end')
   self.cube((0,sign*4.84,4.52),(9.96,.16,.16),'timber','eave-fascia')
   for x in np.linspace(-4.8,4.8,24 if not self.lod else 12):self.b.tube([(x,sign*4.35,self.roofz(4.35)-.14),(x,sign*5,self.roofz(5)-.14)],.035,'timber',6,'visible-rafter-end')
  self.cube((0,0,6.56),(9.96,.24,.20),'cap','simplified-ridge')
  # Narrow pierced ridge band is original regular geometry, not a traced carving.
  for x in np.linspace(-4.8,4.8,44 if not self.lod else 22):self.b.tube([(x-.07,0,6.68),(x+.07,0,6.78)],.025,'cap',6,'simplified-ridge-piercing')
  self.cube((0,0,6.84),(9.96,.18,.08),'cap','ridge-top-cap')
 def finish(self):
  self.walls();self.roof()
  for part in self.b.parts:
   v=np.array(part['vertices']);t=np.array(part['triangles']);volume=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(volume)>1e-10,part['label']
   if volume<0:part['triangles']=[(a,c,b) for a,b,c in t]
  return self
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);m=Yimen(a.lod).finish();role='lod' if a.lod else 'raw'
 result=m.b.save(a.out/f'{ID}-{role}.glb',metadata={'id':ID,'name':'崇明学宫仪门（照片形态参照候选）','status':'Photo-form candidate, no photo-scale or geographic acceptance','documentary_dimensions_m':[10.6,9.7,9.07],'modeled_height_m':7.0,'height_conflict':'Modeled height7.0m is an explicit design estimate; documented9.07m endpoints unresolved, not forced into the visible facade. No pixel-to-metric measurement claimed.','observed':'Curved pale end walls, front curved roof, two inner uprights, six side grille fields each, two exposed fields per curtain flank, beige curtain and vertical plaque field.','estimated':'Profile dimensions, pane counts, fold count, two steps, colours, mirrored rear roof and plain rear wall. No documented full bay or column network.','omitted':'Hidden door leaves, calligraphy, precise carvings, plants, adjacent buildings and interiors','photo_scope':'Reference-only observation; no photograph redistributed, embedded or sampled into textures.'})
 (a.out/f'{role}-features.json').write_text(json.dumps({'features':m.features,'grilles':m.grilles},indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='part_summary'}))
