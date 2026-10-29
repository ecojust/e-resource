"""Ray probes of delivered GLBs, independent of builder part labels."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import trimesh

p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parent.parent
g=json.loads((root/'geometry-input.json').read_text());x=g['architecture_X_EN'];y=g['architecture_Y_EN']
r=np.array([[x[0],y[0],0],[0,0,1],[-x[1],-y[1],0]])
s=trimesh.load(a.glb,force='scene',process=False);meshes=list(s.geometry.values())
materials=np.concatenate([[m.visual.material.name]*len(m.faces) for m in meshes]);mesh=trimesh.util.concatenate(meshes)
def hit(point,direction):
 origin=np.array(point)@r.T;direction=np.array(direction)@r.T
 locations,_,faces=mesh.ray.intersects_location([origin],[direction],multiple_hits=True)
 assert len(locations),'No ray hit'
 distances=np.linalg.norm(locations-origin,axis=1);i=np.argmin(distances)
 return float(distances[i]),str(materials[faces[i]])
arches=[]
for cx in [-6,-2,2,6]:
 distance,material=hit([cx+.25,-10,2.2],[0,1,0])
 assert 3.8<distance<4.5 and material in ['glass','red wood'],(cx,distance,material)
 arches.append({'x':cx+.25,'first_hit_distance_m':distance,'material':material})
windows=[]
for cx in [2,6,-4]:
 distance,material=hit([cx+.22,-10,5.4],[0,1,0])
 assert abs(distance-2.02)<2e-5 and material=='glass',(cx,distance,material)
 windows.append({'x':cx+.22,'glass_inset_m':distance-1.8})
ceiling=[]
for cx in [-6,-2,2,6]:
 distance,material=hit([cx,-10,4.48],[0,1,0])
 assert abs(distance-1.8)<2e-5 and material=='pebbledash',('Ceiling leaks through facade',cx,distance,material)
 coincident=[]
 for part in meshes:
  loc,_,_=part.ray.intersects_location([np.array([cx,-10,4.48])@r.T],[np.array([0,1,0])@r.T],multiple_hits=True)
  if len(loc) and np.any(abs(np.linalg.norm(loc-np.array([cx,-10,4.48])@r.T,axis=1)-1.8)<2e-5):coincident.append(part.visual.material.name)
 assert set(coincident)=={'pebbledash'},('Coplanar facade materials',cx,coincident)
 ceiling.append({'x':cx,'material':material,'distance_m':distance,'coincident_materials':coincident})
steps=[]
for i in range(6):
 distance,material=hit([6,-8.2-(6-i-.5)*.28,2],[0,0,-1]);height=2-distance
 assert abs(height-(i+1)*.075)<2e-5 and material=='stone',(i,height,material)
 steps.append(height)
side_faces=[]
for sign in [-1,1]:
 for yy in [-8.05,-5.79,8.05]:
  for z in [2.17,6.13]:
   origin=np.array([sign*10,yy,z])@r.T;direction=np.array([-sign,0,0])@r.T
   faces,_=mesh.ray.intersects_id([origin],[direction],return_locations=False,multiple_hits=True)
   normals=mesh.face_normals[faces];dist=np.einsum('ij,ij->i',normals,mesh.triangles[faces,0]-origin)/(normals@direction)
   count=int(np.sum(abs(dist-1.2)<2e-5))
   assert count==1,('Overlapping side-wall/end-cap faces',sign,yy,z,count)
   side_faces.append({'side':sign,'y':yy,'z':z,'exterior_face_count':count})
report={'raw_sha256':hashlib.sha256(a.glb.read_bytes()).hexdigest(),'four_open_arches_to_recessed_doors':arches,'upper_windows_actual_glass_inset':windows,'ceiling_not_exposed_at_front':ceiling,'six_tread_heights_m':steps,'no_coplanar_side_wall_end_caps':side_faces,'scope':'Geometry probes, not measured dimensions or walking acceptance'}
a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
