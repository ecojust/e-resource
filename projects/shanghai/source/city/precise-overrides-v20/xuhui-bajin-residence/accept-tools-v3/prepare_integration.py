#!/usr/bin/env python3
"""V20 existing-macro data-only preparation. Never installs MAIN or changes runtime.

The existing V20 source-context freeze pins current V19 MAIN; owner builds one near group,
candidate stages the real reviewed model, accept binds actual browser evidence.
Every output is a new directory and every source asset is SHA-bound.
"""
import argparse, copy, gzip, hashlib, html, importlib.util, json, math, os, re, shutil, subprocess, sys
import struct
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(HERE))
MAIN=Path('/workspace/shanghai_project')
V12=Path('/workspace/shanghai_expansion/building-by-building-v12')
ID='xuhui-bajin-residence';MACRO='14-13718-6695';LOCAL=1950
NEAR='14-13718-6695-1_1-s0-s1';KEEP=[234,276,388,575,938,1040,1327,1448,1689,1828,2602,2974,3558,3671,3828,3991,4118]
VIEW_NAMES={'garden-front','north-entry','north-oblique'}
PRIOR_IDS=['xuhui-wukang-129','xuhui-wukang-210','columbia-country-club','xuhui-wukang-mansion','changning-hudec-residence']
PREFIX='source/city/precise-overrides-v20/'+ID
PUBLIC='data/audit/precise-buildings-v20/'+ID
import integration_contract as contract
SOURCE_GEOMETRY=Path(contract.GEOMETRY['path'])
BASE_COUNTS=contract.BASE_COUNTS
FINAL_COUNTS=contract.FINAL_COUNTS
LIMIT=100_000_000
CHECKS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty')

def need(ok,msg):
 if not ok:raise ValueError(msg)
def read(p):
 p=Path(p);b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b,object_pairs_hook=contract.unique_object,parse_constant=contract.reject_constant)
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
 content=encoded(d);need(0<len(content)<LIMIT,'Generated JSON exceeds file-size limit')
 need(shutil.disk_usage(HERE).free>=contract.RESERVE_BYTES+len(content),'JSON output would cross the 300MB reserve')
 with p.open('xb') as f:f.write(content)
def fresh(p):
 return contract.fresh_output(p,create=True,budget_bytes=40_000_000)
