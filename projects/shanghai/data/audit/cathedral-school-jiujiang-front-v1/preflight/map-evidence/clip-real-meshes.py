"""Measure actual 3D surface area removed from the two source meshes after registration."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json,sys,hashlib,runpy,shutil
import numpy as np
import shapely
from shapely.geometry import box
w=Path(__file__).resolve().parent;p=Path('/workspace/e-resource/projects/shanghai');sys.path.insert(0,str(p/'tools'))
from candidate_placement_meshes import PlacementMeshes
read=lambda f:json.loads(f.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
src=read(w/'original-review.json');base={**src,'author_frame':read(w/'school-author-frame.json')};ground=read(w/'measured-entrance-ground.json');bounds=ground['mask_xy_m'];mask=box(*bounds);groups=runpy.run_path(str(p/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
source=1810;rows={};kinds={};x0,y0,x1,y1=bounds
def polygon_area(poly):
 a=np.asarray(poly);return float(np.linalg.norm(np.cross(a[1:-1]-a[0],a[2:]-a[0]),axis=1).sum()/2) if len(a)>2 else 0.
def trim(poly,axis,limit,side):
 if not len(poly):return []
 out=[];prev=poly[-1];d0=(prev[axis]-limit)*side
 for nxt in poly:
  d1=(nxt[axis]-limit)*side
  if (d0<0)!=(d1<0):out.append(prev+(nxt-prev)*d0/(d0-d1))
  if d1>=0:out.append(nxt)
  prev=nxt;d0=d1
 return out
parent=max([Path('/tmp'),Path('/dev/shm')],key=lambda q:shutil.disk_usage(q).free)
with TemporaryDirectory(dir=parent,prefix='school281-triangles-')as t:
 t=Path(t)
 for e in src['frozen_bindings']:
  n=Path(e['repository_path']).name;(t/n).symlink_to((w/'inputs'/n).resolve())
 m=PlacementMeshes(p,t,base)
 for group in src['near_tiles']:
  for level,tris,ids,ambiguous in groups(m,group):
   data=rows.setdefault(level,{})
   for i in set(ids):
    tri=tris[ids==i]; bb=shapely.convex_hull(shapely.polygons(tri[:,:,:2]));distance=float(shapely.distance(bb,mask).min());key=str(int(i));total=float(np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1).sum()/2);removed=0.;split=0;full=0
    if i==source:
     for index in np.where(shapely.intersects(bb,mask))[0]:
      face=tri[index];clipped=face
      for axis,limit,side in [(0,x0,1),(0,x1,-1),(1,y0,1),(1,y1,-1)]:clipped=trim(clipped,axis,limit,side)
      a=polygon_area(clipped);removed+=a
      if a>1e-8:
       if abs(a-polygon_area(face))<1e-8:full+=1
       else:split+=1
     assert full+split and removed>15
    else:assert distance>.01,(level,i,distance)
    record=dict(original_triangles=len(tri),original_surface_m2=total,clipped_surface_m2=removed,remaining_surface_m2=total-removed,retained_surface_ratio=(total-removed)/total,cut_through_triangles=split,fully_removed_triangles=full,closest_mesh_to_mask_m=distance,xyz_sha256=sha(tri.astype('<f8').tobytes()),max_z_m=float(tri[:,:,2].max()))
    if key in data:assert data[key]==record
    data[key]=record
   (t/('baseline-'+level+'-triangles.f64')).unlink(missing_ok=True)
 print([(v,rows[v][str(source)])for v in rows],flush=True)
assert set(rows)=={'near','far'} and set(rows['near'])==set(rows['far']) and all(str(k)in rows['near']for k in [616,587,1810]);out=dict(passed=True,original_review_sha256=sha((w/'original-review.json').read_bytes()),frame=base['author_frame'],mask_xy=bounds,model_geometry=read(w/'ground-placement-fragment.json')['model_geometry_sha256'],scope='Source city triangles cut to the four vertical planes. Every neighboring owner is measured against the cut, including the church and bell tower. Visual and walkable replacements are verified individually in the runtime.',variants=rows);(w/'physical-mesh-cut.json').write_text(json.dumps(out,indent=1)+'\n')
