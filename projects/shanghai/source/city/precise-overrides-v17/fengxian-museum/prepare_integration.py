#!/usr/bin/env python3
"""V17 new-macro data-only preparation. Never installs MAIN or changes runtime.

The existing V17 freeze pins current V16 MAIN; owner builds one near group,
candidate stages the real reviewed model, accept binds actual browser evidence.
Every output is a new directory and every source asset is SHA-bound.
"""
import argparse, copy, gzip, hashlib, html, importlib.util, json, math, os, re, subprocess, sys
import struct
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
MAIN=Path('/workspace/shanghai_project')
V12=Path('/workspace/shanghai_expansion/building-by-building-v12')
ID='fengxian-museum';MACRO='14-13721-6710';LOCAL=143
NEAR='14-13721-6710-0_-3';KEEP=[95]
PREFIX='source/city/precise-overrides-v17/'+ID
PUBLIC='data/audit/precise-buildings-v17/'+ID
SOURCE_GEOMETRY=HERE/'freeze-v1'/ID/'geometry-input.json'
BASE_COUNTS={'navigation':33,'owners':19,'owner_macros':12,'near_chunks':17,'ordinary_records':14,'catalog_macros':11}
FINAL_COUNTS={key:value+1 for key,value in BASE_COUNTS.items()}
LIMIT=100_000_000
CHECKS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty')

def need(ok,msg):
 if not ok:raise ValueError(msg)
