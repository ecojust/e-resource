"""Package original Jiangwan swimming hall assets with explicit estimate metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='yangpu-jiangwan-swimming-hall'
def document(path):
 data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0]
 return json.loads(data[20:20+size])
def preserve_metadata(path,source):
 data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);doc['extras']=document(source)['extras']
 payload=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4);tail=data[20+size:]
 path.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),0x4E4F534A)+payload+tail)
 assert document(path)['extras']==document(source)['extras']
def record(path):
 data=path.read_bytes();assert 0<len(data)<100000000
 row={'file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 if path.suffix=='.glb':
  d=document(path);assert not d.get('images') and not d.get('textures')
  row['triangles']=sum(d['accessors'][p['indices']]['count']//3 for n in d['nodes'] if 'mesh' in n for p in d['meshes'][n['mesh']]['primitives'])
 return row

def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--lod',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',type=Path,required=True);a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=True);assets={}
 for source in [a.raw,a.lod]:assert document(source)['extras']['id']==ID
 for role,source,suffix in [('raw',a.raw,'-raw.glb'),('native',a.native,'.blend')]:
  dst=a.out/(ID+suffix)
  if source.resolve()!=dst.resolve():shutil.copyfile(source,dst)
  assets[role]=record(dst)
 for role,source,suffix in [('full',a.raw,'-web.glb'),('lod',a.lod,'-lod.glb')]:
  dst=a.out/(ID+suffix)
  subprocess.run([str(a.gltfpack),'-i',str(source),'-o',str(dst),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
  preserve_metadata(dst,source);assets[role]=record(dst)
  assert assets[role]['triangles']==record(source)['triangles']
 d=document(a.raw);meta=d['extras'];assert len(d['nodes'])==1 and not any(k in d['nodes'][0] for k in ['matrix','translation','rotation','scale','children'])
 pos=[d['accessors'][p['attributes']['POSITION']] for m in d['meshes'] for p in m['primitives']]
 lo=[min(v['min'][i] for v in pos) for i in range(3)];hi=[max(v['max'][i] for v in pos) for i in range(3)]
 bounds={'min':[lo[0],-hi[2],lo[1]],'max':[hi[0],-lo[2],hi[1]]}
 tool_version=subprocess.run([str(a.gltfpack),'-v'],capture_output=True,text=True)
 params=json.loads(Path(__file__).with_name('model-parameters.json').read_text())
 xy=params['source_footprint_enu']['coordinates'][0];mapped=[max(v[i] for v in xy)-min(v[i] for v in xy) for i in range(2)]
 manifest={'id':ID,'name':'江湾游泳馆（历史池馆与现状屋盖）','status':meta['status'],
   'viewer_page':'jiangwan-swimming-hall.html','audit_directory':'data/audit/jiangwan-swimming-hall-v1/',
   'authored_bounds_enu_m':bounds,
   'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],[bounds['max'][i]-bounds['min'][i] for i in range(3)])),
   'model_scope_zh':'独立泳馆红砖折角围体、北浅石单拱阶梯入口、池侧砖附房及小尖顶、现代浅弧高屋盖与低翼和采光带；非1934露天原状，不含内部池体或外围白棚。',
   'documented_existing_height_m':None,'all_elevation_datums_estimated':True,
   'selected_modern_roof_apex_m':params['selected_roof_apex_m'],
   'selected_modern_roof_edge_m':params['selected_roof_edge_height_m'],
   'selected_perimeter_wall_m':params['selected_perimeter_height_m'],
   'selected_north_central_wall_m':params['selected_north_central_wall_m'],
   'selected_north_wing_wall_m':params['selected_north_annex_wall_m'],
   'selected_north_pool_side_eave_m':params['selected_north_pool_side_eave_m'],
   'selected_north_pool_side_pitched_roof_apex_m':params['selected_north_pool_side_pitched_roof_apex_m'],
   'selected_north_central_ancillary_cover_m':params['selected_north_ancillary_cover_m'],
   'selected_north_side_ancillary_cover_m':params['selected_north_side_ancillary_cover_m'],
   'source_mapped_building_dimensions_m':mapped,
   'historic_pool_water_body_dimensions_m':[50,20],
   'historic_pool_and_mapped_building_are_different_objects':True,
   'roof_addition_reported_in_2006_12_29_news':True,
   'current_roof_cladding_material_and_exact_completion_date_unknown':True,
   'original_1934_open_pool_state_claimed':False,
   'photographic_archive_date_not_assumed_capture_date':True,
   'northern_public_facade_single_arch_upper_central_slots':5,
   'northern_pool_side_pitched_roof_is_not_public_facade_ornament':True,
   'source_wall_joints_mitered_and_roof_edge_fascias_built':True,
   'door_backstops_bound_unmodeled_interiors':True,
   'central_translucent_bands_and_clerestory_separate_from_opaque_cover':True,
   'obscured_long_side_arches_and_north_transition_elevations_estimated':True,
   'photos_embedded':False,'pool_interior_modeled':False,'interiors_modeled':False,'underground_modeled':False,
   'outdoor_stadium_modeled':False,'gymnasium_modeled':False,'external_white_shelters_modeled':False,'site_slab_modeled':False,
   'original_geometry':True,'geometry_license':'MIT','map_reference_license':'ODbL-1.0',
   'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,
      'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated',
      'map_source_correction':'bounded runtime contract',
      'source_metadata_scope':'Only independent swimming hall source1666 is eligible for replacement; northern gymnasium, outdoor stadium, external white shelters and other city sources remain. Assets do not execute source replacement.'},
   'walk_integration':False,'complete_photo_reconstruction_accepted':False,
   'source_register':'source/precise/'+ID+'/source-register.json',
   'source_candidate_metadata':meta,'assets':assets,
   'packaging_tool':{'version_output':(tool_version.stdout+tool_version.stderr).strip(),
      'executable_sha256':hashlib.sha256(a.gltfpack.read_bytes()).hexdigest(),
      'flags':['-cc','-noq','-vnf','-km','-kn','-ke']}}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(assets,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
