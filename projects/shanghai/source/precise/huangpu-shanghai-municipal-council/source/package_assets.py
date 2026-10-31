"""Package original Municipal Council historic-wing assets with explicit estimate metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='huangpu-shanghai-municipal-council'
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
 manifest={'id':ID,'name':'上海公共租界工部局历史街面翼楼外观候选','status':meta['status'],
  'subject':'Historic street wings of Shanghai Municipal Council building',
  'viewer_page':'municipal-council.html','authored_bounds_enu_m':bounds,
  'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],spans)),
  'current_address':meta['current_address'],'official_narrative_address':meta['official_narrative_address'],
  'address_correspondence_verified':False,'documented_existing_height_m':None,
  'model_selected_architectural_top_m':20.20,'model_above_ground_floor_layers':4,'model_below_ground_layers':0,
  'all_plan_dimensions_estimated':True,'all_floor_layer_datums_estimated':True,
  'scope_kind':meta['scope_kind'],'model_scope_zh':'历史北翼、东翼及南翼东段；三个不同凹角入口，现代西侧L形楼和两接缝未核带保留',
  'complete_listed_site_modeled':False,'modern_west_L_modeled':False,'courtyard_buildings_modeled':False,
  'modern_roof_pavilions_modeled':False,'canceled_50m_tower_modeled':False,'join_faces_author_closure':True,
  'street_elevations_photo_guided':True,'unseen_roof_is_author_closure':True,
  'commercial_signs_modeled':False,'interiors_modeled':False,'underground_modeled':False,'original_historic_state_claimed':False,
  'photos_embedded':False,'geometry_license':'MIT','original_geometry':True,'map_reference_license':'ODbL-1.0',
  'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,
    'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated',
    'map_source_correction':'bounded runtime contract',
    'source_metadata_scope':'The asset does not execute map correction. The external historical-wing contract is partial: current source intersect(y>=36 OR x>=-18), retaining the modern west/southwest L, uncertain3m join strips and all independently owned courtyard buildings. Artificial end faces are plain author closures.'},
  'walk_integration':False,'complete_photo_reconstruction_accepted':False,
  'source_register':'source/precise/huangpu-shanghai-municipal-council/source-register.json',
  'estimated':meta['scope']+' Old wall top19.25m, strong cornice14.6m, straight cap19.8m and corner cap20.20m are author estimates checked against a design illustration scale, not measured heights. No modern23.5–25m roof pavilion or canceled50m tower.',
  'source_candidate_metadata':meta,'assets':assets}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in assets.items()},ensure_ascii=False))
if __name__=='__main__':main()
