#!/usr/bin/env python3
"""Small V13 data-only preparation. Never installs MAIN or changes runtime.

freeze reads the completed V12 MAIN, owner builds one isolated near group,
candidate stages the real reviewed model, accept binds actual browser evidence.
Every output is a new directory and every source asset is SHA-bound.
"""
import argparse, copy, gzip, hashlib, html, importlib.util, json, math, os, re, subprocess, sys
import struct
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
MAIN=Path('/workspace/shanghai_project')
V12=HERE.parent.parent/'building-by-building-v12'
RESEARCH=V12/'next-candidate-preparation'
ID='yangpu-library';MACRO='14-13722-6690';LOCAL=1196
NEAR='14-13722-6690--1_-2-s0-s1';KEEP=[50,503,569,1058,1141,1698,1927,2245,2292]
PREFIX='source/city/precise-overrides-v13/yangpu-library'
PUBLIC='data/audit/precise-buildings-v13/yangpu-library'
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
 for row in lock['files']+lock['runtime_files']:
  need(meta(MAIN/row['file'])=={k:row[k] for k in ('bytes','sha256')},'Completed V12 MAIN changed: '+row['file'])
 nav=read(MAIN/'data/landmarks.json');reg=read(MAIN/'data/precise-buildings-v6.json');cat=read(MAIN/'data/precise-buildings/catalog.json')
 need(len(nav)==30 and len({r['id'] for r in nav})==30 and ID not in {r['id'] for r in nav},'Expected30 previous navigation entries')
 need(reg['complete'] and len(reg['landmarks'])==16 and len(reg['macros'])==10 and sum(len(m['near']) for m in reg['macros'])==14,'Expected completed16owner/10macro/14near baseline')
 need(cat['record_count']==11 and cat['macro_count']==len(cat['macros'])==9,'Expected11ordinary/9catalog macro baseline')
 need(MACRO not in {m['id'] for m in reg['macros']} and MACRO not in {m['id'] for m in cat['macros']},'New macro must not already exist')
 return nav,reg,cat

