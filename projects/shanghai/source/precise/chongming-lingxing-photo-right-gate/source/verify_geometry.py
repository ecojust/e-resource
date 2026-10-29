"""Actual exported historical right portal checks: frame opening and closed/slatted leaves."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import trimesh
from build_model import RightGate
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();reports={}
for role in ['raw','lod']:
 path=a.assets/f'chongming-lingxing-photo-right-gate-{role}.glb';scene=trimesh.load(path,force='scene',process=True);meshes=list(scene.geometry.values());assert meshes
 for m in meshes:
  assert np.isfinite(m.vertices).all() and (m.area_faces>1e-12).all()
  m.merge_vertices(merge_norm=True,merge_tex=True)
  assert m.is_winding_consistent and m.volume>0
 bounds=scene.bounds;assert abs(bounds[0,1])<1e-6 and abs(bounds[1,1]-4.88)<1e-5
 authored=RightGate(role=='lod').finish()
 for part in authored.b.parts:
  component=trimesh.Trimesh(part['vertices'],part['triangles'],process=True)
  assert component.is_watertight and component.is_winding_consistent and component.volume>0,part['label']
 assert sum(len(m.faces) for m in meshes)==sum(len(v['triangles']) for v in authored.b.parts)
 stone=trimesh.util.concatenate([m for m in meshes if m.visual.material.name.startswith('stone')])
 locations,rays,_=stone.ray.intersects_location([[0,1.8,0],[0,1.8,0],[0,0,0]],[[1,0,0],[-1,0,0],[0,1,0]])
 nearest=[]
 for i,start in enumerate([[0,1.8,0],[0,1.8,0],[0,0,0]]):nearest.append(float(np.linalg.norm(locations[rays==i]-start,axis=1).min()))
 assert abs(nearest[0]+nearest[1]-2.3)<1e-5 and abs(nearest[2]-3.2)<1e-5,nearest
 for sign in [-1,1]:assert abs(stone.vertices[stone.vertices[:,0]*sign>1.0,1].max()-4.88)<1e-5
 total=trimesh.util.concatenate(meshes)
 assert total.ray.intersects_any([[0,1.8,3],[.5,.58,3]],[[0,0,-1],[0,0,-1]]).all(),'Closed batten/lower board was opened'
 gap=.5715+1.131/2-.19-(1.131-.38)/10
 assert not total.ray.intersects_any([[-gap,1.8,3],[gap,1.8,3]],[[0,0,-1],[0,0,-1]]).any(),'Slat gaps filled'
 reports[role]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':sum(len(m.faces) for m in meshes),'bounds_glb':bounds.tolist(),'authored_closed_solids':len(authored.b.parts),'authored_solids_watertight':True,'nondegenerate':True,'consistent_winding':True,'measured_clear_stone_opening_m':[nearest[0]+nearest[1],nearest[2]],'both_upper_posts_present':True,'closed_centre_and_lower_board_block_rays':True,'upper_slat_gap_rays_clear':True,'scope':'Photo-right historical portal; closed pose inferred; no geographic or full restoration acceptance'}
assert reports['lod']['triangles']<reports['raw']['triangles']
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
