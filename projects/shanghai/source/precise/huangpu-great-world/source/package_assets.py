"""Pack Great World GLBs with lossless FLOAT32 positions and bound metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='huangpu-great-world'
def document(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];return json.loads(data[20:20+n])
def record(path):
 data=path.read_bytes();assert 0<len(data)<100_000_000
 row={'file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 if path.suffix=='.glb':
  d=document(path);assert not d.get('images') and not d.get('textures');row['triangles']=sum(d['accessors'][p['indices']]['count']//3 for n in d['nodes'] if 'mesh'in n for p in d['meshes'][n['mesh']]['primitives'])
 return row
def metadata(path,source):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);doc['extras']=document(source)['extras'];j=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);tail=data[20+n:];path.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail)
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--lod',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);assets={}
 for role,src,suffix in [('raw',a.raw,'-raw.glb'),('native',a.native,'.blend')]:
  dst=a.out/(ID+suffix)
  if src.resolve()!=dst.resolve():shutil.copyfile(src,dst)
  assets[role]=record(dst)
 for role,src,suffix in [('full',a.raw,'-web.glb'),('lod',a.lod,'-lod.glb')]:
  dst=a.out/(ID+suffix);subprocess.run([str(a.gltfpack),'-i',str(src),'-o',str(dst),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True);metadata(dst,src);assets[role]=record(dst);assert assets[role]['triangles']==record(src)['triangles']
 d=document(a.raw);pos=[d['accessors'][p['attributes']['POSITION']]for m in d['meshes']for p in m['primitives']];lo=[min(v['min'][i]for v in pos)for i in range(3)];hi=[max(v['max'][i]for v in pos)for i in range(3)];bounds={'min':[lo[0],-hi[2],lo[1]],'max':[hi[0],-lo[2],hi[1]]};params=json.loads(Path(__file__).with_name('model-parameters.json').read_text());tool=subprocess.run([str(a.gltfpack),'-v'],capture_output=True,text=True)
 manifest={'id':ID,'model_id':ID,'name':'上海大世界历史主楼与街角塔','status':'original-photo-informed-exterior','viewer_page':'great-world.html','audit_directory':'data/audit/great-world-v1/','authored_bounds_enu_m':bounds,'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],[bounds['max'][i]-bounds['min'][i]for i in range(3)])),'coordinate_convention':'author ENU metres; GLB east/up/south; heading 0','anchor':params['anchor'],'model_scope_zh':'1519沿街U形四层主体、497街角塔及照片可见两座屋顶亭；不含共舞台。2017后中庭屋盖现状未证，白钢盖不按2014旧照重建。','all_dimensions_estimated':True,'all_elevation_datums_estimated':True,'documented_existing_height_m':None,'measured_survey':False,'selected_roof_levels_m':{'main_body':20.4,'tower_tip':43.8,'tower_finial':46.4},'main_tower_arched_bays':12,'main_tower_lower_registration_source_localId':497,'map_tower_vertices_not_equal_to_column_count':True,'tower_has_inset_glazed_cores_and_open_colonnades':True,'actual_open_balusters_and_entrance_fretwork':True,'roof_surface_below_wall_cap_m':.04,'pavilion_positions_inferred':True,'ordinary_hidden_side_windows_inferred':True,'roof_inscription':'大世界 — original simplified stroke geometry; approximate size based on2024 photographs','original_geometry':True,'geometry_license':'MIT','map_reference_license':'ODbL-1.0','photos_embedded':False,'third_party_models_embedded':False,'interiors_modeled':False,'underground_modeled':False,'site_slab_modeled':False,'courtyard_roof_current_status':'unverified, excluded; historical2014 white canopy not presented as current','adjacent_gongwutai_included':False,'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated','source_metadata_scope':'source1519 + overlapped497; source2367 共舞台 explicitly preserved; map replacement separately audited'},'complete_photo_reconstruction_accepted':False,'source_register':'source/precise/'+ID+'/source-register.json','source_candidate_metadata':d['extras'],'assets':assets,'packaging_tool':{'version_output':(tool.stdout+tool.stderr).strip(),'executable_sha256':hashlib.sha256(a.gltfpack.read_bytes()).hexdigest(),'flags':['-cc','-noq','-vnf','-km','-kn','-ke']}}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(assets,indent=2))
if __name__=='__main__':main()
