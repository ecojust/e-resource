"""Check actual exported envelope, document-base interpretation and recessed window panes."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import trimesh
from build_model import Shrine
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();reports={}
for role in ['raw','lod']:
 path=a.assets/f'chongming-xiangxian-shrine-{role}.glb';scene=trimesh.load(path,force='scene',process=True);meshes=list(scene.geometry.values());assert meshes
 for m in meshes:
  assert np.isfinite(m.vertices).all() and (m.area_faces>1e-12).all()
  m.merge_vertices(merge_norm=True,merge_tex=True)
  assert m.is_winding_consistent and m.volume>0
 bounds=scene.bounds;assert abs(bounds[0,1])<1e-6 and abs(bounds[1,1]-6.5)<1e-5
 authored=Shrine(role=='lod').finish()
 for part in authored.b.parts:
  component=trimesh.Trimesh(part['vertices'],part['triangles'],process=True)
  assert component.is_watertight and component.is_winding_consistent and component.volume>0,part['label']
 assert sum(len(m.faces) for m in meshes)==sum(len(v['triangles']) for v in authored.b.parts)
 total=trimesh.util.concatenate(meshes)
 ground=total.vertices[np.abs(total.vertices[:,1])<1e-6]
 base=(ground.max(0)-ground.min(0))[[0,2]]
 assert np.allclose(base,[8.8,6.6],atol=1e-5)
 # At each lattice cell centre, first visible surface should be the inset backing,
 # rather than an accidentally uncut plaster wall or opaque grid panel.
 loc,ray,_=total.ray.intersects_location([[-2.8,1.65,5],[2.8,1.65,5]],[[0,0,-1],[0,0,-1]])
 first=[float(loc[ray==i,2].max()) for i in range(2)]
 assert np.allclose(first,[2.78,2.78],atol=1e-5),first
 assert total.ray.intersects_any([[0,1.8,5]],[[0,0,-1]]).all(),'Closed entrance missing'
 span=bounds[1]-bounds[0]
 reports[role]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':sum(len(m.faces) for m in meshes),'bounds_glb':bounds.tolist(),'actual_total_envelope_width_depth_height_m':span[[0,2,1]].tolist(),'interpreted_base_width_depth_m':base.tolist(),'documentary_dimensions_are_not_eave_envelope':True,'authored_closed_solids':len(authored.b.parts),'authored_solids_watertight':True,'nondegenerate':True,'consistent_winding':True,'window_cell_rays_reach_inset_backing':True,'closed_central_door_present':True,'scope':'Text-size candidate only; roof/windows unverified; no photographic or geographic acceptance'}
assert reports['lod']['triangles']<reports['raw']['triangles']
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
