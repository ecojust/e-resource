"""Package original Daxin main-block assets with explicit estimate metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='huangpu-daxin-company'
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
 manifest={'id':ID,'name':'大新公司历史主楼外观候选','status':meta['status'],
  'subject':'Historic main building of Daxin / The Sun Company, Shanghai First Department Store, 830 East Nanjing Road',
  'viewer_page':'daxin-company.html','authored_bounds_enu_m':bounds,
  'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],spans)),
  'documented_storeys':10,'documented_height_m':42.3,'height_endpoints_verified':False,
  'model_selected_architectural_top_m':42.3,'all_plan_dimensions_estimated':True,'all_floor_layer_datums_estimated':True,
  'current_address':'南京东路830号','opening_date_in_source':'1936-01-10',
  'scope_kind':meta['scope_kind'],'north_and_east_elevations_photo_verified':False,
  'unseen_roof_is_author_closure':True,'courtyard_configuration_verified':False,
  'modern_north_B_building_modeled':False,'modern_east_C_building_modeled':False,
  'excluded_adjoining_block_construction_dates_verified':False,
  'adjoining_block_naming_note':'The legacy modern_* exclusion field names identify the present adjoining B/C map objects only; their construction dates and the historical extent of the 1988 enlargement have not been established. They do not assert that those blocks were built in a verified modern period.',
  'commercial_signs_modeled':False,'interiors_modeled':False,'original_1936_state_claimed':False,
  'photos_embedded':False,'geometry_license':'MIT','original_geometry':True,'map_reference_license':'ODbL-1.0',
  'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,
    'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated',
    'map_source_correction':'bounded runtime contract',
    'source_metadata_scope':'The asset does not execute map correction; the external runtime contract replaces only the independently identified historic main-block source. The separately identified adjoining north B and east C buildings remain separate; their construction dates have not been established.'},
  'walk_integration':False,'complete_photo_reconstruction_accepted':False,
  'source_register':'source/precise/huangpu-daxin-company/source-register.json',
  'estimated':'Current photo-informed south/west exterior of the historic main building, rounded high southwest corner, narrow windows and vertical ribs, actual upper gallery recesses, pierced friezes/crown and circular ornament stack. All dimensions, floor allocation and hidden north/east/roof construction are author estimates. Documented 42.3m lacks a defined height endpoint; its use as model maximum is not a survey. Adjoining B/C blocks, signs and interiors excluded; adjoining construction dates remain unverified.',
  'source_candidate_metadata':meta,'assets':assets}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in assets.items()},ensure_ascii=False))
if __name__=='__main__':main()
