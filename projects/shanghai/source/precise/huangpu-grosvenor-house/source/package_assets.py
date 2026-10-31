"""Package original Grosvenor House main-block assets with explicit estimate metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='huangpu-grosvenor-house'
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
 manifest={'id':ID,'name':'峻岭公寓高层主体外观候选','status':meta['status'],
  'subject':'Grosvenor House historic high-rise / middle building of Jinjiang Hotel, Shanghai',
  'viewer_page':'grosvenor-house.html','authored_bounds_enu_m':bounds,
  'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],spans)),
  'current_address':meta['current_address'],'official_narrative_address':meta['official_narrative_address'],
  'address_correspondence_verified':False,'documented_storeys_including_basement':18,'documented_basements':1,
  'secondary_storey_account':meta['secondary_storey_account'],'documented_height_m':78.0,
  'height_endpoints_verified':False,'model_selected_architectural_top_m':78.0,
  'model_above_ground_floor_layers':17,'model_below_ground_layers':0,
  'all_plan_dimensions_estimated':True,'all_floor_layer_datums_estimated':True,
  'scope_kind':meta['scope_kind'],'model_scope_zh':'高层主体与有限入口雨棚；前庭左右未核源余块保留','unresolved_southern_source_residuals_retained':True,'garden_elevation_photo_guided':True,'rear_elevation_photo_verified':False,
  'unseen_roof_is_author_closure':True,'source_south_step_height_attribution_verified':False,
  'shelter_equals_specific_map_step_claimed':False,'shelter_depth_constrained_to_preserve_adjacent_source':True,
  'western_low_apartments_modeled':False,'neighboring_new_jinjiang_tower_modeled':False,
  'commercial_signs_modeled':False,'interiors_modeled':False,'underground_modeled':False,'original_1934_state_claimed':False,
  'photos_embedded':False,'geometry_license':'MIT','original_geometry':True,'map_reference_license':'ODbL-1.0',
  'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,
    'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated',
    'map_source_correction':'bounded runtime contract',
    'source_metadata_scope':'The asset does not execute map correction. Its external bounded contract addresses only the identified high-rise source, preserving separately owned western low apartments and the foreground independent source. The coarse southern source steps have no verified tall-wall-versus-canopy attribution; their residual areas are not assumed empty.'},
  'walk_integration':False,'complete_photo_reconstruction_accepted':False,
  'source_register':'source/precise/huangpu-grosvenor-house/source-register.json',
  'estimated':'Current photo-informed historic high-rise with an estimated five-fold concave garden facade, five real stepped terrace levels, continuous narrow pale central/end strips, horizontally grouped recessed windows, eight deep crown grooves backed by brick, and a low entrance shelter with eighteen actual glass-panel holes in its metal roof frame. Every dimension, floor datum, rear/roof detail and main-versus-low-shelter division of coarse map steps is estimated. Shelter depth4.6m is constrained to leave a separately owned foreground source clear, not measured. Official18 includes1 basement; the model interprets17 above-ground layers and a78m architectural maximum; height endpoints and the contradictory secondary18-above/3-below account remain unresolved. Underground construction, western lower apartments, New Jinjiang tower, gardens, signs and interiors excluded.',
  'source_candidate_metadata':meta,'assets':assets}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in assets.items()},ensure_ascii=False))
if __name__=='__main__':main()
