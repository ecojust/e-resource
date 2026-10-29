"""Check Yimen source solids, genuine grille apertures, closed curtain and separate height claims."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import trimesh
from build_model import Yimen,ID,P
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();reports={}
for role in ['raw','lod']:
 path=a.assets/f'{ID}-{role}.glb';scene=trimesh.load(path,force='scene',process=True);meshes=list(scene.geometry.values());assert meshes
 for m in meshes:
  assert np.isfinite(m.vertices).all() and (m.area_faces>1e-12).all();m.merge_vertices(merge_norm=True,merge_tex=True);assert m.is_winding_consistent and m.volume>0
 authored=Yimen(role=='lod').finish()
 for part in authored.b.parts:
  m=trimesh.Trimesh(part['vertices'],part['triangles'],process=True);assert m.is_watertight and m.is_winding_consistent and m.volume>0,part['label']
 triangles=sum(len(m.faces) for m in meshes);assert triangles==sum(len(part['triangles']) for part in authored.b.parts)
 bounds=scene.bounds;assert abs(bounds[0,1])<1e-6 and abs(bounds[1,1]-7.0)<1e-5
 total=trimesh.util.concatenate(meshes);origins=[]
 for g in authored.grilles:
  origins.append([g['x0']+(g['x1']-g['x0'])/(2*g['grid'][0]),g['bottom']+(g['top']-g['bottom'])/(2*g['grid'][1]),7])
 locations,rays,_=total.ray.intersects_location(origins,[[0,0,-1]]*len(origins));first=[float(locations[rays==i,2].max()) for i in range(len(origins))];assert len(first)==16 and np.allclose(first,4.51,atol=1e-5),first
 hit,_,_=total.ray.intersects_location([[0,2.0,7]],[[0,0,-1]]);assert 4.87<float(hit[:,2].max())<4.96
 base=next(x for x in authored.b.parts if x['label']=='interpreted-base');vb=np.array(base['vertices']);assert np.allclose(vb.max(0)-vb.min(0),[10.6,9.7,.22])
 assert sum(x['label']=='observed-inner-upright' for x in authored.b.parts)==2
 assert sum(x['label']=='observed-form-curved-end-wall' for x in authored.b.parts)==2
 assert not any('door-leaf' in x['label'] for x in authored.b.parts)
 reports[role]={'representation':'Uncompressed authored source; final packed files checked separately','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':triangles,'bounds_glb':bounds.tolist(),'actual_total_envelope_width_depth_height_m':(bounds[1]-bounds[0])[[0,2,1]].tolist(),'interpreted_base_width_depth_m':[10.6,9.7],'authored_closed_solids':len(authored.b.parts),'authored_solids_watertight':True,'nondegenerate':True,'consistent_winding':True,'grille_fields_tested':16,'all_grille_cell_rays_reach_recessed_backing':True,'central_curtain_ray_hits_closed_solid':True,'hidden_door_leaves_not_invented':True,'observed_inner_uprights':2,'curved_end_walls':2,'source_height_m':9.07,'estimated_model_height_m':7.0,'height_reconciled':False,'photo_scale_accepted':False,'scope':'Form candidate with explicit estimated dimensions, unobserved rear, two estimated steps and blank sign. No geographic registration.'}
assert reports['lod']['triangles']<reports['raw']['triangles'];a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
