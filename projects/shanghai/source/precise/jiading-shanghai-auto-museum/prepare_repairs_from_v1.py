#!/usr/bin/env python3
"""Bounded read-only v1 triangle diagnostics → explicit local v2 design inputs.

Optional evidence regeneration requires the rejected v1 raw/sidecar supplied by
the caller. Complete v2 model generation only needs the resulting JSON inputs.
This script never generates a complete museum or accepts geometry.
"""
from pathlib import Path
import argparse,json,struct,hashlib
import numpy as np
from shapely.geometry import Polygon,LineString,Point,box,mapping
from shapely.ops import unary_union,polygonize,nearest_points
HERE=Path(__file__).resolve().parent
EXPECTED_RAW='5c2f93f9b66f75771587ed532928d02dbc3d6960fc1c0804d37e498faa9a969d'

def descriptor(p):
 data=p.read_bytes();return {'file':p.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

class Actual:
 def __init__(self,path,sidecar):
  self.data=path.read_bytes();assert hashlib.sha256(self.data).hexdigest()==EXPECTED_RAW
  length,kind=struct.unpack_from('<II',self.data,12);assert kind==0x4e4f534a
  self.doc=json.loads(self.data[20:20+length]);self.off=28+length
  assert all(not any(k in n for k in ['matrix','translation','rotation','scale']) for n in self.doc['nodes'])
  side=json.loads(sidecar.read_text());assert side['sha256']==EXPECTED_RAW
  self.rows={r['label']:r for r in side['actual_serialized_part_ranges']};assert len(self.rows)==12373
 def accessor(self,i):
  a=self.doc['accessors'][i];v=self.doc['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC3':3}[a['type']]
  assert 'byteStride' not in v and 'sparse' not in a
  return np.frombuffer(self.data,dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']],count=a['count']*n,offset=self.off+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 def triangles(self,label):
  r=self.rows[label];p=self.doc['meshes'][0]['primitives'][r['primitive_index']]
  ids=self.accessor(p['indices']).reshape(-1,3)[r['first_triangle']:r['first_triangle']+r['triangle_count']]
  q=self.accessor(p['attributes']['POSITION'])[ids].astype(float)
  return q[:,:,[0,2,1]]*np.array([1,-1,1])
 def key(self,label):
  r=self.rows[label];return [label,r['material'],0]

def section(triangles,z):
 polys=[];segments=[]
 for t in triangles:
  d=t[:,2]-z
  if abs(d).max()<1e-9:
   p=Polygon(t[:,:2])
   if p.area>1e-12:polys.append(p)
   continue
  points=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if abs(d[i])<1e-9:points.append(t[i,:2])
   if d[i]*d[j]<0:points.append(t[i,:2]+(t[j,:2]-t[i,:2])*(-d[i])/(d[j]-d[i]))
  unique=list(dict.fromkeys(tuple(np.round(p,7)) for p in points))
  if len(unique)==2 and unique[0]!=unique[1]:segments.append(LineString(unique))
 if segments:polys.extend(polygonize(unary_union(segments)))
 return unary_union(polys)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--sidecar',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if a.output.exists():raise ValueError('Preserve previous repair inputs; use a new file')
 m=Actual(a.raw,a.sidecar);add=[];diagnostics=[]
 def support(label,plan,bottom,top,material,targets,note):
  # Local estimated infill outlines may inherit micron-scale buffer corners.
  # Remove sub0.1mm plan edges before Float32, not by relaxing geometry tests.
  plan=plan.simplify(.0001,preserve_topology=True)
  assert plan.geom_type=='Polygon' and plan.is_valid and plan.area>0 and top>bottom
  add.append({'label':label,'material':material,'plan':mapping(plan),'bottom_m':bottom,'top_m':top,'actual_v1_target_labels':targets,'dimensions_estimated':True,'note':note})
 # Only the small orphaned upper-entry pane needs a local extension.
 pane='curtain/layer-1/bay-161/glass-pane-1';head='entry/continuous-head'
 base=section(m.triangles(pane),3.4800000190734863);header=section(m.triangles(head),3.48)
 p=base.representative_point();q=nearest_points(p,header.buffer(-.025))[1]
 plan=unary_union([base.buffer(.02,quad_segs=4),LineString([p,q]).buffer(.065,cap_style=2)]).convex_hull
 support('repair/entry-small-pane-bottom-seat',plan,3.43,3.51,'Museum brushed rail metal',[pane,head],'Local extension below existing small pane; original door/header/curtain geometry stays unchanged.')
 # Two local floor seats restore the omitted north-return intersections.
 floor='interior-estimate/fifth-floor-plate';floor_plan=section(m.triangles(floor),27.350000381469727)
 for side,bay in [('west',2),('east',28)]:
  pane=f'curtain/layer-5/bay-{bay:03d}/glass-pane-0';foot=section(m.triangles(pane),27.350000381469727)
  join=nearest_points(foot.centroid,floor_plan.buffer(-.12))[1].buffer(.08,quad_segs=4)
  plan=unary_union([foot.buffer(.025,quad_segs=4),join]).convex_hull
  support(f'repair/fifth-floor-{side}-pane-seat',plan,27.08,27.365,'Museum interior floor',[pane,floor],'Bounded local floor extension from the unchanged actual pane footprint to the existing floor; not an enlarged whole floor.')
 # Small north roof patch remains; two narrow concealed ties bridge to the deck.
 north='roof/lower-curved-continuous-underlayer';deck='roof/upper-deep-cantilever-underlayer';z=22.18
 npoly=section(m.triangles(north),z);dpoly=section(m.triangles(deck),z)
 slot_shadow=[]
 for i in range(1,6):
  t=m.triangles(f'north-spine/glazed-wrap-slot-{i}')
  t=t[(t[:,:,2].min(1)<=22.26)&(t[:,:,2].max(1)>=22.10)]
  slot_shadow.extend(Polygon(q[:,:2]) for q in t if Polygon(q[:,:2]).area>1e-12)
 forbidden=unary_union(slot_shadow);chosen=[]
 for side,xrange in [('west',(-14.,-8.)),('east',(-1.5,3.5))]:
  candidates=[]
  for x in np.linspace(*xrange,41):
   patch=npoly.intersection(box(x-.07,-100,x+.07,100))
   if patch.is_empty:continue
   p=patch.representative_point();q=nearest_points(p,dpoly.buffer(-.16))[1]
   plan=LineString([p,q]).buffer(.09,cap_style=2)
   if plan.intersection(forbidden).area>1e-12:continue
   if plan.intersection(npoly).area<.005 or plan.intersection(dpoly).area<.005:continue
   if any(plan.intersects(other) for other in chosen):continue
   candidates.append((p.distance(q),plan,p,q))
  if not candidates:raise ValueError('No bounded north tie avoids actual glazing-slot projection: '+side)
  distance,plan,p,q=min(candidates,key=lambda v:v[0]);chosen.append(plan)
  support(f'repair/north-roof-concealed-tie-{side}',plan,22.10,22.26,'Museum recessed panel joint',[north,deck],'Narrow tie within the existing deck depth; conservative actual slot projection at the complete tie z interval is avoided. Estimated internal support, not structural certification.')
  diagnostics.append({'role':side+' north tie','span_between_interior_endpoints_m':distance,'width_m':.18,'plan_area_m2':plan.area,'actual_old_north_slice_overlap_m2':plan.intersection(npoly).area,'actual_old_deck_slice_overlap_m2':plan.intersection(dpoly).area,'actual_slot_projection_overlap_m2':plan.intersection(forbidden).area})
 panel='roof/lower-silver-top/panel--1--12-0'
 result={'schema':'auto-museum-bounded-repair-inputs-v2','building_id':'jiading-shanghai-auto-museum','baseline_raw':descriptor(a.raw),'baseline_sidecar':descriptor(a.sidecar),'baseline_source_freeze':descriptor(HERE/'history/source-freeze-v1.json'),'new_model_generated':False,'source_only':True,'added_parts':add,'changed_part':{'key':m.key(panel),'label':panel,'bottom_extension_m':.0015,'top_and_plan_unchanged':True,'actual_v1_maximum_affine_gap_m':.00042802964890180026,'scope':'Only this actual panel; not a global thickness/tolerance change.'},'diagnostics':diagnostics,'section_numeric_method':'Actual Float32 triangles, finite horizontal intersection lines welded at1e-7m solely for this source-input preparation. Subsequent independent actual raw audit is required.','source_geometry_unchanged':True,'overall_height_and_curves_unchanged':True,'complete_collision_checked':False}
 a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'added_parts':[{'label':p['label'],'plan_area_m2':Polygon(p['plan']['coordinates'][0]).area} for p in add],'diagnostics':diagnostics,'new_model_generated':False},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
