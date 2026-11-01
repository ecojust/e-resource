"""Package original former Shanghai city museum assets with explicit estimate metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='yangpu-former-shanghai-city-museum'
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
 manifest={'id':ID,'name':'旧上海市博物馆江湾馆舍','status':meta['status'],
   'viewer_page':'city-museum.html','audit_directory':'data/audit/city-museum-v1/',
   'authored_bounds_enu_m':bounds,
   'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],[bounds['max'][i]-bounds['min'][i] for i in range(3)])),
   'model_scope_zh':'旧市博物馆江湾馆舍：照片参照西主立面、现存两层南北翼及黄瓦重檐门楼；东中后厅仅为简化估计低体量。两院凹独立连接体及医院邻楼不并入，非1930年代原状复原。',
   'documented_existing_height_m':None,'all_elevation_datums_estimated':True,
   'documentary_secondary_wing_height_m':10.5,'documentary_secondary_tower_height_m':24,
   'documentary_height_datums_not_field_verified':True,
   'selected_wing_wall_m':params['selected_wing_wall_m'],
   'selected_tower_base_m':params['selected_tower_base_m'],
   'selected_gallery_floor_m':params['selected_gallery_floor_m'],
   'selected_gallery_eave_m':params['selected_gallery_eave_m'],
   'selected_upper_roof_eave_m':params['selected_upper_roof_eave_m'],
   'selected_upper_roof_ridge_m':params['selected_upper_ridge_m'],
   'source_mapped_main_dimensions_m':mapped,
   'modern_two_storey_wings_distinguished_from_historic_single_storey':True,
   '1935_register_1936_completion_1937_opening_distinguished':True,
   'western_entrance_single_arch_two_octagonal_windows_five_upper_slots':True,
   'gallery_has_open_column_aisles_and_recessed_window_walls':True,
   'both_roofs_and_upper_loft_physically_closed':True,
   'rear_hall_current_fabric_date_and_details_unverified':True,
   'rear_hall_rendered_as_simplified_estimated_low_volume':True,
   'court_sources_510_1262_included':False,
   'source_wall_joints_mitered':True,'door_backstops_bound_unmodeled_interiors':True,
   'photos_embedded':False,'interiors_modeled':False,'underground_modeled':False,
   'site_slab_modeled':False,'banners_trees_lamps_exhibits_modeled':False,
   'original_geometry':True,'geometry_license':'MIT','map_reference_license':'ODbL-1.0',
   'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,
      'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated',
      'map_source_correction':'bounded runtime contract',
      'source_metadata_scope':'Main source1860 and overlapping central tower1931 only. Rear hall is a low estimated volume, not photographically verified. Court sources510/1262 and other hospital buildings remain. Assets themselves do not execute source replacement.'},
   'walk_integration':False,'complete_photo_reconstruction_accepted':False,
   'source_register':'source/precise/'+ID+'/source-register.json',
   'source_candidate_metadata':meta,'assets':assets,
   'packaging_tool':{'version_output':(tool_version.stdout+tool_version.stderr).strip(),
      'executable_sha256':hashlib.sha256(a.gltfpack.read_bytes()).hexdigest(),
      'flags':['-cc','-noq','-vnf','-km','-kn','-ke']}}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(assets,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
