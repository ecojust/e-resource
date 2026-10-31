"""Package original New Wing On assets with explicit estimate metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='huangpu-new-wing-on-company'
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
 manifest={'id':ID,'name':'新永安公司／七重天大厦历史外观候选','status':meta['status'],
  'subject':'New Wing On Company / Seventh Heaven Building, 627 East Nanjing Road',
  'viewer_page':'new-wing-on-company.html','authored_bounds_enu_m':bounds,
  'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],spans)),
  'documented_front_storeys':22,'documented_rear_storeys':8,'documented_total_height_m':72.,
  'height_endpoints_verified':False,'model_selected_architectural_top_m':72.,
  'modern_tall_antenna_included':False,'all_plan_dimensions_estimated':True,
  'rear_and_roof_estimated':True,'documented_site_area_m2':1400.,
  'modeled_plan_area_m2_estimated':meta['model_plan_area_m2_estimated'],
  'documented_site_area_not_used_to_rescale_current_map':True,
  'current_address':'南京东路627号','gazetteer_address_variant':'南京东路727号',
  'indexed_year':'1933','gazetteer_year_variant':'1932','date_conflict_unresolved':True,
  'historic_exterior_scope':True,'old_wing_on_company_at_635_included':False,
  'connecting_bridges_included':False,'interiors_modeled':False,'neighboring_buildings_modeled':False,
  'commercial_advertisements_and_text_modeled':False,'thermometer_readout_and_numbers_modeled':False,
  'photos_embedded':False,'geometry_license':'MIT','original_geometry':True,
  'map_reference_license':'ODbL-1.0',
  'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,
    'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated',
    'map_source_correction':'bounded runtime contract',
    'source_metadata_scope':'The asset itself does not execute map correction; its map_replacement:false flag describes the GLB, while the linked runtime contract performs the bounded source correction.'},
  'walk_integration':False,'complete_photo_reconstruction_accepted':False,
  'source_register':'source/precise/huangpu-new-wing-on-company/source-register.json',
  'estimated':'Plan, layer datums, window counts, curves, hidden faces and roof equipment are author estimates. 72m is selected as the solid architectural endpoint, not a verified measurement. 13+7+2 is an authored allocation of the documented 22-storey front; the rear uses eight authored layers. Modern tall antenna, bridge, Old Wing On, commercial lettering and thermometer readings are omitted.',
  'source_candidate_metadata':meta,'assets':assets}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in assets.items()},ensure_ascii=False))
if __name__=='__main__':main()
