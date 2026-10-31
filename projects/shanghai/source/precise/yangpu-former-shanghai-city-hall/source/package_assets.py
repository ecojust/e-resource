"""Package original Yangpu former city-hall assets with explicit estimate metadata."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ID='yangpu-former-shanghai-city-hall'
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
 d=document(a.raw);meta=d['extras']
 assert all(not any(k in n for k in ['matrix','translation','rotation','scale']) for n in d['nodes'])
 pos=[d['accessors'][p['attributes']['POSITION']] for m in d['meshes'] for p in m['primitives']]
 lo=[min(v['min'][i] for v in pos) for i in range(3)];hi=[max(v['max'][i] for v in pos) for i in range(3)]
 bounds={'min':[lo[0],-hi[2],lo[1]],'max':[hi[0],-lo[2],hi[1]]}
 tool_version=subprocess.run([str(a.gltfpack),'-v'],capture_output=True,text=True)
 manifest={'id':ID,'name':'原上海特别市政府大楼（绿瓦大楼）外观候选','status':meta['status'],
   'viewer_page':'yangpu-city-hall.html','audit_directory':'data/audit/yangpu-city-hall-v1/',
   'authored_bounds_enu_m':bounds,
   'outer_envelope_including_projection_design_estimate_m':dict(zip(['width','depth','height'],[bounds['max'][i]-bounds['min'][i] for i in range(3)])),
   'model_scope_zh':'三段绿瓦歇山顶主楼；独立南侧仪式阶梯与真实东西向道路拱桥；侧面入口及北面保守外观估计',
   'documented_long_axis_m':93,'documented_central_depth_m':25,'documented_wing_depth_m':20,
   'documented_existing_height_m':None,'all_elevation_datums_estimated':True,
   'bridge_axis_photo_guided':True,'bridge_width_and_clearance_estimated':True,
   'bridge_deck_overhead_not_ground_collision':True,'north_entry_threshold_not_surveyed':True,
   'source_footprint_and_independent_approach_scopes_separate':True,
   'photos_embedded':False,'interiors_modeled':False,'underground_modeled':False,
   'campus_neighbors_modeled':False,'courtyard_ground_modeled':False,'road_fill_modeled':False,
   'original_geometry':True,'geometry_license':'MIT','map_reference_license':'ODbL-1.0',
   'city_integration':{'catalog':'data/candidate-city-integrations.json','id':ID,
      'view':'index.html#landmark='+ID+'&mode=overview','placement':'estimated',
      'map_source_correction':'bounded runtime contract',
      'source_metadata_scope':'Main source525 removal is independent of approach stairs and overhead road bridge. The asset does not execute map correction.'},
   'walk_integration':False,'complete_photo_reconstruction_accepted':False,
   'source_register':'source/precise/'+ID+'/source-register.json',
   'source_candidate_metadata':meta,'assets':assets,
   'packaging_tool':{'version_output':(tool_version.stdout+tool_version.stderr).strip(),
      'executable_sha256':hashlib.sha256(a.gltfpack.read_bytes()).hexdigest(),
      'flags':['-cc','-noq','-vnf','-km','-kn','-ke']}}
 (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(assets,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