def module(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main_file(name):return {'file':name,**meta(MAIN/name)}

def validate_baseline(lock):
 need(lock==contract.check_baseline(),'Must use the exact frozen V20 preparation baseline')
 need(lock['counts']==BASE_COUNTS and lock['projected_counts_if_one_complete_model_accepted']==FINAL_COUNTS,'Wrong V20 count contract')
 need(lock['root_approved_published_head']=='3048f6f8a16c1cbd35b7d74c3f0483bcf8e059cc','Wrong published V19 baseline')
 for key in ('source_context','source_identity'):
  row=lock[key];need(meta(row['path'])=={k:row[k] for k in ('bytes','sha256')},'Frozen source context changed: '+key)
 for row in lock['files']+lock['runtime_files']:
  need(meta(MAIN/row['file'])=={k:row[k] for k in ('bytes','sha256')},'MAIN beforeimage changed: '+row['file'])
 need(len(lock['runtime_files'])==len({r['file'] for r in lock['runtime_files']})==35,'Expected unchanged runtime35')
 need(len(lock['external_files'])==1 and lock['external_files'][0]['repository_relative_path']=='README.md','Pinned root README required')
 for row in lock['external_files']:
  need(meta(row['source'])=={k:row[k] for k in ('bytes','sha256')},'Root README baseline changed')
  for key in ('fresh_pinned_remote_copy','published_fetch_evidence'):
   d=row[key];need(meta(d['path'])=={k:d[k] for k in ('bytes','sha256')},'Pinned publication evidence changed')
 nav=read(MAIN/'data/landmarks.json');reg=read(MAIN/'data/precise-buildings-v6.json');cat=read(MAIN/'data/precise-buildings/catalog.json')
 actual={'navigation':len(nav),'owners':len(reg['landmarks']),'owner_macros':len(reg['macros']),'near_chunks':sum(len(m['near']) for m in reg['macros']),'ordinary_records':cat['record_count'],'catalog_macros':len(cat['macros'])}
 need(actual==BASE_COUNTS and reg['complete'] and cat['macro_count']==actual['catalog_macros'],'Wrong actual V19 baseline counts')
 need(len({r['id'] for r in nav})==len(nav) and len({r['id'] for r in reg['landmarks']})==len(reg['landmarks']),'Duplicate previous navigation/owner IDs')
 need(len({m['id'] for m in reg['macros']})==len(reg['macros']) and len({m['id'] for m in cat['macros']})==len(cat['macros']),'Duplicate baseline macro IDs')
 need(sum(m['record_count'] for m in cat['macros'])==cat['record_count'],'Existing catalog record sum differs')
 need(ID not in {r['id'] for r in nav+reg['landmarks']} and ID not in reg['geometry_inputs'],'Target owner already registered')
 existing=next(m for m in reg['macros'] if m['id']==MACRO);catalog_macro=next(m for m in cat['macros'] if m['id']==MACRO)
 need(existing==lock['existing_target_macro'] and catalog_macro==lock['existing_target_catalog_macro'],'Existing shared-macro baseline changed')
 index=read(MAIN/catalog_macro['file']);need([r['id'] for r in index['models']]==PRIOR_IDS and index['record_count']==5 and lock['existing_target_catalog_record_ids']==PRIOR_IDS,'All five prior shared-macro records required')
 need(len(existing['near'])==5 and NEAR not in {n['id'] for n in existing['near']} and all(LOCAL not in n['featureLocalIds'] for n in existing['near']),'Ba Jin source owner already registered or near overlaps')
 return nav,reg,cat


def compose_registry(base,new):
 need(len(new['macros'])==len(new['landmarks'])==1 and new['macros'][0]['id']==MACRO and new['landmarks'][0]['id']==ID,'Exactly one new Ba Jin residence owner required')
 old=next(m for m in base['macros'] if m['id']==MACRO);added=new['macros'][0]
 need({k:v for k,v in old.items() if k!='near'}=={k:v for k,v in added.items() if k!='near'},'Existing and new macro source/far configuration differs')
 need(len(added['near'])==1 and added['near'][0]['id']==NEAR,'Exactly one new near group required')
 need(set(added['near'][0]['featureLocalIds'])==set(KEEP+[LOCAL]),'New near target and all seventeen retained IDs differ')
 need(NEAR not in {n['id'] for n in old['near']} and all(not(set(n['featureLocalIds'])&set(added['near'][0]['featureLocalIds'])) for n in old['near']),'New near duplicates or overlaps an existing precise near')
 need(ID not in {r['id'] for r in base['landmarks']} and ID not in base['geometry_inputs'] and set(new['geometry_inputs'])=={ID},'Duplicate or unexpected source owner')
 result=copy.deepcopy(base);target=next(m for m in result['macros'] if m['id']==MACRO)
 target['near']+=copy.deepcopy(added['near']);landmark=copy.deepcopy(new['landmarks'][0]);landmark.update(boundary_role='frozen_source_owner_context_not_architectural_wall',architectural_wall_boundary_surveyed=False,source_owner_boundary_is_model_wall=False);result['landmarks'].append(landmark);result['geometry_inputs'].update(copy.deepcopy(new['geometry_inputs']))
 need(len(result['landmarks'])==FINAL_COUNTS['owners'] and len(result['macros'])==len({m['id'] for m in result['macros']})==FINAL_COUNTS['owner_macros'] and sum(len(m['near']) for m in result['macros'])==FINAL_COUNTS['near_chunks'],'Composed owner counts differ')
 need(result['landmarks'][:-1]==base['landmarks'] and target['near'][:-1]==old['near'],'Previous owners or shared-macro near groups changed')
 need([m for m in result['macros'] if m['id']!=MACRO]==[m for m in base['macros'] if m['id']!=MACRO],'Other twelve owner macros changed')
 need({k:v for k,v in result['geometry_inputs'].items() if k!=ID}==base['geometry_inputs'],'Previous geometry input records changed')
 return result


class Plan:
 def __init__(self,out,execute=False):
  self.out=contract.fresh_output(out,budget_bytes=40_000_000);self.files={};self.pending={};self.execute=execute
 def add(self,name,source=None,data=None):
  p=Path(name);need(not p.is_absolute() and '..' not in p.parts and p.as_posix()==name and not any(c in name for c in '\\:%?#'),'Unsafe destination')
  need(name.startswith(('data/','source/','assets/')),'Data-only preparation requires data/source/assets destination')
  if data is not None:
   content=encoded(data);source=self.out/'payload'/name;d={'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
  else:
   source=Path(source).resolve();d=meta(source);content=None
  need(0<d['bytes']<LIMIT,'Single file must be strictly below100000000 bytes: '+name)
  before=meta(MAIN/name) if (MAIN/name).is_file() else None
  row={'file':name,'source':str(source),**d,'old_main':before}
  need(name not in self.files or self.files[name]==row,'Duplicate conflicting destination: '+name)
  self.files[name]=row
  if content is not None:self.pending[name]=content
  return {'file':name,**d}
 def finish(self,**fields):
  for name,row in self.files.items():
   if name in self.pending:
    content=self.pending[name];need({'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}=={k:row[k] for k in ('bytes','sha256')},'Pending payload differs')
   else:verified(row)
  result={'schema':'bajin-residence-v20-installation-plan','files':list(self.files.values()),'file_count':len(self.files),'main_written':False,'runtime_changed':False,**fields}
  total=sum(len(value) for value in self.pending.values())+len(encoded(result));need(total<40_000_000,'Actual isolated candidate workset exceeds 40MB')
  if not self.execute:
   print(json.dumps({'status':'ACTUAL_INPUTS_VALIDATED_NO_OUTPUT','intended_stage':fields.get('status'),'file_count':len(self.files),'output_created':False,'main_written':False},indent=2));return result
  contract.fresh_output(self.out,create=True,budget_bytes=40_000_000)
  for name,content in self.pending.items():
   destination=Path(self.files[name]['source']);destination.parent.mkdir(parents=True,exist_ok=True)
   with destination.open('xb') as handle:handle.write(content)
  write(self.out/'installation-plan.json',result);need(shutil.disk_usage(HERE).free>=contract.RESERVE_BYTES,'Final output crossed the 300MB reserve')
  print(json.dumps({'plan':desc(self.out/'installation-plan.json'),'status':fields.get('status'),'file_count':len(self.files)},indent=2));return result

def check_glb(p):
 with Path(p).open('rb') as f:
  header=f.read(20);magic,version,size,n,typ=struct.unpack('<4sIIII',header);need(magic==b'glTF' and version==2 and size==Path(p).stat().st_size and typ==0x4e4f534a,'Invalid actual GLB header');doc=json.loads(f.read(n))
 need(not any('uri'in x for x in doc.get('images',[])+doc.get('buffers',[])),'External GLB dependencies are not allowed')
 return doc

def candidate(a):
 binding=contract.validate_root_review(a.root_model_review,a.root_model_review_sha256)
 contract.check_frozen_inputs()
 need(a.freeze.resolve()==contract.PREPARATION/'freeze-v1' and a.owner_input_root.resolve()==contract.PREPARATION/'source-owner-input-v1','Use the fixed V20 frozen inputs')
 contract.fresh_output(a.output,budget_bytes=40_000_000)
 owner_proof=contract.check_owner_binding(a.owner,binding)
 lock=read(a.freeze/'baseline.json');nav,base_reg,base_cat=validate_baseline(lock);g=read(a.owner_input_root/ID/'geometry-input.json')
 need(meta(a.owner_input_root/ID/'geometry-input.json')==meta(SOURCE_GEOMETRY),'Candidate source owner input differs')
 need(g['context_freeze']==lock['source_context'] and g['boundary_role']=='frozen_source_owner_context_not_architectural_wall' and g['source_owner_boundary_is_model_wall'] is False,'Source context is not architectural wall geometry')
 need(g['geometry']==read(lock['source_context']['path'])['frozen_background_geometry'],'Source-owner polygon shifted')
 new=read(a.owner/'precise-buildings-v6.json');geo=read(a.owner/'geometry-validation.json')
 need(new['complete'] and geo['pass'] and len(new['macros'])==len(new['landmarks'])==1,'Actual independent owner proof required')
 need(new['macros'][0]['id']==MACRO and new['geometry_inputs'][ID]['sha256']==meta(a.owner_input_root/ID/'geometry-input.json')['sha256'],'New owner source binding differs')
 need(new['landmarks'][0]['confirmed_boundary']==g['geometry'] and len(new['macros'][0]['near'])==1,'New exact owner boundary differs')
 near=new['macros'][0]['near'][0];need(near['id']==NEAR and set(near['featureLocalIds'])==set(KEEP+[LOCAL]) and near['groups'][0]['local_ids']==[LOCAL],'New near must replace only1950 and retain all seventeen other source owners')
 model=read(a.metadata);need(model['id']==ID and model['anchor']==g['anchor'] and model.get('ground_base_m')==0 and model.get('rotation_y')==0,'Model id/anchor/frame/ground differs; baked ENU requires explicit heading zero')
 height=model['height_estimate_m'];need(type(height) in (int,float) and math.isfinite(height) and 1<height<60,'Actual finite model envelope height required');need(isinstance(model.get('height_note'),str) and model['height_note'].strip(),'Explicit height evidence/estimation note required')
 need(set(model['assets'])=={'raw','web','lod','native'},'Need four actual model roles')
 ordinary=module(V12/'integration/minimal-tools-v1/registration/ordinary_assets.py','bajin_residence_ordinary_contract')
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
 for role in ('raw','native'):
  need(contract.descriptor(sources[role])==binding['assets'][role],'Candidate asset differs from root-reviewed actual '+role)
 need(isinstance(model.get('lod_raw'),dict),'Metadata must bind the root-reviewed LOD raw source')
 for label in ('lod_raw','lod_source'):
  if label in model:
   lod_source={k:model[label][k] for k in ('path','bytes','sha256')}
   need(lod_source==binding['assets']['lod_raw'],'Metadata '+label+' differs from the root-reviewed LOD raw source');contract.verify_descriptor(lod_source)
 codec=read(a.codec_qa);codec_desc=contract.descriptor(a.codec_qa)
 if a.codec_qa_sha256:need(codec_desc['sha256']==a.codec_qa_sha256,'Codec QA changed')
 need(codec.get('passed') is True and codec.get('input_raw_sha256')==assets['raw']['sha256'] and codec.get('input_lod_raw_sha256')==binding['assets']['lod_raw']['sha256'] and codec.get('web_sha256')==assets['web']['sha256'] and codec.get('lod_sha256')==assets['lod']['sha256'],'Actual independent codec QA must bind raw, LOD raw, web and LOD web')
 for role,doc in asset_docs.items():
  for texture in doc.get('textures',[]):
   sampler=doc.get('samplers',[])[texture['sampler']] if 'sampler' in texture else {}
   need(sampler.get('wrapS',10497)==10497 and sampler.get('wrapT',10497)==10497,'Textured original pebbledash requires REPEAT sampling; uniform materials need no texture')
 proposal=read(a.navigation);navigation=proposal.get('navigation',proposal)
 need(set(navigation)>={'walkStart','bearing'},'Explicit exterior walkStart/bearing required')
 need(len(navigation['walkStart'])==2 and all(math.isfinite(x) for x in navigation['walkStart']) and math.isfinite(navigation['bearing']),'Finite navigation required')
 navigation={'listed':True,'overviewZoom':18,**navigation}
 screen=proposal.get('actual_model_screen',{});need(screen.get('geometry_screen_passed') is True and screen.get('raw_asset_sha256')==assets['raw']['sha256'],'Actual frozen raw model navigation screen required')
 screen_sources={}
 for role in ('report','camera_views'):
  item=screen[role];source=Path(item['path']);need(meta(source)=={k:item[k] for k in ('bytes','sha256')},'Frozen model screen bytes changed: '+role);screen_sources[role]=source
 screen_report=read(screen_sources['report']);need(screen_report.get('root_source_owner_authorization')==binding,'Navigation mesh screen must bind the same actual root review');need(screen_report.get('geometry_screen_passed') is True and screen_report.get('building_id')==ID and screen_report['raw_asset']['sha256']==assets['raw']['sha256'] and screen_report['triangles']==triangles['raw'],'Actual model navigation report differs')
 screen_script=screen_report['screen_script'];need(meta(screen_script['path'])=={k:screen_script[k] for k in ('bytes','sha256')},'Actual model screen script changed after screen')
 neighbor_desc=screen_report['independent_neighbor_report'];neighbor_path=Path(neighbor_desc['path']);need(meta(neighbor_path)=={k:neighbor_desc[k] for k in ('bytes','sha256')},'Independent neighbor screen changed')
 neighbor=read(neighbor_path);need(neighbor.get('root_source_owner_authorization')==binding,'Neighbor screen must bind the same actual root review');need(neighbor.get('passed_source_estimated_height_prism_screen') is True and neighbor['raw_asset']['sha256']==assets['raw']['sha256'] and neighbor['actual_triangle_count']==triangles['raw'],'Actual height-aware neighbor screen must pass for these raw bytes')
 neighborhood_desc=neighbor['source_neighborhood'];need({k:neighborhood_desc[k] for k in ('path','bytes','sha256')}==contract.NEIGHBORHOOD,'Neighbor report must bind the complete frozen80 neighborhood');neighborhood_path=Path(neighborhood_desc['path']);need(meta(neighborhood_path)=={k:neighborhood_desc[k] for k in ('bytes','sha256')},'Actual screened neighborhood changed')
 neighborhood=read(neighborhood_path);source_context=read(lock['source_context']['path'])
 identity=lambda r:(r['macro'],r['key'],r['local_id'])
 expected_neighbors={identity(r) for r in neighborhood['features']};screened_neighbors={identity(r) for r in neighbor['neighbor_checks']}
 required_neighbors={(r['macro'],r['key'],r['localId']) for r in source_context['nearby_context_features']}|{(MACRO,r['key'],r['localId']) for r in source_context['same_near_neighbors']}
 need(expected_neighbors==screened_neighbors and required_neighbors<=expected_neighbors and len(expected_neighbors)==len(neighborhood['features'])==len(neighbor['neighbor_checks'])==neighbor['source_neighbor_count'],'Actual mesh screen must cover the complete bound neighborhood, including all frozen nearby and same-near sources')
 need(neighborhood['anchor']==g['anchor'] and neighborhood['target_key']==g['source']['key'],'Mesh-neighborhood coordinate/identity contract differs')
 need(neighbor['same_near_neighbors_preserved_count']==17 and {r['local_id'] for r in neighbor['neighbor_checks'] if r['same_near_neighbor']}==set(KEEP) and neighbor['all_same_near_actual_projection_clear'] is True and neighbor['input_and_main_preservation']['all_exact'] is True,'KEEP17 or original source preservation differs')
 neighbor_dependencies=neighbor['tools']+[neighbor['input_and_main_preservation']['input_preimages'],neighborhood_desc,neighbor['model_handoff']]
 for descriptor in neighbor_dependencies+neighborhood['source_files']:need(meta(descriptor['path'])=={k:descriptor[k] for k in ('bytes','sha256')},'Neighbor-screen dependency changed')
 screen_views=read(screen_sources['camera_views']);need(set(screen_views)==VIEW_NAMES,'All three actual mesh-screened Ba Jin camera views required')
 need(screen_report.get('navigation')==navigation and screen_report.get('camera_requests')==screen_views,'Selected spawn/bearing/cameras must exactly match actual model screen')
 ground_descriptor=proposal['source_ground_screen'];ground_path=Path(ground_descriptor['path']);need(meta(ground_path)=={k:ground_descriptor[k] for k in ('bytes','sha256')},'Independent source/ground report changed')
 ground=read(ground_path);need(ground.get('root_source_owner_authorization')==binding,'Ground screen must bind the same actual root review');need(ground.get('passed_source_screen_only') is True and ground['candidate_navigation']=={k:navigation[k] for k in ('walkStart','bearing')},'Independent source/ground screen does not match selected navigation')
 need(ground['all_probe_buffers_inside_requested_bbox'] and not ground['incomplete_way_node_refs'] and not ground['invalid_way_geometries'] and not ground['water_relations_pending'],'Source/ground evidence has incomplete finite-probe context')
 for descriptor in [ground['osm_input'],ground['tool'],ground['candidate_binding'],ground['coordinate_contract'],ground['effective_neighborhood'],ground['visual_ground_review'],ground['runtime_scope_review']]+ground['runtime_source_inputs']:
  need(meta(descriptor['path'])=={k:descriptor[k] for k in ('bytes','sha256')},'Independent source/ground evidence dependency changed')
 need(ground['coordinate_contract']['sha256']==meta(a.owner_input_root/ID/'geometry-input.json')['sha256'],'Ground and model coordinate contracts differ')

 photos=[];photo_sources={};procedural_sources={};register=read(a.photo_register)
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
  if kind=='material_sample' and embedded:
   generator=contract.V20/'model/bajin-detailed-v2/source/generate_material.py';generator_name='source/precise/'+ID+'/source/generate_material.py'
   need(photo.get('generator_sha256')==meta(generator)['sha256'],'Original material must bind its actual frozen generator')
   need(photo['source']=='https://github.com/ecojust/e-resource/blob/master/projects/shanghai/'+generator_name,'Original material source must identify the actual planned public generator path')
   need(photo.get('repeat_metres')==[.4,.4] and photo.get('sampler_wrap')=='REPEAT','Original pebbledash physical-scale declaration differs')
   row.update(generator_sha256=photo['generator_sha256'],generator_source={'file':generator_name,**meta(generator)},repeat_metres=photo['repeat_metres'],sampler_wrap='REPEAT')
   procedural_sources[generator_name]=generator
  if photo.get('limitations'):row['limitations']=photo['limitations']
  if photo.get('usage'):row['usage']=photo['usage']
  photos.append(row);photo_sources[name]=source
 need(photos,'At least one actual redistributable reference photo required')
 reference=photos[0];need(reference['kind']=='building_photograph','Viewer reference must be an actual licensed photograph of the building')
 embedded_sources={p['sha256']:p for p in photos if p['embedded_as_texture']}
 need(set(embedded_sources)=={h for hashes in image_hashes.values() for h in hashes},'Embedded images must match exact published original bytes; no unused or undeclared image claim')
 for role,hashes in image_hashes.items():
  need(set(hashes)<=set(embedded_sources),'Unattributed embedded image: '+role)
  copyright=asset_docs[role].get('asset',{}).get('copyright','');token=re.sub('[^a-z0-9]','',copyright.lower())
  for h in hashes:
   p=embedded_sources[h];need(p['author'] in copyright and re.sub('[^a-z0-9]','',p['license'].lower()) in token,'Existing ordinary GLB image attribution contract failed: '+role)
 texture_contract={'mode':'embedded_licensed_images' if embedded_sources else 'none','expected_images':images,'embedded_sha256_by_role':image_hashes,'note':'Viewer reference is an actual licensed building photograph. Generic surface maps, if embedded, are illustrative material samples, including original procedural materials where declared, and do not measure the building surfaces. Embedded image bytes and attributions are verified against the published source register.'}
 need(isinstance(model.get('uncertainty',[]),list) and all(isinstance(x,str) and x.strip() for x in model.get('uncertainty',[])),'Uncertainty must be explicit nonempty strings in a list')
 model_asset_licenses=model.get('asset_license')
 if not isinstance(model_asset_licenses,list):
  need(model_asset_licenses is None or isinstance(model_asset_licenses,str) and 'MIT for original geometry/code' in model_asset_licenses,'Unsupported author license declaration')
  model_asset_licenses=[{'id':'MIT','url':'https://opensource.org/license/mit','attribution':'Copyright (c)2026 agent','role':'Original model geometry and authoring code; map and photographs retain separately declared licenses.'}]
 c=g['current_city_detail'];owner={'macro_id':MACRO,'feature_local_id':LOCAL,'feature_key':c['frozen_effective_feature']['key'],'near_owner_id':NEAR,'baseline_configuration_sha256':c['configuration_sha256'],'baseline_ready_sha256':c['ready_source_file']['sha256'],'baseline_feature_table_sha256':c['feature_table_source_file']['sha256'],'baseline_near_sha256':c['near_asset_sha256'],'baseline_near_feature_local_ids':c['near_feature_local_ids'],'replace_only_local_ids':[LOCAL],'preserve_neighbor_local_ids':KEEP}
 row={'id':ID,'name':'巴金旧居主楼','kind':'building','detail_level':'architectural','district':{'id':g['district_id'],'name':g['district_name']},'districtId':g['district_id'],'district_name':g['district_name'],'anchor':g['anchor'],'lng':g['anchor'][0],'lat':g['anchor'][1],'bbox':g['geographic_bbox'],'confirmed_boundary':g['geometry'],'boundary_role':'frozen_source_owner_context_not_architectural_wall','source_owner_boundary_is_model_wall':False,'architectural_wall_boundary_surveyed':False,'geometry_input_sha256':meta(a.owner_input_root/ID/'geometry-input.json')['sha256'],'height_m':height,'height_estimated':True,'height_note':model['height_note'],'navigation':navigation,'walkStart':navigation['walkStart'],'bearing':navigation['bearing'],'overviewZoom':navigation['overviewZoom'],'assets':assets,'owner':owner,'triangles':triangles['web'],'raw_triangles':triangles['raw'],'lod_triangles':triangles['lod'],'lod_switch_in_m':300,'lod_switch_out_m':400,'source_provider':'OpenStreetMap via Overture Maps','source_url':'https://www.openstreetmap.org/way/582302404/history','source_license':[{'id':'ODbL-1.0','url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors; Overture Maps2026-10-21.0','role':'Existing frozen owner boundary and identity; not surveyed architectural walls.'}],'asset_license':model_asset_licenses,'source_photos':photos,'reference':{'image':reference['file'],**{k:reference[k] for k in ('author','license','license_url','source','sha256')}},'source_package':'source/precise/'+ID,'source_provenance':{'provider_records':g['source']['provider_records'],'frozen_license':['ODbL-1.0'],'frozen_attribution':g['attribution']},'architecture_style':model.get('architecture_style','独立式花园住宅；南侧花园立面、北侧拱形入口和折线坡屋顶。'),'detail_note':model.get('detail_note','依据建筑文献及照片复原巴金旧居主楼外观；2.2米门扇先验与北侧隐藏屋面4.5米过渡深度属估计，源轮廓仅标识背景替换对象。'),'accuracy_scope':'Photo- and architecture-text-informed Ba Jin main-house exterior only at explicitly estimated scale. Excludes auxiliary buildings, garden, gates, neighbors and interiors. The unshifted mapped owner polygon is context, not surveyed walls; 2.2m door-leaf prior and 4.5m hidden north-roof transition are estimates. Anchor-local ENU is baked into vertices with zero heading.','uncertainty':model.get('uncertainty',[])+[note for note in g['limitations'] if note!='No navigation, mesh, material, compression, browser or production capacity acceptance.']+['External spawn and finite movement/camera probes are screened. Ground probes use mapped context and nearby source footprints, with independently documented source limitations. Runtime building collision uses loaded online map polygons, not the precise mesh. Building openings, arcades, visual stairs and platforms do not automatically gain exact collision or ground support; interior access and stair climbing are not accepted.'],'photo_texture':texture_contract,'accepted':False,'candidate_only':True,'browser_passed':False,'catalog_lifecycle_browser_passed':False,'pending_stages':list(CHECKS),'acceptance':{k:{'status':'pending','scope':'Awaiting actual scoped model/browser review.'} for k in CHECKS}}
 row['uncertainty'].append('The selected outdoor spawn and three camera poses require actual detailed-mesh and source-ground screens. Photo-page GPS and aerial roof color are context clues, not survey control. Exact public-path width and current access are not surveyed. Close-up framing is limited to its declared subject region.')
 for role,key in [('raw','editable_model'),('web','model'),('lod','lod_model'),('native','native_model')]:row[key]=assets[role]['file'];row[role+'_bytes']=assets[role]['bytes'];row[role+'_sha256']=assets[role]['sha256']
 contract.recheck_binding(binding)
 validate_baseline(lock)
 out=Plan(a.output,execute=a.execute_candidate)
 out.add(PUBLIC+'/root-source-owner-mesh-review.json',source=Path(binding['root_model_review']['path']))
 out.add(PUBLIC+'/codec-qa.json',source=a.codec_qa)
 for role,item in assets.items():out.add(item['file'],source=sources[role])
 for name,source in photo_sources.items():out.add(name,source=source)
 for name,source in procedural_sources.items():out.add(name,source=source)
 out.add('source/precise/'+ID+'/geometry-input.json',source=a.owner_input_root/ID/'geometry-input.json')
 out.add('source/precise/'+ID+'/model-metadata.json',source=a.metadata)
 out.add('source/precise/'+ID+'/public-photo-register.json',source=a.photo_register)
 out.add(PUBLIC+'/navigation-proposal.json',source=a.navigation)
 out.add(PUBLIC+'/model-clearance.json',source=screen_sources['report'])
 out.add(PUBLIC+'/model-neighbor-screen.json',source=neighbor_path)
 for index,dependency in enumerate(neighbor_dependencies):out.add(PREFIX+'/neighbor-screen/'+str(index)+'-'+Path(dependency['path']).name,source=Path(dependency['path']))
 out.add(PUBLIC+'/camera-views.json',source=screen_sources['camera_views'])
 out.add(PUBLIC+'/source-ground-review.json',source=ground_path)
 out.add(PUBLIC+'/visual-ground-notes.json',source=Path(ground['visual_ground_review']['path']))
 # Publish only independently checked source evidence and original tool inputs.
 out.add(PREFIX+'/ground-source/'+Path(ground['osm_input']['path']).name,source=Path(ground['osm_input']['path']))
 out.add(PREFIX+'/ground-source/navigation-seed.json',source=Path(ground['candidate_binding']['path']))
 out.add(PREFIX+'/ground-source/source-neighborhood.json',source=Path(ground['effective_neighborhood']['path']))
 out.add(PREFIX+'/screen_source_ground.py',source=Path(ground['tool']['path']))
 out.add(PREFIX+'/screen_frozen_model.py',source=Path(screen_report['screen_script']['path']))
 out.add(PUBLIC+'/runtime35.json',source=a.freeze/'runtime35.json')
 out.add(PUBLIC+'/runtime-collision-scope.json',source=Path(ground['runtime_scope_review']['path']))
 out.add(PREFIX+'/geometry-validation.json',source=a.owner/'geometry-validation.json')
 out.add(PREFIX+'/owner-registry.json',source=a.owner/'precise-buildings-v6.json')
 for filename in ('geometry-comparison-targeted-input.json','generation-provenance.json','main-baseline-preservation.json'):
  out.add(PREFIX+'/'+filename,source=a.owner/filename)
 out.add(PREFIX+'/prepare_integration.py',source=Path(__file__))
 out.add(PREFIX+'/integration_contract.py',source=HERE/'integration_contract.py')
 override_path=a.owner/Path(near['model']['file']).name;need(meta(override_path)=={'bytes':near['model']['size_bytes'],'sha256':near['model']['sha256']},'Real override asset differs')
 out.add(near['model']['file'],source=override_path)
 reg=compose_registry(base_reg,new)
 composition={'passed':True,'scope':'Data-only composition: all previous owner records, near groups, macro provenance and geometry-input records remain exact. One new near group is appended within the existing shared macro, replacing source1950 only and preserving all seventeen neighbors. No model/browser acceptance.','baseline_registry':main_file('data/precise-buildings-v6.json'),'new_owner_registry':desc(a.owner/'precise-buildings-v6.json'),'new_geometry_report':desc(a.owner/'geometry-validation.json'),'old_validation':base_reg['validation'],'existing_same_macro_ids':PRIOR_IDS,'counts':{'owners':FINAL_COUNTS['owners'],'macros':FINAL_COUNTS['owner_macros'],'near':FINAL_COUNTS['near_chunks']}}
 validation=out.add(PREFIX+'/composition-proof.json',data=composition);reg['validation']={k:validation[k] for k in ('file','sha256')};reg['status']='All owner variants have actual geometry checks; candidate model/browser remain pending.';reg['integration_scope']='Candidate37: previous36 navigation records and all12 catalog macros remain preserved; the new building candidate is outside the active ordinary catalog until acceptance.'
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
 contract.recheck_binding(binding)
 return out.finish(status='candidate37_actual_browser_pending',root_source_owner_authorization=binding,codec_qa=codec_desc,baseline=desc(a.freeze/'baseline.json'),runtime_baseline=desc(a.freeze/'runtime35.json'),model_metadata=desc(a.metadata),navigation_count=FINAL_COUNTS['navigation'],owner_count=FINAL_COUNTS['owners'],owner_macro_count=FINAL_COUNTS['owner_macros'],near_count=FINAL_COUNTS['near_chunks'],catalog_unchanged=True,model_accepted=False,browser_accepted=False)

def accept(a):
 binding=contract.validate_root_review(a.root_model_review,a.root_model_review_sha256)
 contract.fresh_output(a.output,budget_bytes=40_000_000)
 plan=read(a.candidate_plan);need(plan.get('root_source_owner_authorization')==binding,'Candidate root authorization differs');contract.verify_descriptor(plan['codec_qa']);need(plan['status']=='candidate37_actual_browser_pending','Wrong candidate plan');lock=read(verified(plan['baseline']));validate_baseline(lock)
 rows={f['file']:f for f in plan['files']}
 for f in rows.values():verified(f)
 nav=read(verified(rows['data/landmarks.json']));reg=read(verified(rows['data/precise-buildings-v6.json']));row=copy.deepcopy(nav[-1]);need(row['id']==ID and nav[:-1]==read(MAIN/'data/landmarks.json'),'Candidate37 mismatch')
 review=read(a.model_review);need(review.get('passed') is True and review.get('reviewer')=='root' and review.get('building_id')==ID,'Actual root model review required')
 need(review.get('asset_sha256')=={k:v['sha256'] for k,v in row['assets'].items()},'Root model review must bind all four actual assets')
 scopes=review.get('scopes',{});need(set(scopes)==set(CHECKS)-{'browser_proof'} and all(isinstance(v,str) and v.strip() for v in scopes.values()),'Root review must state9actual scoped checks')
 browser=read(a.browser);visual=read(a.visual)
 need(browser.get('passed') is True and browser.get('technical_passed') is True and browser.get('finished_at') and browser.get('building_id')==ID,'Actual completed target browser report required')
 need(browser.get('web_sha256')==row['web_sha256'] and browser.get('lod_sha256')==row['lod_sha256'] and browser.get('runtime_baseline_sha256')==plan['runtime_baseline']['sha256'],'Browser must bind exact web/LOD/runtime35')
 for key,name in [('expected_landmarks','data/landmarks.json'),('expected_registry','data/precise-buildings-v6.json'),('reviewed_views',PUBLIC+'/camera-views.json')]:
  need(all(browser.get(key,{}).get(k)==rows[name][k] for k in ('bytes','sha256')),'Browser must bind exact candidate '+key)
 required={'runtime_unchanged','source_owner','full_loaded','lod_loaded','returned_full','owner_lifecycle','neighbors_preserved','keyboard_movement','post_keyup_stopped','directory_direct_link','fragment_reload','reviewed_start_safe','web_textures_decoded','lod_textures_decoded'}
 need(all(browser.get('checks',{}).get(k) is True for k in required),'Missing actual functional browser checks')
 proof_files=[];texture_models={}
 for item in browser.get('texture_proofs',[]):
  p=Path(item['file']);need(meta(p)=={k:item[k] for k in ('bytes','sha256')},'Exact texture proof changed after browser run');proof_files.append(p)
  for proof in read(p)['models']:
   need(proof['sha256'] not in texture_models,'Duplicate exact-model texture proof');texture_models[proof['sha256']]=proof
 need(proof_files and {row['web_sha256'],row['lod_sha256']}<=set(texture_models),'Missing exact web/LOD texture proofs')
 audits=browser.get('asset_audits',[])
 need([r.get('sha256') for r in audits]==[row['web_sha256'],row['lod_sha256'],row['web_sha256']],'Browser texture audits must bind initial full, LOD and returned full in order')
 # Replay the exact frozen v2 validator over the original loaded texture state.
 # No synthetic legacy fields or replacement browser evidence are introduced.
 browser_tools={Path(item['file']).resolve():item for item in browser.get('tools',[])}
 validator_dir=HERE.parents[1]/'qa/bajin-residence/preparation-v2/navigation'
 validator_path=validator_dir/'texture_acceptance.py'
 for tool in (validator_path,validator_dir/'helpers.py'):
  item=browser_tools.get(tool.resolve());need(item and meta(tool)=={k:item[k] for k in ('bytes','sha256')},'Actual browser texture validator changed or missing')
 material_descriptor=browser['material_contract'];material_path=Path(material_descriptor['file'])
 need(meta(material_path)=={k:material_descriptor[k] for k in ('bytes','sha256')},'Actual browser original material contract changed')
 material_contract=read(material_path)
 sys.path.insert(0,str(validator_dir))
 texture_validator=module(validator_path,'bajin_actual_texture_revalidation')
 runtime_states=[browser['initial_full']['assets'][ID],
  next(c for c in browser['captures'] if c['name']=='distant-lod')['state']['assets'][ID],
  browser['return_state']['assets'][ID]]
 image_fields=('image_index','bytes','mime_type','sha256','decoded_dimensions')
 for audit,role,state in zip(audits,('web','lod','web'),runtime_states):
  need(state['id']==ID and state['status']=='loaded' and state['visible'] is True and state['variant']==('full' if role=='web' else 'distant') and state['triangles']==row['triangles' if role=='web' else 'lod_triangles'],'Original runtime snapshot differs from reviewed asset role')
  proof=texture_models[audit['sha256']];need(proof.get('passed') is True and proof['bytes']==audit['bytes']==row[role+'_bytes'],'Actual browser/proof asset differs')
  need(audit['images']==[{k:r[k] for k in image_fields} for r in proof['images']],'Browser original image byte/decode evidence differs from exact proof')
  need(sorted(r['sha256'] for r in audit['images'])==sorted(row['photo_texture']['embedded_sha256_by_role'][role]),'Browser embedded images differ from candidate original image list')
  for img in audit['images']:need(len(img['decoded_dimensions'])==2 and all(type(v)is int and v>0 for v in img['decoded_dimensions']),'Actual browser image dimensions invalid')
  check=audit['texture_check'];need(check.get('passed') is True and check['embedded_png_count']==len(audit['images'])==row['photo_texture']['expected_images'][role],'Actual loaded texture check absent or counts differ')
  replay=texture_validator.check_images_and_runtime(audit,proof,state['actualTextureMaterials'],row,role,material_contract,material_descriptor)
  need(replay==check,'Pure replay of original loaded material/texture/UV state differs from actual browser result')
 for item in browser.get('tools',[]):need(meta(item['file'])=={k:item[k] for k in ('bytes','sha256')},'Browser QA tool changed after actual run')
 need(visual.get('passed') is True and visual.get('reviewer')=='root' and visual.get('building_id')==ID and visual.get('browser_sha256')==meta(a.browser)['sha256'] and visual.get('scope'),'Actual root browser visual review required')
 need(isinstance(visual.get('actually_viewed'),list) and visual['actually_viewed'],'Root must list actual viewed screenshots')
 captures=browser.get('captures',[]);need(len(captures)==5 and {c['name'] for c in captures}==VIEW_NAMES|{'distant-lod','return-full-after-W'} and all(c.get('screenshot_complete') is True for c in captures),'All five actual V20 captures required')
 actual_shots={c['screenshot']['file']:{k:c['screenshot'][k] for k in ('bytes','sha256')} for c in captures}
 need(len(visual['actually_viewed'])==5 and {s['file']:{k:s[k] for k in ('bytes','sha256')} for s in visual['actually_viewed']}==actual_shots,'Root must actually view all five exact browser captures')
 contract.recheck_binding(binding)
 validate_baseline(lock)
 out=Plan(a.output,execute=a.execute_accept)
 for f in rows.values():out.add(f['file'],source=verified(f))
 model_desc=out.add(PUBLIC+'/model-review.json',source=a.model_review);browser_desc=out.add(PUBLIC+'/browser.json',source=a.browser);visual_desc=out.add(PUBLIC+'/visual-review.json',source=a.visual)
 for index,p in enumerate(proof_files,1):out.add(PUBLIC+'/texture-proof-'+str(index)+'.json',source=p)
 out.add(PREFIX+'/accept-tools-v3/prepare_integration.py',source=Path(__file__))
 for tool in (validator_path,validator_dir/'helpers.py'):out.add(PREFIX+'/actual-browser-texture-validator/'+tool.name,source=tool)
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
 reg['status']='All23 owner variants preserve source geometry. The current building model and actual static browser checks passed; dynamic catalog lifecycle is not claimed.'
 # Extend the existing shared macro while retaining all previous records and assets.
 prior_index=read(MAIN/lock['existing_target_catalog_macro']['file'])
 need(prior_index['record_count']==5 and [r['id'] for r in prior_index['models']]==PRIOR_IDS,'Prior shared-macro model records changed')
 macro_ids=PRIOR_IDS+[ID]
 inner=copy.deepcopy(reg);inner.pop('ordinary_catalog',None);inner.pop('integration_scope',None)
 inner['landmarks']=[r for r in reg['landmarks'] if r['id'] in macro_ids];inner['macros']=[m for m in reg['macros'] if m['id']==MACRO];inner['geometry_inputs']={ident:reg['geometry_inputs'][ident] for ident in macro_ids}
 need(len(inner['landmarks'])==6 and len(inner['macros'])==1 and len(inner['macros'][0]['near'])==6,'Shared macro must contain six separate owners and near groups')
 prior_replacement=read(MAIN/prior_index['replacement_registry']['file'])
 need([r for r in inner['landmarks'] if r['id']!=ID]==prior_replacement['landmarks'] and inner['macros'][0]['near'][:-1]==prior_replacement['macros'][0]['near'],'Prior replacement owners or near groups changed')
 need({k:v for k,v in inner['geometry_inputs'].items() if k!=ID}==prior_replacement['geometry_inputs'],'Prior macro geometry inputs changed')
 repl=out.add('data/precise-buildings/macros/'+MACRO+'/replacement.json',data=inner)
 index=copy.deepcopy(prior_index);index['record_count']=6;index['models'].append(row);index['replacement_registry']=repl
 need(index['models'][:-1]==prior_index['models'],'Prior ordinary model records changed')
 idx=out.add('data/precise-buildings/macros/'+MACRO+'/index.json',data=index)
 base_cat=read(MAIN/'data/precise-buildings/catalog.json');cat=copy.deepcopy(base_cat)
 position=next(i for i,m in enumerate(cat['macros']) if m['id']==MACRO);old=cat['macros'][position]
 bbox=[min(old['bbox'][0],row['bbox'][0]),min(old['bbox'][1],row['bbox'][1]),max(old['bbox'][2],row['bbox'][2]),max(old['bbox'][3],row['bbox'][3])]
 cat['macros'][position]={**old,'record_count':6,'bbox':bbox,**idx};cat['macro_count']=len(cat['macros']);cat['record_count']=sum(m['record_count'] for m in cat['macros'])
 cat['scope']='Eighteen individually reviewed ordinary models in twelve macros. The shared macro preserves all five prior records and adds Ba Jin residence. Actual static full/LOD/return/owner/keyboard checks are recorded; dynamic catalog lifecycle remains separately scoped.'
 need(cat['macro_count']==len({m['id'] for m in cat['macros']})==FINAL_COUNTS['catalog_macros'] and cat['record_count']==FINAL_COUNTS['ordinary_records'],'Duplicate macro or wrong catalog counts')
 need([m for m in cat['macros'] if m['id']!=MACRO]==[m for m in base_cat['macros'] if m['id']!=MACRO],'Other eleven catalog macro descriptors changed')
 need(not any(name in rows for m in base_cat['macros'] if m['id']!=MACRO for name in (m['file'],read(MAIN/m['file'])['replacement_registry']['file'])),'Candidate attempts to replace an unrelated catalog index/replacement')
 catdesc=out.add('data/precise-buildings/catalog.json',data=cat);reg['ordinary_catalog']=catdesc
 reg['integration_scope']='Accepted37 static navigation. Previous36 records, all prior source owners and near groups remain exact. Only the existing shared macro index/replacement is extended; eleven other catalog macros stay unchanged. Dynamic-only catalog lifecycle is not claimed by this static proof.'
 replace('data/precise-buildings-v6.json',reg)
 out.add('data/precise-buildings/by-id/'+ID+'.json',data={'schema':'precise-building-pointer-v1','id':ID,'macro_id':MACRO,'macro_index':idx['file'],'feature_local_id':LOCAL})
 ordinary=module(V12/'integration/minimal-tools-v1/registration/ordinary_assets.py','bajin_residence_accept_contract');districts={str(d['id']):d['name'] for d in read(MAIN/'data/districts.json')['districts']};ordinary.record_contract(row,districts);ordinary.bind(row,reg);validate_baseline(lock)
 contract.recheck_binding(binding)
 return out.finish(status='actual_model_and_static_browser_pass_catalog_lifecycle_unclaimed',root_source_owner_authorization=binding,codec_qa=plan['codec_qa'],baseline=plan['baseline'],runtime_baseline=plan['runtime_baseline'],navigation_count=FINAL_COUNTS['navigation'],owner_count=FINAL_COUNTS['owners'],owner_macro_count=FINAL_COUNTS['owner_macros'],near_count=FINAL_COUNTS['near_chunks'],catalog_macro_count=FINAL_COUNTS['catalog_macros'],ordinary_record_count=FINAL_COUNTS['ordinary_records'],browser_accepted=True,model_accepted=True,catalog_lifecycle_browser_passed=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 q=s.add_parser('candidate')
 for key in ('freeze','owner-input-root','owner','metadata','navigation','photo-register','output'):q.add_argument('--'+key,type=Path,required=True)
 q.add_argument('--delivery',type=Path)
 q.add_argument('--codec-qa',type=Path,required=True)
 q.add_argument('--codec-qa-sha256')
 q.add_argument('--root-model-review',type=Path,required=True)
 q.add_argument('--root-model-review-sha256',required=True)
 mode=q.add_mutually_exclusive_group()
 mode.add_argument('--check-only',dest='execute_candidate',action='store_false')
 mode.add_argument('--execute-candidate',action='store_true',help='Write a candidate only after actual input validation; default is read-only')
 q.set_defaults(execute_candidate=False)
 q=s.add_parser('accept')
 for key in ('candidate-plan','model-review','browser','visual','output'):q.add_argument('--'+key,type=Path,required=True)
 q.add_argument('--root-model-review',type=Path,required=True)
 q.add_argument('--root-model-review-sha256',required=True)
 mode=q.add_mutually_exclusive_group()
 mode.add_argument('--check-only',dest='execute_accept',action='store_false')
 mode.add_argument('--execute-accept',action='store_true',help='Write acceptance only after actual model/browser/root evidence; default is read-only')
 q.set_defaults(execute_accept=False)
 a=p.parse_args();globals()[a.command](a)
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError,TypeError,StopIteration) as error:
  print('BAJIN_INTEGRATION_REJECTED: '+str(error),file=sys.stderr);sys.exit(2)
