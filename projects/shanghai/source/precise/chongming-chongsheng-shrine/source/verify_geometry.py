"""Validate exported raw/LOD meshes, independently of builder assertions."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import trimesh
from build_model import Shrine
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
reports={}
for role in ['raw','lod']:
 path=a.assets/f'chongming-chongsheng-shrine-{role}.glb'
 scene=trimesh.load(path,force='scene',process=True)
 meshes=list(scene.geometry.values());assert meshes
 for m in meshes:
  assert np.isfinite(m.vertices).all()
  assert (m.area_faces>1e-12).all(),'degenerate triangles'
  m.merge_vertices(merge_norm=True,merge_tex=True)
  assert m.is_winding_consistent,'inconsistent normals'
  assert m.volume>0,'inside-out mesh'
 bounds=scene.bounds
 assert abs(bounds[0,1])<1e-6 and abs(bounds[1,1]-11)<1e-5
 assert np.max(np.abs(bounds[:,0]))<7.4 and np.max(np.abs(bounds[:,2]))<7.1
 authored=Shrine(role=='lod').finish()
 for part in authored.b.parts:
  component=trimesh.Trimesh(part['vertices'],part['triangles'],process=True)
  assert component.is_watertight and component.is_winding_consistent and component.volume>0,part['label']
 assert sum(len(m.faces) for m in meshes)==sum(len(v['triangles']) for v in authored.b.parts)
 reports[role]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':sum(len(m.faces) for m in meshes),'bounds_glb':bounds.tolist(),'authored_closed_solids':len(authored.b.parts),'authored_solids_watertight':True,'material_mesh_note':'Touching separate solids can produce nonmanifold edges when welded together; no whole-building solid union claimed','nondegenerate':True,'consistent_winding':True}
assert reports['lod']['triangles']<reports['raw']['triangles']
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
