"""Verify actual exported meshes and framed opening; keep source components separate."""
import argparse,json,hashlib,math
from pathlib import Path
import numpy as np
import trimesh
from build_model import Portal
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();reports={}
for role in ['raw','lod']:
 path=a.assets/f'chongming-lingxing-gate-{role}.glb'
 scene=trimesh.load(path,force='scene',process=True);meshes=list(scene.geometry.values());assert meshes
 for m in meshes:
  assert np.isfinite(m.vertices).all() and (m.area_faces>1e-12).all()
  m.merge_vertices(merge_norm=True,merge_tex=True)
  assert m.is_winding_consistent and m.volume>0
 bounds=scene.bounds
 assert abs(bounds[0,1])<1e-6 and abs(bounds[1,1]-5.85)<1e-5
 authored=Portal(role=='lod').finish()
 for part in authored.b.parts:
  component=trimesh.Trimesh(part['vertices'],part['triangles'],process=True)
  assert component.is_watertight and component.is_winding_consistent and component.volume>0,part['label']
 assert sum(len(m.faces) for m in meshes)==sum(len(v['triangles']) for v in authored.b.parts)
 stone=trimesh.util.concatenate([m for m in meshes if m.visual.material.name.startswith('granite')])
 locations,rays,_=stone.ray.intersects_location([[0,1.8,0],[0,1.8,0],[0,0,0]],[[1,0,0],[-1,0,0],[0,1,0]])
 nearest=[]
 for i,start in enumerate([[0,1.8,0],[0,1.8,0],[0,0,0]]):nearest.append(float(np.linalg.norm(locations[rays==i]-start,axis=1).min()))
 assert abs(nearest[0]+nearest[1]-3.35)<1e-5 and abs(nearest[2]-3.6)<1e-5,nearest
 total=trimesh.util.concatenate(meshes)
 assert not total.ray.intersects_any([[0,1.8,3]],[[0,0,-1]]).any(),'Centre gap blocked'
 # Cast across a real vertical gap between bars of each open door.
 for sign,angle in [(-1,18),(1,67)]:
  angle=math.radians(angle);u=np.array([-sign*math.cos(angle),math.sin(angle),0.]);n=np.array([-u[1],u[0],0.])
  q=np.array([sign*1.65,.04,1.8])+u*(.24+(1.57-.48)/14)
  start=q-n*.25;start=start[[0,2,1]]*[1,1,-1];direction=n[[0,2,1]]*[1,1,-1]
  loc,_,_=total.ray.intersects_location([start],[direction])
  assert not len(loc) or np.linalg.norm(loc-start,axis=1).min()>.5,'Slat opening filled'
 reports[role]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':sum(len(m.faces) for m in meshes),'bounds_glb':bounds.tolist(),'authored_closed_solids':len(authored.b.parts),'authored_solids_watertight':True,'nondegenerate':True,'consistent_winding':True,'measured_clear_stone_opening_m':[nearest[0]+nearest[1],nearest[2]],'central_gap_clear':True,'door_bar_gap_rays_clear':True,'scope':'Central portal only; no entire Lingxing Gate or geographic registration acceptance'}
assert reports['lod']['triangles']<reports['raw']['triangles']
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
