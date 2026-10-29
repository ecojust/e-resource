"""Check distributed bytes, placed-scene counts, compressed geometry and open long cores. MIT."""
import argparse,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
import trimesh
ID='chongming-stele-corridors'
def document(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n])
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--gltfpack',type=Path,required=True);a=p.parse_args()
m=json.loads((a.assets/'manifest.json').read_text());g=json.loads((a.audit/'geometry.json').read_text());native=json.loads((a.audit/'native.json').read_text());browser=json.loads((a.audit/'browser.json').read_text())
assert m['id']==ID and m['model_scope']['modeled_baseline_total_length']==61 and not m['model_scope']['north_south_geometry_created']
assert m['model_scope']['component_count']==2 and m['display_layout']['placement_only'] and not m['display_layout']['measured_courtyard_width']
assert m['historical_collection_count']==53 and not m['inscriptions_reconstructed'];assert native['model_meshes']==native['independent_editable_components_after_reopen']==2
assert not browser['errors'];report={'id':ID,'assets':{},'native_independently_editable_components':2,'source_total76_7_and_modeled61_separately_recorded':True,'south_north_short_components_absent':True,'display_spacing_not_measured_courtyard':True,'all_asset_files_under100MB':True}
with tempfile.TemporaryDirectory(prefix='stele-corridors-decode-') as tmp:
 for role,entry in m['assets'].items():
  path=a.assets/entry['file'];b=path.read_bytes();sha=hashlib.sha256(b).hexdigest();assert sha==entry['sha256'] and len(b)==entry['bytes'] and len(b)<100_000_000
  r={'bytes':len(b),'sha256':sha,'manifest_matches':True}
  if role=='native':
   assert sha==native['sha256'];assert native['source_raw_sha256']==g['raw']['sha256']==m['assets']['raw']['sha256'];report['assets'][role]=r;continue
  d=document(path);assert d['extras']['id']==ID and d['extras']['modeled_components']['total_modeled_baseline_length_m']==61
  assert d['extras']['north_south_pending']['physical_segments_created'] is False and d['extras']['historical_collection_count']==53
  assert not d.get('images');assert {'East_long_component','West_long_component'}.issubset({x.get('name') for x in d['nodes']})
  decoded=path
  if role!='raw':
   decoded=Path(tmp)/(role+'.glb');subprocess.run([str(a.gltfpack.resolve()),'-i',str(path),'-o',str(decoded),'-noq','-vnf','-km','-kn','-ke'],check=True)
  scene=trimesh.load(decoded,force='scene',process=False);meshes=list(scene.dump());triangles=sum(len(q.faces) for q in meshes)
  assert triangles==entry['triangles'];assert np.allclose(scene.bounds,g['raw']['bounds_glb'],atol=1e-5)
  assert all(np.isfinite(q.vertices).all() and (q.area_faces>1e-12).all() and q.is_winding_consistent for q in meshes)
  total=trimesh.util.concatenate(meshes);origins=[[-16,h,-(c+off)] for c in [-3.5,3.5] for off in [-.55,0,.55] for h in [.25,1,1.7,2.8]]
  assert not total.ray.intersects_any(origins,[[1,0,0]]*len(origins)).any()
  if role in ['full','lod']:assert browser[role]['modelId']==ID and browser[role]['triangles']==triangles
  r.update({'triangles_after_decode_including_placed_components':triangles,'finite_vertices':True,'zero_degenerate_faces':True,'consistent_winding':True,'bounds_match_source':True,'two_named_components_preserved':True,'longitudinal_core_rays_clear':len(origins),'embedded_images':0});report['assets'][role]=r
(a.audit/'packaged.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
