"""Actual GLB check for horizontal upward grey-roof/stone cap overlap.

This scans every shared horizontal elevation, not only the intended roof levels.
It detects coplanar material surfaces that can flicker in a rasterized renderer;
closure tests alone do not detect them. Polygon projection uses serialized FLOAT32.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from verify_junctions import load,ray

def check(path):
 triangles,materials=load(path);normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);horizontal=(np.ptp(triangles[:,:,2],axis=1)<1e-5)&(normals[:,2]>1e-10);groups={}
 for tri,mat in zip(triangles[horizontal],materials[horizontal]):
  if mat not in ['grey roof','pale grey stone','light stone coping']:continue
  key=(round(float(tri[:,2].mean()),5),str(mat));groups.setdefault(key,[]).append(Polygon(tri[:,:2]))
 unions={key:unary_union(value)for key,value in groups.items()};rows=[]
 for z,mat in sorted(unions):
  if mat!='grey roof':continue
  for stone in ['pale grey stone','light stone coping']:
   if (z,stone) not in unions:continue
   roof=unions[(z,mat)];wall=unions[(z,stone)];area=roof.intersection(wall).area
   rows.append({'z_m':z,'roof_material':mat,'other_material':stone,'roof_projected_area_m2':roof.area,'other_projected_area_m2':wall.area,'coplanar_intersection_area_m2':area,'passed':area<1e-7})
 contacts=[]
 for name,origin,material,z in [
  ('front wing stone upstand',[-14.50,10,10.9],'pale grey stone',10.6),
  ('front wing inset roof',[-14.35,10,10.9],'grey roof',10.56),
  ('outer terrace stone upstand',[-16.9,.4,12.4],'pale grey stone',12.2),
  ('outer terrace inset roof',[-16.8,.4,12.4],'grey roof',12.16),
  ('rear wing stone upstand',[20,-9.26,8.4],'pale grey stone',8.2),
  ('rear wing inset roof',[20,-9.15,8.4],'grey roof',8.16),
  ('east portal stone upstand',[25.08,1.15,8.9],'pale grey stone',8.65),
  ('east portal inset roof',[24.98,1.15,8.9],'grey roof',8.61)]:
  hit=ray(triangles,materials,origin,[0,0,-1]);passed=bool(hit and hit['materials_at_nearest_hit']==[material] and abs(hit['point_enu'][2]-z)<.002)
  contacts.append({'name':name,'origin_enu':origin,'expected_material':material,'expected_z_m':z,'hit':hit,'passed':passed})
 return {'id':'yangpu-china-aviation-association-building','file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scan':'All upward horizontal grey roof triangles against all upward horizontal pale grey stone and light stone coping triangles, at every shared serialized elevation. No construction function or expected roof-level list used.','upward_horizontal_triangles_scanned':int(horizontal.sum()),'grey_roof_elevations_m':sorted(z for z,m in unions if m=='grey roof'),'shared_elevation_results':rows,'total_intersection_area_m2':sum(r['coplanar_intersection_area_m2']for r in rows),'roof_wall_contact_rays':contacts,'passed':all(r['passed']for r in rows+contacts),'limitation':'Checks horizontal same-plane surface overlap; it does not assert a complete all-orientation mesh boolean union or exact construction detailing.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=check(a.asset);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed']else 1)