def read(p):
 p=Path(p);b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def encoded(d):return (json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def meta(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def desc(p):return {'source':str(Path(p).resolve()),**meta(p)}
def verified(d):
 p=Path(d['source']);need(meta(p)=={k:d[k] for k in ('bytes','sha256')},'Source bytes changed: '+str(p));return p
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(encoded(d))
def fresh(p):
 p=Path(p).resolve();need(p.is_relative_to(HERE) and p!=HERE and not p.exists(),'Use a NEW isolated integration child directory');p.mkdir(parents=True);return p
def module(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main_file(name):return {'file':name,**meta(MAIN/name)}

def validate_baseline(lock):
 need(lock['counts']==BASE_COUNTS and lock['projected_counts_if_one_complete_model_accepted']==FINAL_COUNTS,'Wrong frozen V17 count contract')
 need(lock['root_approved_published_head']=='ee7a32de12cecc667f7989af6c3d62b21c12adb4','Wrong pinned published V16 baseline')
 for key in ('source_geometry','source_identity'):
  row=lock[key];need(meta(row['path'])=={k:row[k] for k in ('bytes','sha256')},'Frozen source evidence changed: '+key)
 for row in lock['files']+lock['runtime_files']:
  need(meta(MAIN/row['file'])=={k:row[k] for k in ('bytes','sha256')},'Current MAIN beforeimage changed: '+row['file'])
 need(len(lock['runtime_files'])==len({row['file'] for row in lock['runtime_files']})==35,'Expected unchanged runtime35 baseline')
 # The repository-root README is outside MAIN and must not be silently omitted.
 need(len(lock['external_files'])==1 and lock['external_files'][0]['repository_relative_path']=='README.md','Pinned external root README is required')
 for row in lock['external_files']:
  need(meta(row['path'])=={k:row[k] for k in ('bytes','sha256')},'External published beforeimage changed: '+row['repository_relative_path'])
  remote=row['fresh_pinned_remote_copy'];need(meta(remote['path'])=={k:remote[k] for k in ('bytes','sha256')}=={k:row[k] for k in ('bytes','sha256')},'Frozen exact-commit root README copy differs')
  proof=row['remote_fetch_evidence'];need(meta(proof['path'])=={k:proof[k] for k in ('bytes','sha256')},'Frozen remote fetch evidence changed')
 nav=read(MAIN/'data/landmarks.json');reg=read(MAIN/'data/precise-buildings-v6.json');cat=read(MAIN/'data/precise-buildings/catalog.json')
 actual={'navigation':len(nav),'owners':len(reg['landmarks']),'owner_macros':len(reg['macros']),'near_chunks':sum(len(m['near']) for m in reg['macros']),'ordinary_records':cat['record_count'],'catalog_macros':len(cat['macros'])}
 need(actual==BASE_COUNTS and reg['complete'] and cat['macro_count']==actual['catalog_macros'],'Wrong actual V17 baseline counts')
 need(len({r['id'] for r in nav})==len(nav) and len({r['id'] for r in reg['landmarks']})==len(reg['landmarks']),'Duplicate previous navigation/owner IDs')
 need(len({m['id'] for m in reg['macros']})==len(reg['macros']) and len({m['id'] for m in cat['macros']})==len(cat['macros']),'Duplicate baseline macro IDs')
 need(sum(m['record_count'] for m in cat['macros'])==cat['record_count'],'Existing catalog record sum differs')
 need(ID not in {r['id'] for r in nav+reg['landmarks']} and ID not in reg['geometry_inputs'],'Target owner already registered')
 need(lock['existing_target_macro'] is None and lock['existing_target_catalog_macro'] is None and lock['existing_target_catalog_record_ids']==[],'Frozen target must be a new precise/catalog macro')
 need(MACRO not in {m['id'] for m in reg['macros']} and MACRO not in {m['id'] for m in cat['macros']},'New macro already exists')
 return nav,reg,cat

def compose_registry(base,new):
 need(len(new['macros'])==len(new['landmarks'])==1 and new['macros'][0]['id']==MACRO and new['landmarks'][0]['id']==ID,'Single new Fengxian owner required')
 added=new['macros'][0]
 need(MACRO not in {m['id'] for m in base['macros']} and ID not in {r['id'] for r in base['landmarks']} and ID not in base['geometry_inputs'],'Duplicate target macro/owner')
 need(len(added['near'])==1 and added['near'][0]['id']==NEAR,'Exactly one new near group required')
 need(set(added['near'][0]['featureLocalIds'])==set(KEEP+[LOCAL]),'New near owner/retained source IDs differ')
 need(set(new['geometry_inputs'])=={ID},'New source geometry index must contain target only')
 result=copy.deepcopy(base);result['macros'].append(copy.deepcopy(added))
 result['landmarks']+=copy.deepcopy(new['landmarks']);result['geometry_inputs'].update(copy.deepcopy(new['geometry_inputs']))
 need(len(result['landmarks'])==FINAL_COUNTS['owners'] and len(result['macros'])==len({m['id'] for m in result['macros']})==FINAL_COUNTS['owner_macros'] and sum(len(m['near']) for m in result['macros'])==FINAL_COUNTS['near_chunks'],'Wrong composed owner counts')
 need(result['landmarks'][:-1]==base['landmarks'] and result['macros'][:-1]==base['macros'],'Previous owner records or macro objects changed')
 need({k:v for k,v in result['geometry_inputs'].items() if k!=ID}==base['geometry_inputs'],'Previous frozen geometry index changed')
 return result

def owner(a):
 lock=read(a.freeze/'baseline.json');validate_baseline(lock);g=read(a.freeze/ID/'geometry-input.json')
 need(g['id']==ID and g['current_city_detail']['feature_local_id']==LOCAL and meta(a.freeze/ID/'geometry-input.json')=={k:lock['source_geometry'][k] for k in ('bytes','sha256')},'Wrong owner source or frozen geometry bytes')
 out=Path(a.output).resolve();need(out.is_relative_to(HERE) and not out.exists(),'Fresh isolated owner output required')
 tool=V12/'integration/minimal-tools-v1/owner/tools'
 subprocess.run([sys.executable,str(tool/'build_precise_overrides.py'),'--project',str(MAIN),'--output',str(out),'--geometry-input-root',str(a.freeze),'--ids',ID,'--gltfpack','/workspace/shanghai_tools/node_modules/gltfpack/cli.js','--asset-prefix','assets/city-overrides-v6/'+MACRO],check=True)
 subprocess.run(['node',str(tool/'verify_override_geometry.mjs'),str(out/'geometry-comparison-input.json')],check=True)
 reg=read(out/'precise-buildings-v6.json');report=read(out/'geometry-validation.json')
 need(reg['complete'] and report['pass'] and len(reg['macros'])==len(reg['landmarks'])==1,'Actual single owner geometry validation failed')
 validate_baseline(lock);print(json.dumps({'owner_registry':desc(out/'precise-buildings-v6.json'),'geometry_report':desc(out/'geometry-validation.json')},indent=2))

class Plan:
 def __init__(self,out):self.out=fresh(out);self.files={}
 def add(self,name,source=None,data=None):
  p=Path(name);need(not p.is_absolute() and '..' not in p.parts and p.as_posix()==name and not any(c in name for c in '\\:%?#'),'Unsafe destination')
  need(name.startswith(('data/','source/','assets/')),'Data-only preparation requires data/source/assets destination')
  if data is not None:
   source=self.out/'payload'/name;source.parent.mkdir(parents=True,exist_ok=True)
   with source.open('xb') as f:f.write(encoded(data))
  source=Path(source).resolve();d=meta(source);need(0<d['bytes']<LIMIT,'Single file must be strictly below100000000 bytes: '+name)
  before=meta(MAIN/name) if (MAIN/name).is_file() else None
  row={'file':name,'source':str(source),**d,'old_main':before}
  need(name not in self.files or self.files[name]==row,'Duplicate conflicting destination: '+name);self.files[name]=row
  return {'file':name,**d}
 def finish(self,**fields):
  for row in self.files.values():verified(row)
  result={'schema':'fengxian-v17-installation-plan','files':list(self.files.values()),'file_count':len(self.files),'main_written':False,'runtime_changed':False,**fields}
  write(self.out/'installation-plan.json',result);print(json.dumps({'plan':desc(self.out/'installation-plan.json'),'status':fields.get('status'),'file_count':len(self.files)},indent=2));return result

def check_glb(p):
 with Path(p).open('rb') as f:
  header=f.read(20);magic,version,size,n,typ=struct.unpack('<4sIIII',header);need(magic==b'glTF' and version==2 and size==Path(p).stat().st_size and typ==0x4e4f534a,'Invalid actual GLB header');doc=json.loads(f.read(n))
 need(not any('uri'in x for x in doc.get('images',[])+doc.get('buffers',[])),'External GLB dependencies are not allowed')
 return doc

def candidate(a):
 lock=read(a.freeze/'baseline.json');nav,base_reg,base_cat=validate_baseline(lock);g=read(a.freeze/ID/'geometry-input.json')
 need(meta(a.freeze/ID/'geometry-input.json')=={k:lock['source_geometry'][k] for k in ('bytes','sha256')},'Candidate geometry differs from frozen baseline')
 new=read(a.owner/'precise-buildings-v6.json');geo=read(a.owner/'geometry-validation.json')
 need(new['complete'] and geo['pass'] and len(new['macros'])==len(new['landmarks'])==1,'Actual independent owner proof required')
 need(new['macros'][0]['id']==MACRO and new['geometry_inputs'][ID]['sha256']==meta(a.freeze/ID/'geometry-input.json')['sha256'],'New owner source binding differs')
 need(new['landmarks'][0]['confirmed_boundary']==g['geometry'] and len(new['macros'][0]['near'])==1,'New exact owner boundary differs')
 near=new['macros'][0]['near'][0];need(near['id']==NEAR and set(near['featureLocalIds'])==set(KEEP+[LOCAL]) and near['groups'][0]['local_ids']==[LOCAL],'New near must replace only143 and retain source95')
 model=read(a.metadata);need(model['id']==ID and model['anchor']==g['anchor'] and model.get('ground_base_m')==0 and model.get('rotation_y',0)==0,'Model id/anchor/frame/ground differs')
 height=model['height_estimate_m'];need(type(height) in (int,float) and math.isfinite(height) and 1<height<60,'Actual finite model envelope height required');need(isinstance(model.get('height_note'),str) and model['height_note'].strip(),'Explicit height evidence/estimation note required')
 need(set(model['assets'])=={'raw','web','lod','native'},'Need four actual model roles')
 ordinary=module(V12/'integration/minimal-tools-v1/registration/ordinary_assets.py','fengxian_ordinary_contract')
 assets={};sources={};images={};image_hashes={};asset_docs={};triangles={}
 for role,item in model['assets'].items():
  name=item.get('path') or item.get('source');need(isinstance(name,str),'Actual asset path required: '+role)
  source=Path(name);source=source if source.is_absolute() else a.metadata.parent/source
  source=source.resolve();d=meta(source);need(d=={k:item[k] for k in ('bytes','sha256')},'Actual model descriptor differs: '+role)
  need(0<d['bytes']<LIMIT,'Model file size limit')
  prefix='assets/native/precise/' if role=='native' else 'assets/models/precise/'
  suffix='.blend' if role=='native' else '-'+role+'.glb';name=prefix+MACRO+'/'+ID+'/'+ID+suffix
  assets[role]={'file':name,**d};sources[role]=source
  if role!='native':
   check_glb(source);doc,embedded=ordinary.glb_images(source.read_bytes());images[role]=len(embedded);image_hashes[role]=embedded;asset_docs[role]=doc
   triangles[role]=item.get('triangles');need(type(triangles[role]) is int and triangles[role]>0,'Real expanded triangle count required: '+role)
 proposal=read(a.navigation);navigation=proposal.get('navigation',proposal)
 need(set(navigation)>={'walkStart','bearing'},'Explicit exterior walkStart/bearing required')
 need(len(navigation['walkStart'])==2 and all(math.isfinite(x) for x in navigation['walkStart']) and math.isfinite(navigation['bearing']),'Finite navigation required')
 navigation={'listed':True,'overviewZoom':18,**navigation}
 screen=proposal.get('actual_model_screen',{});need(screen.get('geometry_screen_passed') is True and screen.get('raw_asset_sha256')==assets['raw']['sha256'],'Actual frozen raw model navigation screen required')
 screen_sources={}
 for role in ('report','camera_views'):
  item=screen[role];source=Path(item['path']);need(meta(source)=={k:item[k] for k in ('bytes','sha256')},'Frozen model screen bytes changed: '+role);screen_sources[role]=source
 screen_report=read(screen_sources['report']);need(screen_report.get('geometry_screen_passed') is True and screen_report.get('building_id')==ID and screen_report['raw_asset']['sha256']==assets['raw']['sha256'] and screen_report['triangles']==triangles['raw'],'Actual model navigation report differs')
 screen_script=screen_report['screen_script'];need(meta(screen_script['path'])=={k:screen_script[k] for k in ('bytes','sha256')},'Actual model screen script changed after screen')
 screen_views=read(screen_sources['camera_views']);need(set(screen_views)=={'front','rear'},'Both actual mesh-fitted camera views required')
 need(screen_report.get('navigation')==navigation and screen_report.get('camera_requests')==screen_views,'Selected spawn/bearing/cameras must exactly match actual model screen')
 ground_descriptor=proposal['source_ground_screen'];ground_path=Path(ground_descriptor['path']);need(meta(ground_path)=={k:ground_descriptor[k] for k in ('bytes','sha256')},'Independent source/ground report changed')
 ground=read(ground_path);need(ground.get('passed_source_screen_only') is True and ground['candidate_navigation']=={k:navigation[k] for k in ('walkStart','bearing')},'Independent source/ground screen does not match selected navigation')
 need(ground['all_probe_buffers_inside_requested_bbox'] and not ground['incomplete_way_node_refs'] and not ground['invalid_way_geometries'] and not ground['water_relations_pending'],'Source/ground evidence has incomplete finite-probe context')
 for descriptor in [ground['osm_input'],ground['tool'],ground['candidate_binding'],ground['complete_water_evidence'],ground['effective_neighborhood']]+ground['runtime_source_inputs']+ground['water_source_dependencies']:
  need(meta(descriptor['path'])=={k:descriptor[k] for k in ('bytes','sha256')},'Independent source/ground evidence dependency changed')
 water_proof=read(ground['complete_water_evidence']['path'])
 need(water_proof['source_extraction_passed'] and water_proof['all_relation_way_nodes_present'],'Complete source lake reconstruction required')
 for descriptor in (water_proof['script'],water_proof['source_contract']):
  need(meta(descriptor['path'])=={k:descriptor[k] for k in ('bytes','sha256')},'Water reconstruction tool or coordinate contract changed')
 need(water_proof['source_contract']['sha256']==meta(a.freeze/ID/'geometry-input.json')['sha256'],'Water and model coordinate contract differ')
 photos=[];photo_sources={};register=read(a.photo_register)
 for photo in register['photos']:
  source=Path(photo.get('path') or photo.get('file'));source=source if source.is_absolute() else a.photo_register.parent/source
  need(meta(source)=={k:photo[k] for k in ('bytes','sha256')},'Licensed photo changed')
  need('private-reference' not in source.resolve().parts,'Private research photographs cannot be published')
  photoid=photo['id'];need(re.fullmatch(r'[a-zA-Z0-9_-]+',photoid),'Unsafe photograph ID')
  suffix=source.suffix.lower();need(suffix in ('.jpg','.jpeg','.png','.webp'),'Unsupported photo suffix')
  name='assets/references/precise/'+ID+'/'+photoid+suffix
  kind=photo.get('kind');need(kind in ('building_photograph','generic_material_scan','material_sample'),'Image kind must distinguish actual building photograph from illustrative material scan')
  embedded=photo.get('embedded_as_texture',False);need(type(embedded)is bool,'Explicit embedded image flag must be boolean')
  if kind in ('generic_material_scan','material_sample'):need(isinstance(photo.get('limitations'),str) and photo['limitations'].strip() and isinstance(photo.get('usage'),str) and photo['usage'].strip(),'Generic maps need explicit illustrative/not-measured limitation and mapping usage')
  if embedded:need(isinstance(photo.get('usage'),str) and photo['usage'].strip(),'Embedded image needs explicit mapping usage')
  row={**{k:photo[k] for k in ('id','author','license','license_url','source','date','modification')},'file':name,**meta(source),'embedded_as_texture':embedded,'kind':kind}
  if photo.get('limitations'):row['limitations']=photo['limitations']
  if photo.get('usage'):row['usage']=photo['usage']
  photos.append(row);photo_sources[name]=source
 need(photos,'At least one actual redistributable reference photo required')
 reference=photos[0];need(reference['kind']=='building_photograph','Viewer reference must be an actual licensed photograph of the museum')
 embedded_sources={p['sha256']:p for p in photos if p['embedded_as_texture']}
 need(set(embedded_sources)=={h for hashes in image_hashes.values() for h in hashes},'Embedded images must match exact published original bytes; no unused or undeclared image claim')
 for role,hashes in image_hashes.items():
  need(set(hashes)<=set(embedded_sources),'Unattributed embedded image: '+role)
  copyright=asset_docs[role].get('asset',{}).get('copyright','');token=re.sub('[^a-z0-9]','',copyright.lower())
  for h in hashes:
   p=embedded_sources[h];need(p['author'] in copyright and re.sub('[^a-z0-9]','',p['license'].lower()) in token,'Existing ordinary GLB image attribution contract failed: '+role)
 texture_contract={'mode':'embedded_licensed_images' if embedded_sources else 'none','expected_images':images,'embedded_sha256_by_role':image_hashes,'note':'Viewer reference is an actual licensed museum photograph. Generic surface maps, if embedded, are illustrative material scans and do not measure the museum surfaces. Embedded image bytes and attributions are verified against the published source register.'}
 need(isinstance(model.get('uncertainty',[]),list) and all(isinstance(x,str) and x.strip() for x in model.get('uncertainty',[])),'Uncertainty must be explicit nonempty strings in a list')
 model_asset_licenses=model.get('asset_license')
 if not isinstance(model_asset_licenses,list):
  need(model_asset_licenses is None or isinstance(model_asset_licenses,str) and 'MIT for original geometry/code' in model_asset_licenses,'Unsupported author license declaration')
  model_asset_licenses=[{'id':'MIT','url':'https://opensource.org/license/mit','attribution':'Copyright (c)2026 agent','role':'Original model geometry and authoring code; map and photographs retain separately declared licenses.'}]
 c=g['current_city_detail'];owner={'macro_id':MACRO,'feature_local_id':LOCAL,'feature_key':c['frozen_effective_feature']['key'],'near_owner_id':NEAR,'baseline_configuration_sha256':c['configuration_sha256'],'baseline_ready_sha256':c['ready_source_file']['sha256'],'baseline_feature_table_sha256':c['feature_table_source_file']['sha256'],'baseline_near_sha256':c['near_asset_sha256'],'baseline_near_feature_local_ids':c['near_feature_local_ids'],'replace_only_local_ids':[LOCAL],'preserve_neighbor_local_ids':KEEP}
 row={'id':ID,'name':g['name_zh'],'kind':'building','detail_level':'architectural','district':{'id':g['district_id'],'name':g['district_name']},'districtId':g['district_id'],'district_name':g['district_name'],'anchor':g['anchor'],'lng':g['anchor'][0],'lat':g['anchor'][1],'bbox':g['geographic_bbox'],'confirmed_boundary':g['geometry'],'geometry_input_sha256':meta(a.freeze/ID/'geometry-input.json')['sha256'],'height_m':height,'height_estimated':True,'height_note':model['height_note'],'navigation':navigation,'walkStart':navigation['walkStart'],'bearing':navigation['bearing'],'overviewZoom':navigation['overviewZoom'],'assets':assets,'owner':owner,'triangles':triangles['web'],'raw_triangles':triangles['raw'],'lod_triangles':triangles['lod'],'lod_switch_in_m':300,'lod_switch_out_m':400,'source_provider':'OpenStreetMap via Overture Maps','source_url':'https://www.openstreetmap.org/relation/20262808/history','source_license':[{'id':'ODbL-1.0','url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors; Overture Maps2026-10-21.0','role':'Existing frozen owner boundary and identity; not surveyed architectural walls.'}],'asset_license':model_asset_licenses,'source_photos':photos,'reference':{'image':reference['file'],**{k:reference[k] for k in ('author','license','license_url','source','sha256')}},'source_package':'source/precise/'+ID,'source_provenance':{'provider_records':g['source']['provider_records'],'frozen_license':['ODbL-1.0'],'frozen_attribution':g['attribution']},'architecture_style':model.get('architecture_style','当代博物馆；三体展馆、金属百叶、玻璃幕墙与上层连接。'),'detail_note':model.get('detail_note','依据公开照片、分层图纸与冻结地图身份复原奉贤博物馆新馆外观；三体地面分离、上层连廊及屋顶开放空间分别建模，非测绘复原。'),'accuracy_scope':'Photo- and plan-informed exterior reconstruction of the complete 2019 museum represented by one mapped upper-level owner; dimensions, heights and hidden details remain documented estimates.','uncertainty':model.get('uncertainty',[])+[note for note in g['limitations'] if note!='No navigation, mesh, material, compression, browser or production capacity acceptance.']+['External spawn and finite movement/camera probes are screened. Ground probes use mapped water and nearby source footprints; an elevated camera may be above water. Runtime building collision uses loaded online map polygons, not the precise mesh. Museum passages, visual stairs, platforms and roof paths do not automatically gain exact collision or ground support; interior access, stair climbing and roof walking are not accepted.'],'photo_texture':texture_contract,'accepted':False,'candidate_only':True,'browser_passed':False,'catalog_lifecycle_browser_passed':False,'pending_stages':list(CHECKS),'acceptance':{k:{'status':'pending','scope':'Awaiting actual scoped model/browser review.'} for k in CHECKS}}
 row['ground_corridor_source_verified']=False
 row['ground_corridor_scope']='Horizontal ground-floor ray samples are diagnostic only: source material does not precisely locate every column/glazing boundary. Required roof vertical probes, white platform surfaces and second-floor connectivity do not certify ground-level passage, interior access or roof walking. Actual browser navigation is limited to the reviewed external start and finite movement/camera probes.'
 for role,key in [('raw','editable_model'),('web','model'),('lod','lod_model'),('native','native_model')]:row[key]=assets[role]['file'];row[role+'_bytes']=assets[role]['bytes'];row[role+'_sha256']=assets[role]['sha256']
 out=Plan(a.output)
 for role,item in assets.items():out.add(item['file'],source=sources[role])
 for name,source in photo_sources.items():out.add(name,source=source)
 out.add('source/precise/'+ID+'/geometry-input.json',source=a.freeze/ID/'geometry-input.json')
 out.add('source/precise/'+ID+'/model-metadata.json',source=a.metadata)
 out.add('source/precise/'+ID+'/public-photo-register.json',source=a.photo_register)
 out.add(PUBLIC+'/navigation-proposal.json',source=a.navigation)
 out.add(PUBLIC+'/model-clearance.json',source=screen_sources['report'])
 out.add(PUBLIC+'/camera-views.json',source=screen_sources['camera_views'])
 out.add(PUBLIC+'/source-ground-review.json',source=ground_path)
 # Public source-only evidence contains no private plan/photo pixels. Bind the
 # full lake reconstruction instead of shipping an unexplained water pass.
 out.add(PUBLIC+'/water-source-review.json',source=Path(ground['complete_water_evidence']['path']))
 for descriptor in ground['water_source_dependencies']:
  out.add(PREFIX+'/water-source/'+Path(descriptor['path']).name,source=Path(descriptor['path']))
 out.add(PREFIX+'/water-source/build_water_context.py',source=Path(water_proof['script']['path']))
 out.add(PREFIX+'/ground-source/osm-map.json',source=Path(ground['osm_input']['path']))
 out.add(PREFIX+'/ground-source/navigation-seed.json',source=Path(ground['candidate_binding']['path']))
 out.add(PREFIX+'/ground-source/source-neighborhood.json',source=Path(ground['effective_neighborhood']['path']))
 out.add(PREFIX+'/screen_source_ground.py',source=Path(ground['tool']['path']))
 out.add(PREFIX+'/screen_frozen_model.py',source=Path(screen_report['screen_script']['path']))
 out.add(PUBLIC+'/runtime35.json',source=a.freeze/'runtime35.json')
 out.add(PUBLIC+'/runtime-collision-scope.json',source=HERE/'runtime-collision-scope-v1.json')
 out.add(PREFIX+'/geometry-validation.json',source=a.owner/'geometry-validation.json')
 out.add(PREFIX+'/owner-registry.json',source=a.owner/'precise-buildings-v6.json')
 snapshot=out.out/'prepare_integration.snapshot.py'
 with snapshot.open('xb') as f:f.write(Path(__file__).read_bytes())
 out.add(PREFIX+'/prepare_integration.py',source=snapshot)
 override_path=a.owner/Path(near['model']['file']).name;need(meta(override_path)=={'bytes':near['model']['size_bytes'],'sha256':near['model']['sha256']},'Real override asset differs')
 out.add(near['model']['file'],source=override_path)
 reg=compose_registry(base_reg,new)
 composition={'passed':True,'scope':'Data-only composition: all previous owner records, near groups, macro objects and geometry-input records remain exact. One new museum macro/near replaces source143 only and preserves source95. No model/browser acceptance.','baseline_registry':main_file('data/precise-buildings-v6.json'),'new_owner_registry':desc(a.owner/'precise-buildings-v6.json'),'new_geometry_report':desc(a.owner/'geometry-validation.json'),'old_validation':base_reg['validation'],'existing_same_macro_ids':[],'counts':{'owners':FINAL_COUNTS['owners'],'macros':FINAL_COUNTS['owner_macros'],'near':FINAL_COUNTS['near_chunks']}}
 validation=out.add(PREFIX+'/composition-proof.json',data=composition);reg['validation']={k:validation[k] for k in ('file','sha256')};reg['status']='All owner variants have actual geometry checks; candidate model/browser remain pending.';reg['integration_scope']='Candidate34: previous33 navigation records and all11 catalog macros are preserved; museum candidate remains outside the active ordinary catalog.'
 districts={str(d['id']):d['name'] for d in read(MAIN/'data/districts.json')['districts']};ordinary.record_contract(row,districts,candidate_only=True);ordinary.bind(row,reg)
 out.add('data/landmarks.json',data=nav+[row]);out.add('data/precise-buildings-v6.json',data=reg);out.add('data/precise-candidates/'+ID+'.json',data=row)
 if a.delivery:
  delivery=read(a.delivery)
  for f in delivery['files']:
   supplied=verified(f).resolve();need('private-reference' not in supplied.parts and 'private-reference' not in Path(f['file']).parts and supplied.suffix.lower() not in ('.html','.htm','.mhtml') and Path(f['file']).suffix.lower() not in ('.html','.htm','.mhtml'),'Private research and fetched HTML cannot enter public delivery')
   need(f['file'].startswith(('source/precise/'+ID+'/','assets/models/precise/'+MACRO+'/'+ID+'/','assets/native/precise/'+MACRO+'/'+ID+'/','assets/references/precise/'+ID+'/')),'Optional model delivery escapes scope')
   if f['file'] in out.files:need(out.files[f['file']]['sha256']==f['sha256'],'Conflicting optional delivery asset')
   else:out.add(f['file'],source=verified(f))
 validate_baseline(lock)
 return out.finish(status='candidate34_actual_browser_pending',baseline=desc(a.freeze/'baseline.json'),runtime_baseline=desc(a.freeze/'runtime35.json'),model_metadata=desc(a.metadata),navigation_count=FINAL_COUNTS['navigation'],owner_count=FINAL_COUNTS['owners'],owner_macro_count=FINAL_COUNTS['owner_macros'],near_count=FINAL_COUNTS['near_chunks'],catalog_unchanged=True,model_accepted=False,browser_accepted=False)

def accept(a):
 plan=read(a.candidate_plan);need(plan['status']=='candidate34_actual_browser_pending','Wrong candidate plan');lock=read(verified(plan['baseline']));validate_baseline(lock)
 rows={f['file']:f for f in plan['files']}
 for f in rows.values():verified(f)
 nav=read(verified(rows['data/landmarks.json']));reg=read(verified(rows['data/precise-buildings-v6.json']));row=copy.deepcopy(nav[-1]);need(row['id']==ID and nav[:-1]==read(MAIN/'data/landmarks.json'),'Candidate34 mismatch')
 review=read(a.model_review);need(review.get('passed') is True and review.get('reviewer')=='root' and review.get('building_id')==ID,'Actual root model review required')
 need(review.get('asset_sha256')=={k:v['sha256'] for k,v in row['assets'].items()},'Root model review must bind all four actual assets')
 scopes=review.get('scopes',{});need(set(scopes)==set(CHECKS)-{'browser_proof'} and all(isinstance(v,str) and v.strip() for v in scopes.values()),'Root review must state9actual scoped checks')
 browser=read(a.browser);visual=read(a.visual)
 need(browser.get('passed') is True and browser.get('technical_passed') is True and browser.get('finished_at') and browser.get('building_id')==ID,'Actual completed target browser report required')
 need(browser.get('web_sha256')==row['web_sha256'] and browser.get('lod_sha256')==row['lod_sha256'] and browser.get('runtime_baseline_sha256')==plan['runtime_baseline']['sha256'],'Browser must bind exact web/LOD/runtime35')
 for key,name in [('expected_landmarks','data/landmarks.json'),('expected_registry','data/precise-buildings-v6.json'),('reviewed_views',PUBLIC+'/camera-views.json')]:
  need(all(browser.get(key,{}).get(k)==rows[name][k] for k in ('bytes','sha256')),'Browser must bind exact candidate '+key)
 required={'runtime_unchanged','source_owner','full_loaded','lod_loaded','returned_full','owner_lifecycle','neighbors_preserved','keyboard_movement','post_keyup_stopped','directory_direct_link','reviewed_start_safe','web_textures_decoded','lod_textures_decoded'}
 need(all(browser.get('checks',{}).get(k) is True for k in required),'Missing actual functional browser checks')
 proof_files=[];texture_models={}
 for item in browser.get('texture_proofs',[]):
  p=Path(item['file']);need(meta(p)=={k:item[k] for k in ('bytes','sha256')},'Exact texture proof changed after browser run');proof_files.append(p)
  for proof in read(p)['models']:
   need(proof['sha256'] not in texture_models,'Duplicate exact-model texture proof');texture_models[proof['sha256']]=proof
 need(proof_files and {row['web_sha256'],row['lod_sha256']}<=set(texture_models),'Missing exact web/LOD texture proofs')
 audits=browser.get('asset_audits',[])
 need([r.get('sha256') for r in audits]==[row['web_sha256'],row['lod_sha256'],row['web_sha256']],'Browser texture audits must bind initial full, LOD and returned full in order')
 image_fields=('image_index','bytes','mime_type','sha256','decoded_dimensions')
 for audit,role in zip(audits,('web','lod','web')):
  proof=texture_models[audit['sha256']];need(proof.get('passed') is True and proof['bytes']==audit['bytes']==row[role+'_bytes'],'Actual browser/proof asset differs')
  need(audit['images']==[{k:r[k] for k in image_fields} for r in proof['images']],'Browser original image byte/decode evidence differs from exact proof')
  need(sorted(r['sha256'] for r in audit['images'])==sorted(row['photo_texture']['embedded_sha256_by_role'][role]),'Browser embedded images differ from candidate original image list')
  for img in audit['images']:need(len(img['decoded_dimensions'])==2 and all(type(v)is int and v>0 for v in img['decoded_dimensions']),'Actual browser image dimensions invalid')
  check=audit['texture_check'];need(check.get('passed') is True and check['original_image_count']==len(audit['images'])==row['photo_texture']['expected_images'][role],'Actual loaded texture check absent or counts differ')
  maps=check['actual_loaded_image_maps'];need(bool(maps)==bool(audit['images']),'Browser actual loaded maps do not match image presence')
  for mapping in maps:
   uv=mapping.get('uv');need(mapping.get('isTexture') is True and mapping.get('transform_finite') is True and uv and uv.get('finite') is True and uv['count']==mapping['position_count'] and uv['itemSize']>=2,'Actual loaded image map lacks valid matching UVs/transform')
 for item in browser.get('tools',[]):need(meta(item['file'])=={k:item[k] for k in ('bytes','sha256')},'Browser QA tool changed after actual run')
 need(visual.get('passed') is True and visual.get('reviewer')=='root' and visual.get('building_id')==ID and visual.get('browser_sha256')==meta(a.browser)['sha256'] and visual.get('scope'),'Actual root browser visual review required')
 need(isinstance(visual.get('actually_viewed'),list) and visual['actually_viewed'],'Root must list actual viewed screenshots')
 out=Plan(a.output)
 for f in rows.values():out.add(f['file'],source=verified(f))
 model_desc=out.add(PUBLIC+'/model-review.json',source=a.model_review);browser_desc=out.add(PUBLIC+'/browser.json',source=a.browser);visual_desc=out.add(PUBLIC+'/visual-review.json',source=a.visual)
 for index,p in enumerate(proof_files,1):out.add(PUBLIC+'/texture-proof-'+str(index)+'.json',source=p)
 for shot in visual['actually_viewed']:
  need(shot.get('actually_viewed') is True and Path(shot['file']).name==shot['file'],'Unviewed or unsafe screenshot');source=a.browser.parent/shot['file'];need(meta(source)=={k:shot[k] for k in ('bytes','sha256')},'Viewed screenshot changed');out.add(PUBLIC+'/'+shot['file'],source=source)
 for k in CHECKS:
  d=browser_desc if k=='browser_proof' else model_desc;row['acceptance'][k]={'status':'passed','evidence_sha256':d['sha256'],'evidence_bytes':d['bytes'],'scope':visual['scope'] if k=='browser_proof' else scopes[k]}
 row.update(accepted=True,candidate_only=False,browser_passed=True,pending_stages=[],catalog_lifecycle_browser_passed=False)
 nav[-1]=row
 def replace(name,data):
  out.files.pop(name,None);target=out.out/'payload'/name
  if target.exists():raise ValueError('Unexpected payload already written')
  return out.add(name,data=data)
 replace('data/landmarks.json',nav);replace('data/precise-candidates/'+ID+'.json',row)
 reg['status']='All20 owner variants preserve source geometry. The current museum model and actual static browser checks passed; dynamic catalog lifecycle is not claimed.'
 # This target occupies a genuinely new macro. Never replace/extend a prior macro index.
 inner=copy.deepcopy(reg);inner.pop('ordinary_catalog',None);inner.pop('integration_scope',None);inner['landmarks']=[r for r in reg['landmarks'] if r['id']==ID];inner['macros']=[m for m in reg['macros'] if m['id']==MACRO];inner['geometry_inputs']={ID:reg['geometry_inputs'][ID]}
 need(len(inner['landmarks'])==len(inner['macros'])==len(inner['macros'][0]['near'])==1,'New replacement must contain only the museum owner and near group')
 repl=out.add('data/precise-buildings/macros/'+MACRO+'/replacement.json',data=inner)
 index={'schema':'precise-building-macro-v1','url_base':'project-root','macro_id':MACRO,'record_count':1,'models':[row],'replacement_registry':repl}
 idx=out.add('data/precise-buildings/macros/'+MACRO+'/index.json',data=index)
 base_cat=read(MAIN/'data/precise-buildings/catalog.json');cat=copy.deepcopy(base_cat)
 need(MACRO not in {m['id'] for m in cat['macros']},'New catalog macro unexpectedly exists')
 cat['macros'].append({'id':MACRO,'record_count':1,'bbox':row['bbox'],**idx});cat['macro_count']=len(cat['macros']);cat['record_count']=sum(m['record_count'] for m in cat['macros'])
 cat['scope']='Fifteen individually reviewed ordinary records in twelve macros. Previous eleven macro indexes/replacements remain exact. Actual static full/LOD/return/owner/keyboard checks are recorded; dynamic catalog lifecycle remains separately scoped.'
 need(cat['macro_count']==len({m['id'] for m in cat['macros']})==FINAL_COUNTS['catalog_macros'] and cat['record_count']==FINAL_COUNTS['ordinary_records'],'Duplicate macro or wrong catalog count')
 need(cat['macros'][:-1]==base_cat['macros'],'Previous catalog macro descriptors changed')
 need(not any(name in rows for m in base_cat['macros'] for name in (m['file'],read(MAIN/m['file'])['replacement_registry']['file'])),'Candidate attempts to replace an unrelated existing catalog index/replacement')
 catdesc=out.add('data/precise-buildings/catalog.json',data=cat);reg['ordinary_catalog']=catdesc;reg['integration_scope']='Accepted34 static navigation; previous33 navigation records and all old owner/macro/near/source-input records remain exact. One new catalog macro is added. Museum dynamic catalog lifecycle is not claimed by this static proof.'
 replace('data/precise-buildings-v6.json',reg)
 out.add('data/precise-buildings/by-id/'+ID+'.json',data={'schema':'precise-building-pointer-v1','id':ID,'macro_id':MACRO,'macro_index':idx['file'],'feature_local_id':LOCAL})
 ordinary=module(V12/'integration/minimal-tools-v1/registration/ordinary_assets.py','fengxian_accept_contract');districts={str(d['id']):d['name'] for d in read(MAIN/'data/districts.json')['districts']};ordinary.record_contract(row,districts);ordinary.bind(row,reg);validate_baseline(lock)
 return out.finish(status='actual_model_and_static_browser_pass_catalog_lifecycle_unclaimed',baseline=plan['baseline'],runtime_baseline=plan['runtime_baseline'],navigation_count=FINAL_COUNTS['navigation'],owner_count=FINAL_COUNTS['owners'],owner_macro_count=FINAL_COUNTS['owner_macros'],near_count=FINAL_COUNTS['near_chunks'],catalog_macro_count=FINAL_COUNTS['catalog_macros'],ordinary_record_count=FINAL_COUNTS['ordinary_records'],browser_accepted=True,model_accepted=True,catalog_lifecycle_browser_passed=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 q=s.add_parser('owner');q.add_argument('--freeze',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q=s.add_parser('candidate')
 for key in ('freeze','owner','metadata','navigation','photo-register','output'):q.add_argument('--'+key,type=Path,required=True)
 q.add_argument('--delivery',type=Path)
 q=s.add_parser('accept')
 for key in ('candidate-plan','model-review','browser','visual','output'):q.add_argument('--'+key,type=Path,required=True)
 a=p.parse_args();globals()[a.command](a)
if __name__=='__main__':main()
