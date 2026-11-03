"""Package aviation building GLBs; preserve estimate metadata without quantization."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='yangpu-china-aviation-association-building'
def document(path):
 data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0];return json.loads(data[20:20+size])
def record(path):
 data=path.read_bytes();assert 0<len(data)<100000000
 row={'file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 if path.suffix=='.glb':
  d=document(path);assert not d.get('images') and not d.get('textures');row['triangles']=sum(d['accessors'][p['indices']]['count']//3 for n in d['nodes']if 'mesh'in n for p in d['meshes'][n['mesh']]['primitives'])
 return row
def metadata(path,source):
 data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);doc['extras']=document(source)['extras'];payload=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4);tail=data[20+size:]
 path.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),0x4E4F534A)+payload+tail)
 assert document(path)['extras']==document(source)['extras']
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--lod',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);assets={}
 for role,src,suffix in [('raw',a.raw,'-raw.glb'),('native',a.native,'.blend')]:
  dst=a.out/(ID+suffix)
  if src.resolve()!=dst.resolve():shutil.copyfile(src,dst)
  assets[role]=record(dst)
 for role,src,suffix in [('full',a.raw,'-web.glb'),('lod',a.lod,'-lod.glb')]:
  dst=a.out/(ID+suffix);subprocess.run([str(a.gltfpack),'-i',str(src),'-o',str(dst),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True);metadata(dst,src);assets[role]=record(dst);assert assets[role]['triangles']==record(src)['triangles']
 d=document(a.raw);pos=[d['accessors'][p['attributes']['POSITION']]for m in d['meshes']for p in m['primitives']];lo=[min(v['min'][i]for v in pos)for i in range(3)];hi=[max(v['max'][i]for v in pos)for i in range(3)];bounds={'min':[lo[0],-hi[2],lo[1]],'max':[hi[0],-lo[2],hi[1]]};params=json.loads(Path(__file__).with_name('model-parameters.json').read_text());tool=subprocess.run([str(a.gltfpack),'-v'],capture_output=True,text=True)
 manifest={'id':ID,'model_id':ID,'name':'中国航空协会旧址（长海医院飞机楼）','status':d['extras']['status'],'viewer_page':'aviation-building.html','audit_directory':'data/audit/aviation-building-v1/','authored_bounds_enu_m':bounds,'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],[bounds['max'][i]-bounds['min'][i]for i in range(3)])),'coordinate_convention':'author ENU metres; GLB east/up/south; heading 0','anchor':params['anchor'],'tower_photo_registration':params['tower_registration_review'],'model_scope_zh':'现存修缮后独立飞机形建筑：圆角前翼三道不等高窗带、圆塔及三重开孔退台栏、圆窗小亭、双弧梯、低筒拱连体与东尾翼；东西入口依可见照片简化。未见清的连体及后翼普通侧窗间距为推定，非逐面照片验收。','all_dimensions_estimated':True,'all_elevation_datums_estimated':True,'documented_existing_height_m':None,'measured_survey':False,'documented_total_floor_area_m2':1522,'floor_area_is_not_footprint':True,'selected_roof_levels_m':{'front_wing':round(params['wing_roof_m']-params['flat_roof_surface_recess_m'],2),'outer_terrace':round(params['outer_terrace_m']-params['flat_roof_surface_recess_m'],2),'rear_wing':round(params['rear_roof_m']-params['flat_roof_surface_recess_m'],2),'connector_eave':params['connector_eave_m'],'central_pavilion_lid':16.7},'flat_roof_surface_recess_m':params['flat_roof_surface_recess_m'],'flat_roof_recess_is_estimated':True,'ordinary_side_window_positions_inferred':True,'front_wing_three_bands_not_three_equal_storeys':True,'east_and_west_portals_photographically_referenced':True,'three_terrace_rails_have_actual_openings':True,'closed_barrel_connector_roof':True,'sculptural_dragon_cloud_and_emblem_reliefs_simplified':True,'text_inscriptions_omitted':True,'1935_foundation_1936_completion_distinguished':True,'present_repaired_exterior_not_1935_reconstruction':True,'original_geometry':True,'geometry_license':'MIT','map_reference_license':'ODbL-1.0','photos_embedded':False,'interiors_modeled':False,'underground_modeled':False,'site_slab_modeled':False,'adjacent_hospital_buildings_included':False,'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated','source_metadata_scope':'Frozen OSM source w442978597@2, localId1349 only; exact removal contract validated separately. Assets do not execute map source replacement.'},'walk_integration':False,'complete_photo_reconstruction_accepted':False,'source_register':'source/precise/'+ID+'/source-register.json','source_candidate_metadata':d['extras'],'assets':assets,'packaging_tool':{'version_output':(tool.stdout+tool.stderr).strip(),'executable_sha256':hashlib.sha256(a.gltfpack.read_bytes()).hexdigest(),'flags':['-cc','-noq','-vnf','-km','-kn','-ke']}}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(assets,indent=2))
if __name__=='__main__':main()
