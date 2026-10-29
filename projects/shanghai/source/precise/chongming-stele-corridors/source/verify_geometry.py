"""Check two long components, source closed solids and actual open gallery rays. MIT."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
import trimesh
from build_model import SteleCorridor,ID,P
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();reports={}
for role in ['raw','lod']:
 path=a.assets/f'{ID}-{role}.glb';data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);assert len(doc['nodes'])==2 and len(doc['scenes'][0]['nodes'])==2
 assert doc['extras']['north_south_pending']['physical_segments_created'] is False
 scene=trimesh.load(path,force='scene',process=False);meshes=list(scene.dump())
 assert meshes
 for m in meshes:
  assert np.isfinite(m.vertices).all() and (m.area_faces>1e-12).all();assert m.is_winding_consistent and m.volume>0
 authored=SteleCorridor(role=='lod').finish()
 for part in authored.b.parts:
  m=trimesh.Trimesh(part['vertices'],part['triangles'],process=True);assert m.is_watertight and m.is_winding_consistent and m.volume>0,part['label']
  if part['label']=='estimated-upper-cross-member':
   v=np.array(part['vertices']);assert all(z <= authored.roofz(y)-.06+1e-6 for _,y,z in v), 'Upper cross member protrudes through roof shell'
 count=sum(len(m.faces) for m in meshes);assert count==2*sum(len(part['triangles']) for part in authored.b.parts)
 total=trimesh.util.concatenate(meshes);bounds=scene.bounds;assert abs(bounds[0,1])<1e-6 and abs(bounds[1,1]-4.6)<1e-5
 base=next(x for x in authored.b.parts if x['label']=='interpreted-30.5x2.5-base');v=np.array(base['vertices']);assert np.allclose(v.max(0)-v.min(0),[30.5,2.5,.15])
 assert sum(p['label']=='estimated-blank-stele-panel' for p in authored.b.parts)==20
 assert sum(p['label']=='open-round-column' for p in authored.b.parts)==11
 #24 complete longitudinal probes through a1.1m-wide core at four heights.
 longitudinal=[]
 for c in P['display_y_centres']:
  for off in [-.55,0,.55]:
   for h in [.25,1,1.7,2.8]:longitudinal.append([-16,h,-(c+off)])
 hits=total.ray.intersects_any(longitudinal,[[1,0,0]]*len(longitudinal));assert not hits.any()
 #20 transverse rays enter from the open side; first hit is wall/panel, not a filled facade.
 origins=[];expected=[]
 for c in P['display_y_centres']:
  for x in np.linspace(-13.5,13.5,10):origins.append([x,1.7,-(c-2)]);expected.append(-c)
 loc,ray,_=total.ray.intersects_location(origins,[[0,0,-1]]*len(origins));first=[float(loc[ray==i,2].max()) for i in range(len(origins))]
 assert all(-1.031 < z-e < -.999 for z,e in zip(first,expected)),first
 #Controls intentionally hit the front column and the lower cross beam.
 for c in P['display_y_centres']:
  loc,_,_=total.ray.intersects_location([[0,1.0,-(c-2)]],[[0,0,-1]]);column=next(part for part in authored.b.parts if part['label']=='open-round-column' and abs(np.array(part['vertices'])[:,0].mean())<1e-6);miny=np.array(column['vertices'])[:,1].min();assert np.isclose(loc[:,2].max(),-c-miny,atol=1e-5)
  loc,_,_=total.ray.intersects_location([[0,1.7,-c]],[[0,1,0]]);assert np.isclose(loc[:,1].min(),3.32,atol=1e-5)
 reports[role]={'representation':'Uncompressed two-node authored scene; final packed variants independently decoded','sha256':hashlib.sha256(data).hexdigest(),'triangles':count,'bounds_glb':bounds.tolist(),'actual_total_display_envelope_width_depth_height_m':(bounds[1]-bounds[0])[[0,2,1]].tolist(),'component_count':2,'each_base_length_width_m':[30.5,2.5],'modeled_long_baseline_length_m':61.0,'north_south_combined_pending_m':15.7,'north_south_geometry_created':False,'estimated_total_height_m':4.6,'authored_closed_solids':len(authored.b.parts)*2,'authored_solids_watertight':True,'finite_vertices':True,'nondegenerate':True,'consistent_winding':True,'upper_cross_members_below_roof_shell':True,'blank_panels_per_component':20,'blank_panel_layout_estimated':True,'historical53_not_a_layout_inventory':True,'longitudinal_clear_core_rays':len(longitudinal),'longitudinal_tested_heights_m':[.25,1,1.7,2.8],'longitudinal_tested_core_width_m':1.1,'transverse_open_side_rays_reach_wall_or_panel':len(origins),'front_column_and_cross_beam_control_hits':True,'cross_beam_bottom_m':3.32,'floor_top_m':.175,'conservative_footing_clear_width_m':1.615,'viewer_scope':'Only exterior of complete scene envelope; geometric corridor clearance is not viewer through-gallery traversal acceptance','display_only_centres_y_m':P['display_y_centres'],'courtyard_width_measured':False}
assert reports['lod']['triangles']<reports['raw']['triangles'];a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