def freeze(a):
 runtime=read(V12/'integration/runtime-delta-v1/effective-runtime31.json')['files']
 need(len(runtime)==31,'Expected31 effective runtime files')
 names={'data/landmarks.json','data/precise-buildings-v6.json','data/precise-buildings/catalog.json','data/districts.json','index.html','package.json'}
 cat=read(MAIN/'data/precise-buildings/catalog.json')
 for c in cat['macros']:
  names.add(c['file']);names.add(read(MAIN/c['file'])['replacement_registry']['file'])
 base=MAIN/'assets/city-detail/macros'/MACRO
 ready=read(base/'READY.json');table=read(base/'feature-table.json.gz')
 near=next(n for n in ready['near'] if LOCAL in n['featureLocalIds'])
 need(near['id']==NEAR and sorted(set(near['featureLocalIds'])-{LOCAL})==KEEP,'Unexpected exact near owner/neighbors')
 names.update(str(p.relative_to(MAIN)) for p in [base/'READY.json',base/'feature-table.json.gz',base/'ownership.json.gz',base/near['file']])
 names.add('source/city/detail/geometry_engine.py')
 lock={'schema':'yangpu-v13-completed-v12-baseline','project':str(MAIN),'counts':{'navigation':30,'owners':16,'owner_macros':10,'near_chunks':14,'ordinary_records':11,'catalog_macros':9},'files':[main_file(n) for n in sorted(names)],'runtime_files':runtime,'runtime_unchanged':True}
 validate_baseline(lock)
 source=read(RESEARCH/'source-identity.json');need(source['candidate_id']==ID,'Wrong source identity')
 feature=next(f for f in table['features'] if f['localId']==LOCAL)
 need(feature==source['effective_feature'],'Frozen source feature changed')
 bounded=source['bounded_uniqueness_scan']
 need(len(bounded['raw_identity_hits'])==len(bounded['effective_identity_hits'])==1 and not bounded['other_linked_property_records'] and not bounded['other_positive_area_overlaps_over_0_01_m2'],'Exact source/parts scope differs')
 for row in bounded['files']:verified({'source':row['path'],'bytes':row['bytes'],'sha256':row['sha256']})
 anchor=source['source_geometry']['centroid_lonlat'];R=6378137.;cos=math.cos(math.radians(anchor[1]));ox=R*math.radians(anchor[0]);oy=R*math.log(math.tan(math.pi/4+math.radians(anchor[1])/2))
 def xy(p):return [(R*math.radians(p[0])-ox)*cos,(R*math.log(math.tan(math.pi/4+math.radians(p[1])/2))-oy)*cos]
 geometry=copy.deepcopy(feature['geometry']);coords=geometry['coordinates'];local={'type':'Polygon','coordinates':[[xy(p) for p in ring] for ring in coords]}
 def evidence(name):
  p=base/name;return {'project_relative_path':str(p.relative_to(MAIN)),**meta(p)}
 source_raw=source['raw_feature'];neighbors=[{'local_id':f['localId'],'key':f['key'],'geometry':f['geometry'],'height':f['height'],'base':f['base'],'retain':True} for f in table['features'] if f['localId'] in KEEP]
 g={'schema':'building-v6-frozen-existing-osm-geometry-input-v1','id':ID,'name_zh':'杨浦区图书馆总馆（原上海市图书馆）','name_en':'Yangpu Library, complete historic and expanded compound','district_id':'310110','district_name':'杨浦区','geometry_source_kind':'existing_overture_osm_footprint','is_osm_building_geometry':True,'status':'Source-owner identity only; no model or browser acceptance.','anchor':anchor,'origin_longitude':anchor[0],'origin_latitude':anchor[1],'anchor_method':'Centroid of existing frozen source Polygon; not a survey control point.','geometry':geometry,'geographic_bbox':[min(p[0] for p in coords[0]),min(p[1] for p in coords[0]),max(p[0] for p in coords[0]),max(p[1] for p in coords[0])],'model_geometry_local_east_north_m':local,'polygon_local_east_north':local['coordinates'][0][:-1],'geometry_components':1,'geometry_rings':3,'coordinate_contract':{'earth_radius_m':R,'geographic':'EPSG:4326','metre_frame':'Source-builder Web Mercator differences times cos(anchor latitude)','gltf_xyz':'[east_m,elevation_m,-north_m]','original_vertex_order_and_all_rings_preserved':True,'geometry_exactly_equals_existing_source':True,'no_photo_retrace_or_bbox_substitution':True},'source':{'release':'2026-10-21.0','key':feature['key'],'overture_id':source_raw['id'],'owner_macro_id':MACRO,'owner_tile':[14,13722,6690],'provider_records':source_raw['properties']['sources'],'properties':source_raw['properties'],'source_geometry':geometry,'frozen_raw_feature':source_raw,'raw_macro_source_file':{'project_relative_path':'data/fullcity-raw/tiles/14/13722/6690.geojson.gz',**meta(MAIN/'data/fullcity-raw/tiles/14/13722/6690.geojson.gz')},'is_osm_geometry':True},'identity_evidence':desc(RESEARCH/'source-identity.json'),'current_city_detail':{'configuration_sha256':ready['configuration_sha256'],'complete_city_macro_count':1708,'complete_city_feature_count':1796419,'owner_macro_id':MACRO,'feature_local_id':LOCAL,'feature_id_base':1,'near_owner_id':NEAR,'far_file':str((base/'far.glb').relative_to(MAIN)),'near_file':str((base/near['file']).relative_to(MAIN)),'near_asset_sha256':near['sha256'],'near_asset_size_bytes':near['size_bytes'],'near_feature_local_ids':near['featureLocalIds'],'original_macro_origin':table['origin'],'same_near_neighbors_to_retain':neighbors,'feature_table_source_file':evidence('feature-table.json.gz'),'ready_source_file':evidence('READY.json'),'ownership_source_file':evidence('ownership.json.gz'),'frozen_effective_feature':feature},'existing_height':{'height_m':feature['height'],'base_m':feature['base'],'quality':feature.get('height_quality'),'use_for_new_model':False,'reason':'CNBH 10m raster estimate, not architectural ridge/eave height.'},'parts':[],'parts_audit':{'source_has_parts':False,'raw_linked_parts':0,'overlapping_unassociated_parts':0,'related_residuals':0,'unique_source_owner_occurrences_in_9macro_scan':1,'scope':'Existing frozen3x3macros, bounded identity study; two courtyard rings remain part of one owner.'},'replacement':{'building_ids':[source_raw['id']],'building_part_ids':[],'feature_local_ids':[LOCAL],'retained_same_near_feature_local_ids':KEEP},'license':'ODbL-1.0','attribution':'© OpenStreetMap contributors; Overture Maps2026-10-21.0','limitations':source['limitations']+['Map ring is an identity/replacement boundary, not a measured architectural wall line.']}
 out=fresh(a.output);write(out/'baseline.json',lock);write(out/ID/'geometry-input.json',g)
 write(out/'runtime31.json',{'schema':'immutable-runtime-files-v13','files':runtime,'file_count':31,'scope':'Actual completed V12 MAIN runtime snapshot; no planned runtime changes.'})
 print(json.dumps({'baseline':desc(out/'baseline.json'),'geometry':desc(out/ID/'geometry-input.json'),'runtime':desc(out/'runtime31.json')},indent=2))

