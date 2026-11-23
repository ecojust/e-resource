"""Test an entire source-owner replacement in isolation, prior to any live registration."""
from pathlib import Path
import gzip, sys, json, os, math, hashlib, runpy
import numpy as np
import shapely as ge
from shapely.geometry import Polygon, MultiPoint, shape, mapping, Point
w=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes())
def write(p,v): tmp=p.with_suffix('.new');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
cfg=read(w/'portal-frame.json');registry=read(w/'footprint-review.json');mod=runpy.run_path(str(w/'decode-source.py')); own=2849;groups=cfg['groups'];owners=[own]+cfg['checked_neighbors']; selected={};src=mod['polygons'][own]
for data in groups:
 for level,t,ids,separation in mod['decode'](data):
  if level=='far' and (own,level) in selected:continue
  for id in owners:
   tri=t[ids==id]
   if len(tri)==0:continue
   key=(id,level);assert key not in selected
   p=np.round(tri[:,:,:2].reshape(-1,2),4);bound=ge.union_all(ge.polygons(tri[:,:,:2]),grid_size=.002)
   selected[key]=[bound,float(tri[:,:,2].min()),float(tri[:,:,2].max()),len(tri),np.unique(p,axis=0)]
assert len(selected)==2*len(owners),(set(owners),selected.keys())
actual=ge.union_all([src,selected[own,'near'][0],selected[own,'far'][0]])
# Reproduce a source-scoped geometry that also contains small facade/roof offsets in the old near mesh.
margin=max(float(np.max(ge.distance(ge.points(selected[own,level][4]),src))) for level in ['near','far'])
pad=math.ceil((margin+.06)*100)/100;cut=src.buffer(pad,quad_segs=1,join_style='mitre')
Q=6371008.8*math.cos(math.radians(cfg['anchor'][1]));b=math.asinh(math.tan(math.radians(cfg['anchor'][1])));ang=math.radians(cfg['runtime_heading_degrees']);axes=np.array([[math.cos(ang),-math.sin(ang)],[math.sin(ang),math.cos(ang)]])
def unproject(poly):
 east,north=(poly@axes).T;return np.column_stack((cfg['anchor'][0]+np.degrees(east/Q),np.degrees(np.arctan(np.sinh(b+north/Q)))))
results=[]
for id in owners:
 for level in ['near','far']:
  poly,lo,hi,num,pts=selected[id,level];inside=ge.covers(cut,ge.points(pts));row=dict(id=id,level=level,source_triangles=num,height_range=[lo,hi],source_projection_m2=poly.area,actual_projection_inside_m2=cut.intersection(poly).area,minimum_distance_m=poly.distance(cut),unique_vertices_inside=int(np.count_nonzero(inside)),unique_vertices=len(pts))
  if id==own:assert inside.all() and abs(row['actual_projection_inside_m2']-poly.area)<.0001
  else:assert not inside.any() and row['actual_projection_inside_m2']<.0001,(id,level,row)
  results.append(row)
report=dict(passed=True,status='pre-authoring measurement; no new model or active map integration asserted',id=registry['id'],source_owner=own,checked_neighbors=cfg['checked_neighbors'],source_height_m=37.608,source_area_m2=src.area,actual_near_far_maximum_outside_original_m=margin,source_scoped_planar_pad_m=pad,proposed_cut_local=mapping(cut),proposed_cut_wgs84=mapping(ge.transform(cut,unproject)),actual_owner_meshes_and_neighbors=results)
write(w/'source-owner-selection.json',report)
print('pad',margin,pad,'neighbor_min', min(v['minimum_distance_m'] for v in results if v['id']!=own),'counts',[(v['level'],v['source_triangles'])for v in results if v['id']==own])
