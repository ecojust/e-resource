"""Dedicated Sihang package/decoder/native provenance gate; no evidence creation."""
from pathlib import Path
import json
from sihang_inputs import actual,identity,meta,read,need,IDS,GEOMETRY_SHA
def verify_model(model,values,declaration,row):
 ident=IDS[0];package=values['package'];decoded=values['actual_decoded'];native=values['native_render'];visual=values['root_native_review'];metadata=values['model_metadata']
 need(package.get('schema')=='precise-building-packaging-v1' and package.get('building_id')==ident,'Actual Sihang package schema differs')
 need(metadata.get('schema')=='sihang-warehouse-model-v12' and metadata.get('id')==ident,'Actual Sihang authored metadata required')
 need(metadata.get('height_estimate_m')==27.7 and metadata.get('ground_base_m')==0 and row['height_estimated'] is True,'Project nominal estimated height/ground differs')
 need(identity(metadata.get('raw'))==identity(package['assets']['raw']),'Author/package raw differs')
 need(decoded.get('schema')=='modern-actual-decoded-package-v11' and decoded.get('passed') is True and decoded.get('building_id')==ident and decoded.get('browser_accepted') is False and decoded.get('native_visual_accepted') is False,'Actual completed Three decoder proof required')
 need(decoded.get('package_record_sha256')==model['package']['sha256'],'Decoder/package identity differs')
 # The existing package wire format records target.source and target.sha256,
 # without bytes. Resolve and hash that one historical field explicitly;
 # every other actual descriptor retains the strict byte/SHA requirement.
 target_ref=package.get('modern_target') or {};target_path=Path(target_ref.get('source',''))
 need(target_path.is_absolute() and target_path.is_file(),'Actual package target file missing')
 target_identity=meta(target_path)
 need(0<target_identity['bytes']<100_000_000 and target_identity['sha256']==target_ref.get('sha256'),'Actual package target SHA differs')
 target=json.loads(target_path.read_bytes())
 need(target.get('id')==ident and decoded.get('target_sha256')==package['modern_target']['sha256'],'Actual decoder/target identity differs')
 actual(target['source_geometry']);actual(target['actual']['source_freeze'])
 need(decoded.get('source_geometry_sha256')==target['source_geometry']['sha256']==GEOMETRY_SHA and decoded.get('source_freeze_sha256')==target['actual']['source_freeze']['sha256'],'Actual source/author freeze differs')
 need(decoded.get('web_exact_oriented_position_material_triangle_multiset') is True and decoded.get('modern_material_properties_preserved') is True and decoded.get('lod_mode')=='authored-subtraction','Actual exact web/material/authored LOD proof required')
 for role in ('raw','web','lod'):
  need(identity(decoded['assets'][role])==identity(package['assets'][role]),'Decoded current role differs: '+role)
 actual(decoded.get('authored_lod'));actual(decoded.get('finite_probe_set'))
 need(identity(decoded['authored_lod'])==identity(target['actual']['authored_lod']) and decoded['finite_probe_set']==target['actual']['probe_set'],'Actual authored LOD or finite probe batch differs from target')
 suite=read(decoded.get('finite_actual_decoded_report'))
 need(suite.get('schema')=='modern-actual-decoded-finite-suite-v11' and suite.get('passed') is True and suite.get('building_id')==ident and suite.get('all_actual_roles_checked') is True,'Actual finite decoder suite required')
 need(suite.get('source_geometry_sha256')==GEOMETRY_SHA and suite.get('raw_sha256')==package['assets']['raw']['sha256'] and suite.get('probe_set')==decoded['finite_probe_set'],'Actual finite suite/source/probes differ')
 need(set(suite.get('roles',{}))=={'raw','web','lod','authored_lod'},'All four actual decoded roles required')
 for role,item in suite['roles'].items():
  expected=decoded['authored_lod'] if role=='authored_lod' else package['assets'][role]
  need(item.get('passed') is True and identity(item.get('current_asset'))==identity(expected),'Actual finite role identity differs: '+role)
  finite=read(item.get('finite_report'));actual(item.get('array_manifest'));actual(item.get('chunk_retention'))
  need(finite.get('schema')=='modern-actual-decoded-finite-role-v11' and finite.get('passed') is True and finite.get('building_id')==ident and finite.get('role')==role and identity(finite.get('current_asset'))==identity(expected),'Actual finite role report differs: '+role)
  need(finite.get('requests')==suite['probe_set'] and finite.get('source_geometry_sha256')==GEOMETRY_SHA and finite.get('raw_sha256')==package['assets']['raw']['sha256'],'Actual finite role source/probe batch differs: '+role)
  need(finite.get('array_manifest')==item['array_manifest'] and finite.get('source_structure_report')==suite.get('source_structure_report')==target['actual']['source_structure_report'],'Actual finite role array/structure binding differs: '+role)
 need(native.get('schema')=='sihang-warehouse-native-render-v12' and native.get('source_glb_sha256')==package['assets']['raw']['sha256'],'Actual author native render/current raw required')
 need(identity(native.get('native'))==identity(package['assets']['native']),'Native report/current .blend differs')
 need(visual.get('schema')=='sihang-root-native-visual-v12' and visual.get('passed') is True and visual.get('final') is True and visual.get('actually_viewed') is True and visual.get('reviewer')=='root' and visual.get('browser_accepted') is False,'Root actual final native visual review pending')
 need(identity(visual.get('raw'))==identity(package['assets']['raw']) and identity(visual.get('native'))==identity(package['assets']['native']),'Root review/current model bytes differ')
 need(visual.get('native_report_sha256')==model['native_render']['sha256'],'Root reviewed another native run')
 images=visual.get('actually_viewed_images',[])
 need(len(images)==3 and {i.get('role') for i in images}=={'full','detail','rear'},'Three distinct actually viewed native images required')
 recorded=native.get('images',[])
 need(isinstance(recorded,list) and {i.get('role') for i in recorded}=={'full','detail','rear'},'Native report lacks three image descriptors')
 byrole={i['role']:i for i in recorded}
 for image in images:
  need(image.get('actually_viewed') is True and isinstance(image.get('file'),str) and Path(image['file']).name==image['file'],'Unviewed or unsafe root image')
  need(identity(image)==identity(byrole[image['role']]),'Root/native rendered image differs')
  viewed_source=image.get('source') or str(Path(model['root_native_review']['source']).parent/image['file'])
  actual({'source':viewed_source,**identity(image)})
  src=byrole[image['role']].get('source') or str(Path(model['native_render']['source']).parent/byrole[image['role']]['file'])
  actual({'source':src,**identity(image)})
 need(isinstance(visual.get('limitations'),list) and visual['limitations'] and visual.get('scope'),'Root explicit uncertainty/scope required')
 need(values['prebrowser_summary'].get('browser_accepted') is False,'Prebrowser summary cannot claim browser acceptance')