def owner(a):
 lock=read(a.freeze/'baseline.json');validate_baseline(lock);g=read(a.freeze/ID/'geometry-input.json')
 need(g['id']==ID and g['current_city_detail']['feature_local_id']==LOCAL,'Wrong owner source')
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
  result={'schema':'yangpu-v13-installation-plan','files':list(self.files.values()),'file_count':len(self.files),'main_written':False,'runtime_changed':False,**fields}
  write(self.out/'installation-plan.json',result);print(json.dumps({'plan':desc(self.out/'installation-plan.json'),'status':fields.get('status'),'file_count':len(self.files)},indent=2));return result

def check_glb(p):
 with Path(p).open('rb') as f:
  header=f.read(20);magic,version,size,n,typ=struct.unpack('<4sIIII',header);need(magic==b'glTF' and version==2 and size==Path(p).stat().st_size and typ==0x4e4f534a,'Invalid actual GLB header');doc=json.loads(f.read(n))
 need(not any('uri'in x for x in doc.get('images',[])+doc.get('buffers',[])),'External GLB dependencies are not allowed')
 return doc

def candidate(a):
 lock=read(a.freeze/'baseline.json');nav,base_reg,base_cat=validate_baseline(lock);g=read(a.freeze/ID/'geometry-input.json')
 new=read(a.owner/'precise-buildings-v6.json');geo=read(a.owner/'geometry-validation.json')
 need(new['complete'] and geo['pass'] and len(new['macros'])==len(new['landmarks'])==1,'Actual independent owner proof required')
 need(new['macros'][0]['id']==MACRO and new['geometry_inputs'][ID]['sha256']==meta(a.freeze/ID/'geometry-input.json')['sha256'],'New owner source binding differs')
 need(new['landmarks'][0]['confirmed_boundary']==g['geometry'] and len(new['macros'][0]['near'])==1,'New exact owner boundary differs')
 near=new['macros'][0]['near'][0];need(near['id']==NEAR and set(near['featureLocalIds'])==set(KEEP+[LOCAL]) and near['groups'][0]['local_ids']==[LOCAL],'New near must replace only1196 and retain9neighbors')
 model=read(a.metadata);need(model['id']==ID and model['anchor']==g['anchor'] and model.get('ground_base_m')==0 and model.get('rotation_y',0)==0,'Model id/anchor/frame/ground differs')
 height=model['height_estimate_m'];need(type(height) in (int,float) and math.isfinite(height) and 18.49<height<45,'Use actual estimated top height, not18.49m eave')
 need(set(model['assets'])=={'raw','web','lod','native'},'Need four actual model roles')
 assets={};sources={};images={};triangles={}
 for role,item in model['assets'].items():
  name=item.get('path') or item.get('source');need(isinstance(name,str),'Actual asset path required: '+role)
  source=Path(name);source=source if source.is_absolute() else a.metadata.parent/source
  source=source.resolve();d=meta(source);need(d=={k:item[k] for k in ('bytes','sha256')},'Actual model descriptor differs: '+role)
  need(0<d['bytes']<LIMIT,'Model file size limit')
  prefix='assets/native/precise/' if role=='native' else 'assets/models/precise/'
  suffix='.blend' if role=='native' else '-'+role+'.glb';name=prefix+MACRO+'/'+ID+'/'+ID+suffix
  assets[role]={'file':name,**d};sources[role]=source
  if role!='native':
   doc=check_glb(source);images[role]=len(doc.get('images',[]));need(images[role]==0,'Current geometry-only branch does not publish image textures')
   triangles[role]=item.get('triangles');need(type(triangles[role]) is int and triangles[role]>0,'Real expanded triangle count required: '+role)
 proposal=read(a.navigation);navigation=proposal.get('navigation',proposal)
 need(set(navigation)>={'walkStart','bearing'},'Explicit exterior walkStart/bearing required')
 need(len(navigation['walkStart'])==2 and all(math.isfinite(x) for x in navigation['walkStart']) and math.isfinite(navigation['bearing']),'Finite navigation required')
 navigation={'listed':True,'overviewZoom':18,**navigation}
 photos=[];photo_sources={};register=read(RESEARCH/'photo-register.json')
 for photo in register['photos']:
  source=RESEARCH/photo['file'];need(meta(source)=={k:photo[k] for k in ('bytes','sha256')},'Licensed photo changed')
  md=photo['extmetadata'];name='assets/references/precise/'+ID+'/commons-'+str(photo['pageid'])+'.jpg'
  row={'id':'commons-'+str(photo['pageid']),'file':name,**meta(source),'author':html.unescape(re.sub('<[^>]*>','',md['Artist']['value'])),'license':md['LicenseShortName']['value'],'license_url':md['LicenseUrl']['value'],'source':photo['source_page'],'date':md.get('DateTimeOriginal',md['DateTime'])['value'],'embedded_as_texture':False,'modification':'Commons960px thumbnail; resized from original; no photographic pixels used as model texture.'}
  photos.append(row);photo_sources[name]=source
 reference=next(p for p in photos if p['id']=='commons-100208041')
 model_asset_licenses=model.get('asset_license')
 if not isinstance(model_asset_licenses,list):
  need(model_asset_licenses is None or isinstance(model_asset_licenses,str) and 'MIT for original geometry/code' in model_asset_licenses,'Unsupported author license declaration')
  model_asset_licenses=[{'id':'MIT','url':'https://opensource.org/license/mit','attribution':'Copyright (c)2026 agent','role':'Original model geometry and authoring code; map and photographs retain separately declared licenses.'}]
 c=g['current_city_detail'];owner={'macro_id':MACRO,'feature_local_id':LOCAL,'feature_key':c['frozen_effective_feature']['key'],'near_owner_id':NEAR,'baseline_configuration_sha256':c['configuration_sha256'],'baseline_ready_sha256':c['ready_source_file']['sha256'],'baseline_feature_table_sha256':c['feature_table_source_file']['sha256'],'baseline_near_sha256':c['near_asset_sha256'],'baseline_near_feature_local_ids':c['near_feature_local_ids'],'replace_only_local_ids':[LOCAL],'preserve_neighbor_local_ids':KEEP}
 row={'id':ID,'name':g['name_zh'],'kind':'building','detail_level':'architectural','district':{'id':'310110','name':'杨浦区'},'districtId':'310110','district_name':'杨浦区','anchor':g['anchor'],'lng':g['anchor'][0],'lat':g['anchor'][1],'bbox':g['geographic_bbox'],'confirmed_boundary':g['geometry'],'geometry_input_sha256':meta(a.freeze/ID/'geometry-input.json')['sha256'],'height_m':height,'height_estimated':True,'height_note':model.get('height_note','Official planning18.49m refers to old eave; current highest roof/ornaments are photo-informed estimates, not measured height.'),'navigation':navigation,'walkStart':navigation['walkStart'],'bearing':navigation['bearing'],'overviewZoom':navigation['overviewZoom'],'assets':assets,'owner':owner,'triangles':triangles['web'],'raw_triangles':triangles['raw'],'lod_triangles':triangles['lod'],'lod_switch_in_m':300,'lod_switch_out_m':400,'source_provider':'OpenStreetMap via Overture Maps','source_url':'https://www.openstreetmap.org/relation/21094674/history','source_license':[{'id':'ODbL-1.0','url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors; Overture Maps2026-10-21.0','role':'Existing frozen owner boundary and identity; not surveyed architectural walls.'}],'asset_license':model_asset_licenses,'source_photos':photos,'reference':{'image':reference['file'],**{k:reference[k] for k in ('author','license','license_url','source','sha256')}},'source_package':'source/precise/'+ID,'source_provenance':{'provider_records':g['source']['provider_records'],'frozen_license':['ODbL-1.0'],'frozen_attribution':g['attribution']},'architecture_style':'中国传统宫殿式重檐歇山旧馆，与2018年修缮扩建后的现代石材、玻璃馆体。','detail_note':model.get('detail_note','整馆包含历史入口、重檐琉璃屋顶、斗拱栏杆、现代扩建和两处内院；隐藏细节有明确推估。'),'accuracy_scope':'Photo/plan-informed exterior reconstruction of the whole mapped compound; hidden details and dimensions remain documented estimates.','uncertainty':model.get('uncertainty',[])+g['limitations'],'photo_texture':{'mode':'none','expected_images':images,'note':'Licensed reference photographs only; no embedded image textures.'},'accepted':False,'candidate_only':True,'browser_passed':False,'catalog_lifecycle_browser_passed':False,'pending_stages':list(CHECKS),'acceptance':{k:{'status':'pending','scope':'Awaiting actual scoped model/browser review.'} for k in CHECKS}}
 for role,key in [('raw','editable_model'),('web','model'),('lod','lod_model'),('native','native_model')]:row[key]=assets[role]['file'];row[role+'_bytes']=assets[role]['bytes'];row[role+'_sha256']=assets[role]['sha256']
 out=Plan(a.output)
 for role,item in assets.items():out.add(item['file'],source=sources[role])
 for name,source in photo_sources.items():out.add(name,source=source)
 out.add('source/precise/'+ID+'/geometry-input.json',source=a.freeze/ID/'geometry-input.json')
 out.add('source/precise/'+ID+'/model-metadata.json',source=a.metadata)
 out.add('source/precise/'+ID+'/photo-register.json',source=RESEARCH/'photo-register.json')
 out.add(PUBLIC+'/navigation-proposal.json',source=a.navigation)
 out.add(PUBLIC+'/runtime31.json',source=a.freeze/'runtime31.json')
 out.add(PREFIX+'/geometry-validation.json',source=a.owner/'geometry-validation.json')
 out.add(PREFIX+'/owner-registry.json',source=a.owner/'precise-buildings-v6.json')
 snapshot=out.out/'prepare_integration.snapshot.py'
 with snapshot.open('xb') as f:f.write(Path(__file__).read_bytes())
 out.add(PREFIX+'/prepare_integration.py',source=snapshot)
 override_path=a.owner/Path(near['model']['file']).name;need(meta(override_path)=={'bytes':near['model']['size_bytes'],'sha256':near['model']['sha256']},'Real override asset differs')
 out.add(near['model']['file'],source=override_path)
 reg=copy.deepcopy(base_reg);reg['macros']+=copy.deepcopy(new['macros']);reg['landmarks']+=copy.deepcopy(new['landmarks']);reg['geometry_inputs'].update(copy.deepcopy(new['geometry_inputs']))
 composition={'passed':True,'scope':'Data-only composition: previous16owners/10macros/14near entries remain exact, plus one independently decoded exact-owner near group with9neighbors. No model/browser acceptance.','baseline_registry':main_file('data/precise-buildings-v6.json'),'new_owner_registry':desc(a.owner/'precise-buildings-v6.json'),'new_geometry_report':desc(a.owner/'geometry-validation.json'),'old_validation':base_reg['validation'],'counts':{'owners':17,'macros':11,'near':15}}
 validation=out.add(PREFIX+'/composition-proof.json',data=composition);reg['validation']={k:validation[k] for k in ('file','sha256')};reg['status']='All17owner variants have actual geometry checks; candidate model/browser remain pending.';reg['integration_scope']='Candidate31: previous30navigation and9catalog macros preserved; Yangpu candidate remains outside the active ordinary catalog.'
 ordinary=module(V12/'integration/minimal-tools-v1/registration/ordinary_assets.py','yangpu_ordinary_contract');districts={str(d['id']):d['name'] for d in read(MAIN/'data/districts.json')['districts']};ordinary.record_contract(row,districts,candidate_only=True);ordinary.bind(row,reg)
 out.add('data/landmarks.json',data=nav+[row]);out.add('data/precise-buildings-v6.json',data=reg);out.add('data/precise-candidates/'+ID+'.json',data=row)
 if a.delivery:
  delivery=read(a.delivery)
  for f in delivery['files']:
   need(f['file'].startswith(('source/precise/'+ID+'/','assets/models/precise/'+MACRO+'/'+ID+'/','assets/native/precise/'+MACRO+'/'+ID+'/','assets/references/precise/'+ID+'/')),'Optional model delivery escapes scope')
   if f['file'] in out.files:need(out.files[f['file']]['sha256']==f['sha256'],'Conflicting optional delivery asset')
   else:out.add(f['file'],source=verified(f))
 validate_baseline(lock)
 return out.finish(status='candidate31_actual_browser_pending',baseline=desc(a.freeze/'baseline.json'),runtime_baseline=desc(a.freeze/'runtime31.json'),model_metadata=desc(a.metadata),navigation_count=31,owner_count=17,owner_macro_count=11,near_count=15,catalog_unchanged=True,model_accepted=False,browser_accepted=False)

