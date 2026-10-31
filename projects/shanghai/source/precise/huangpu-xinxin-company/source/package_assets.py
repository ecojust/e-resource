"""Package original Xinxin south shop-front assets with explicit estimate metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='huangpu-xinxin-company'
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
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--lod',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',required=True);a=p.parse_args()
 for path in [a.raw,a.lod]:assert document(path)['extras']['id']==ID
 a.out.mkdir(parents=True,exist_ok=True);assets={}
 for role,source,suffix in [('raw',a.raw,'-raw.glb'),('native',a.native,'.blend')]:
  dst=a.out/(ID+suffix)
  if source.resolve()!=dst.resolve():shutil.copyfile(source,dst)
  assets[role]=record(dst)
 for role,source,suffix in [('full',a.raw,'-web.glb'),('lod',a.lod,'-lod.glb')]:
  dst=a.out/(ID+suffix);subprocess.run([a.gltfpack,'-i',str(source),'-o',str(dst),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
  preserve_metadata(dst,source);assets[role]=record(dst);assert assets[role]['triangles']==record(source)['triangles']
 d=document(a.raw);meta=d['extras'];assert all(not any(k in n for k in ['matrix','translation','rotation','scale']) for n in d['nodes'])
 pp=[d['accessors'][p['attributes']['POSITION']] for m in d['meshes'] for p in m['primitives']]
 lo=[min(v['min'][i] for v in pp) for i in range(3)];hi=[max(v['max'][i] for v in pp) for i in range(3)]
 bounds={'min':[lo[0],-hi[2],lo[1]],'max':[hi[0],-lo[2],hi[1]]}
 spans=[bounds['max'][i]-bounds['min'][i] for i in range(3)]
 manifest={'id':ID,'name':'新新公司南侧商店主楼临街外观候选','status':meta['status'],
  'subject':'Southern commercial street-front portion of Xinxin Company / Shanghai First Foodhall, 720 East Nanjing Road',
  'viewer_page':'xinxin-company.html','authored_bounds_enu_m':bounds,
  'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],spans)),
  'documented_front_storeys':7,'documented_height_description':'more than thirty metres; measurement endpoint unspecified',
  'height_endpoints_verified':False,'model_selected_architectural_top_m':37.5,
  'model_main_gallery_roof_top_design_m':29.2,'all_plan_dimensions_estimated':True,
  'all_floor_layer_datums_estimated':True,'floor_layer_allocation_is_author_interpretation':True,
  'current_address':'南京东路720号','construction_year_in_source':1925,'opening_date_in_source':'1926-01-23',
  'documented_site_area_m2':4280.,'modeled_plan_area_m2_estimated':meta['model_plan_area_m2_estimated'],
  'site_area_does_not_define_this_partial_scope':True,
  'scope_kind':'southern-street-front-partial-exterior','scope_cut_y_m':meta['scope_cut_y_m'],
  'scope_cut_frame':'final model ENU centred on southern source-scope centroid',
  'author_frame_scope_cut_y_m':-8.,'scope_cut_is_surveyed_dividing_wall':False,
  'rear_cut_face_is_neutral_closure_not_real_elevation':True,
  'northern_hotel_modeled':False,'courtyard_modeled':False,'true_front_hotel_dividing_line_verified':False,
  'current_visible_tower_modeled':True,'original_1925_tower_identity_claimed':False,
  'documentary_1949_removal_vs_current_tower_unresolved':True,
  'seven_layer_assignment_resolves_documented_sixth_floor_balcony':False,
  'unseen_historic_northeast_northwest_spires_modeled':False,
  'interiors_modeled':False,'neighboring_buildings_modeled':False,
  'commercial_advertisements_and_text_modeled':False,'modern_roof_antenna_included':False,
  'photos_embedded':False,'geometry_license':'MIT','original_geometry':True,'map_reference_license':'ODbL-1.0',
  'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,
    'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated',
    'map_source_correction':'bounded runtime contract',
    'source_metadata_scope':'Asset GLB does not execute map correction. The external runtime contract replaces only this southern scope and retains northern source geometry.'},
  'walk_integration':False,'complete_photo_reconstruction_accepted':False,
  'source_register':'source/precise/huangpu-xinxin-company/source-register.json',
  'estimated':'Photo-informed southern shop facade, two short side returns, recessed upper gallery, two current corner pavilions and open two-level central tower. Dimensions, layers, north cut and hidden roof are author estimates. The 37.5m model endpoint is not a surveyed interpretation of the broad documented height. North hotel, courtyard, true commercial/hotel boundary, interiors and original 1925 tower identity remain unresolved.',
  'source_candidate_metadata':meta,'assets':assets}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in assets.items()},ensure_ascii=False))
if __name__=='__main__':main()
