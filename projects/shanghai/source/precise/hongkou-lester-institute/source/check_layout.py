"""Measure pre-export geometry requests without allocating renderer or triangle payloads."""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import json,math,runpy
import numpy as np
from shapely.geometry import Polygon,Point,MultiPoint
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1]
src=runpy.run_path(str(root/'source/build_lester_institute.py'));plans=src['PLANS'];pa=src['P'];pf=Polygon(pa['source_outer_uv'])
class Survey:
 def __init__(self):
  self.count=Counter();self.extrema=[];self.outlines=[];self.ground_west=[];self.apertures={};self.windowlocations=[];self.crown=[]
 def record(self,label,material,points):
  assert material in src['PALETTE'],material
  a=np.array(points,float);assert len(a)>0 and np.all(np.isfinite(a))
  self.count[label]+=1;self.extrema.extend((a.min(0),a.max(0)))
  hull=MultiPoint(a[:,:2]).convex_hull
  if pf.distance(hull)>2:raise ValueError((label,pf.distance(hull)))
  self.outlines.append(hull)
  if label.endswith('/recessed glass') and 'wing garden' in label:self.windowlocations.append([label,[round(float(x),3) for x in a.mean(0)]])
 def box(self,center,size,material,basis=None,label='detail'):
  axes=np.eye(3) if basis is None else np.array(basis,float).T
  self.record(label,material,[center+axes@(np.array(size)*np.array([i,j,k])/2)for i in (-1,1)for j in (-1,1)for k in (-1,1)])
 def prism(self,poly,lo,hi,mapper,material,label):
  if poly.is_empty:return
  gc=tuple(poly.geoms) if hasattr(poly,'geoms')else (poly,)
  pts=[mapper(x,y,d)for g in gc if g.geom_type=='Polygon' for x,y in g.exterior.coords for d in (lo,hi)]
  if not pts:return
  self.record(label,material,pts)
  if label.endswith('/continuous-open-wall'):
   self.apertures[label]=sum(len(g.interiors)for g in gc if g.geom_type=='Polygon')
 def plan_prism(self,poly,lo,hi,material,label):self.prism(poly,lo,hi,lambda x,y,d:(x,y,d),material,label)
 def tube(self,pts,r,material,sides,label):
  self.record(label,material,pts)
 def lathe(self,center,profile,material,segs,label):
  self.record(label,material,[(center[0]+r*math.cos(a),center[1]+r*math.sin(a),z)for z,r in profile for a in np.linspace(0,math.tau,segs+1)])
 def add(self,vs,fs,material,label):
  self.record(label,material,vs)
def main(lod):
 b=Survey();src['assemble'](b,lod);assert b.count['west wing garden/recessed glass']==b.count['east wing garden/recessed glass']==45
 assert b.apertures['west wing garden/continuous-open-wall']==b.apertures['east wing garden/continuous-open-wall']==45
 assert b.count['Arcade front/arch arrises']==7 and b.count['Arcade front/shield carving']==6
 assert b.count['Crown/radial masonry ribs']==16 and b.count['Rooflights/northeast panes']==6
 footprint=unary_union(b.outlines);whole=unary_union([Polygon(v) for v in plans.values()]);ext=np.array(b.extrema)
 return {'level':'LOD' if lod else 'full','geometry_requests':sum(b.count.values()),'garden_wing_window_counts':[45,45],'arcade_openings':7,'arcade_corner_shields':6,'dome_ribs_approximate':16,'rooflight_spans_across_each_saw':2,'sawtooth_strips':3,'bounds_enu_m':[ext.min(0).round(4).tolist(),ext.max(0).round(4).tolist()],'authored_base_area_m2':whole.area,'plan_outside_named_owner_m2':whole.difference(pf).area,'geometry_horizontal_projection_outside_named_owner_m2_approx':footprint.difference(pf).area,'facade_positions':b.windowlocations,'material_names':list(src['PALETTE']),'note':'Layout-level prospective positions; independently decoded final assets must be rechecked once built.'}
out={'id':pa['id'],'draft_layout_preflight':True,'exported':False,'source_sha256':sha256((root/'source/build_lester_institute.py').read_bytes()).hexdigest(),'parameter_sha256':sha256((root/'source/parameters.json').read_bytes()).hexdigest(),'checks':[main(False),main(True)]}
p=root/'parameterized-layout-review.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print([{k:v for k,v in q.items()if k in ('geometry_requests','bounds_enu_m','authored_base_area_m2','plan_outside_named_owner_m2','geometry_horizontal_projection_outside_named_owner_m2_approx')}for q in out['checks']])