def accept(a):
 plan=read(a.candidate_plan);need(plan['status']=='candidate31_actual_browser_pending','Wrong candidate plan');lock=read(verified(plan['baseline']));validate_baseline(lock)
 rows={f['file']:f for f in plan['files']}
 for f in rows.values():verified(f)
 nav=read(verified(rows['data/landmarks.json']));reg=read(verified(rows['data/precise-buildings-v6.json']));row=copy.deepcopy(nav[-1]);need(row['id']==ID and nav[:-1]==read(MAIN/'data/landmarks.json'),'Candidate31 mismatch')
 review=read(a.model_review);need(review.get('passed') is True and review.get('reviewer')=='root' and review.get('building_id')==ID,'Actual root model review required')
 need(review.get('asset_sha256')=={k:v['sha256'] for k,v in row['assets'].items()},'Root model review must bind all four actual assets')
 scopes=review.get('scopes',{});need(set(scopes)==set(CHECKS)-{'browser_proof'} and all(isinstance(v,str) and v.strip() for v in scopes.values()),'Root review must state9actual scoped checks')
 browser=read(a.browser);visual=read(a.visual)
 need(browser.get('passed') is True and browser.get('technical_passed') is True and browser.get('finished_at') and browser.get('building_id')==ID,'Actual completed target browser report required')
 need(browser.get('web_sha256')==row['web_sha256'] and browser.get('lod_sha256')==row['lod_sha256'] and browser.get('runtime_baseline_sha256')==plan['runtime_baseline']['sha256'],'Browser must bind exact web/LOD/runtime31')
 required={'runtime_unchanged','source_owner','full_loaded','lod_loaded','returned_full','owner_lifecycle','neighbors_preserved','keyboard_movement','post_keyup_stopped'}
 need(all(browser.get('checks',{}).get(k) is True for k in required),'Missing actual functional browser checks')
 need(visual.get('passed') is True and visual.get('reviewer')=='root' and visual.get('building_id')==ID and visual.get('browser_sha256')==meta(a.browser)['sha256'] and visual.get('scope'),'Actual root browser visual review required')
 need(isinstance(visual.get('actually_viewed'),list) and visual['actually_viewed'],'Root must list actual viewed screenshots')
 out=Plan(a.output)
 for f in rows.values():out.add(f['file'],source=verified(f))
 model_desc=out.add(PUBLIC+'/model-review.json',source=a.model_review);browser_desc=out.add(PUBLIC+'/browser.json',source=a.browser);visual_desc=out.add(PUBLIC+'/visual-review.json',source=a.visual)
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
 inner=copy.deepcopy(reg);inner.pop('ordinary_catalog',None);inner.pop('integration_scope',None);inner['landmarks']=[r for r in reg['landmarks'] if r['id']==ID];inner['macros']=[m for m in reg['macros'] if m['id']==MACRO];inner['geometry_inputs']={ID:reg['geometry_inputs'][ID]}
 repl=out.add('data/precise-buildings/macros/'+MACRO+'/replacement.json',data=inner)
 index={'schema':'precise-building-macro-v1','url_base':'project-root','macro_id':MACRO,'record_count':1,'models':[row],'replacement_registry':repl};idx=out.add('data/precise-buildings/macros/'+MACRO+'/index.json',data=index)
 cat=read(MAIN/'data/precise-buildings/catalog.json');cat['macros'].append({'id':MACRO,'record_count':1,'bbox':row['bbox'],**idx});cat['macro_count']=10;cat['record_count']=12;cat['scope']='Twelve individually reviewed ordinary records in ten macros. Yangpu actual static full/LOD/return/owner/keyboard test is recorded; dynamic catalog lifecycle remains separately scoped.'
 catdesc=out.add('data/precise-buildings/catalog.json',data=cat);reg['ordinary_catalog']=catdesc;reg['integration_scope']='Accepted31 static navigation; previous30 records and prior catalog index/replacement bytes remain exact. Yangpu dynamic catalog lifecycle is not claimed by this static proof.'
 replace('data/precise-buildings-v6.json',reg)
 out.add('data/precise-buildings/by-id/'+ID+'.json',data={'schema':'precise-building-pointer-v1','id':ID,'macro_id':MACRO,'macro_index':idx['file'],'feature_local_id':LOCAL})
 ordinary=module(V12/'integration/minimal-tools-v1/registration/ordinary_assets.py','yangpu_accept_contract');districts={str(d['id']):d['name'] for d in read(MAIN/'data/districts.json')['districts']};ordinary.record_contract(row,districts);ordinary.bind(row,reg);validate_baseline(lock)
 return out.finish(status='actual_model_and_static_browser_pass_catalog_lifecycle_unclaimed',baseline=plan['baseline'],runtime_baseline=plan['runtime_baseline'],navigation_count=31,owner_count=17,owner_macro_count=11,near_count=15,catalog_macro_count=10,ordinary_record_count=12,browser_accepted=True,model_accepted=True,catalog_lifecycle_browser_passed=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 q=s.add_parser('freeze');q.add_argument('--output',type=Path,required=True)
 q=s.add_parser('owner');q.add_argument('--freeze',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q=s.add_parser('candidate')
 for key in ('freeze','owner','metadata','navigation','output'):q.add_argument('--'+key,type=Path,required=True)
 q.add_argument('--delivery',type=Path)
 q=s.add_parser('accept')
 for key in ('candidate-plan','model-review','browser','visual','output'):q.add_argument('--'+key,type=Path,required=True)
 a=p.parse_args();globals()[a.command](a)
if __name__=='__main__':main()
