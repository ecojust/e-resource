#!/usr/bin/env python3
"""Bind actual Sihang source/provenance and registration documents; no model/browser run."""
from pathlib import Path,PurePosixPath
import argparse,copy,hashlib,html,importlib.util,json,re,sys
HERE=Path(__file__).resolve().parent;INTEGRATION=HERE.parent;V12=INTEGRATION.parent
sys.path.insert(0,str(INTEGRATION/'qa-v1'));sys.dont_write_bytecode=True
from sihang_inputs import IDS,GEOMETRY_SHA,actual,read,meta,descriptor,identity,need,PREBROWSER
ID=IDS[0];MACRO='14-13720-6693';DEFAULT_SOURCE=V12/'sihang-model/source-v2'
def json_file(p):return json.loads(Path(p).read_bytes())
def public_text_source(desc):
 content=actual(desc).read_bytes();content.decode('utf-8')
 need(not re.search(rb'data:(?:image|application/(?:pdf|octet-stream))[^,]*,|[A-Za-z0-9+/]{512,}={0,2}',content,re.I),'Private encoded image/document payload is not public text evidence')
def contract_modules():
 lock=json_file(HERE/'reused-contracts.lock.json')
 for row in lock['files']:actual(row)
 old=V12.parent/'building-by-building-v11/registration-museum-v2-preparation/toolchain/registration';sys.path.insert(0,str(old))
 import contracts,report_adapters
 need(Path(contracts.__file__).resolve()==old/'contracts.py' and Path(report_adapters.__file__).resolve()==old/'report_adapters.py','Unexpected generic contract import')
 return old,contracts,report_adapters,lock
def aperture_review(target,source):
 desc=target['actual'].get('all_occluder_raw_review');doc=read(desc)
 need(doc.get('schema')=='sihang-independent-all-part-aperture-foreground-review-v1' and doc.get('all_seven_eroded_apertures_clear') is True,'Actual complete seven-aperture foreground review required')
 need(doc.get('source_freeze_sha256')==target['actual']['source_freeze']['sha256'] and doc.get('calibration_sha256')==meta(source/'calibration.json')['sha256'],'Aperture review source version differs')
 bound={}
 for row in doc['inputs']:
  file={'source':row['file'],**identity(row)};actual(file);bound[row['file']]=file
 for key in ('raw','raw_geometry','source_freeze'):
  row=target['actual'][key];need(bound.get(row['source'])=={'source':row['source'],**identity(row)},'Aperture review actual input differs: '+key)
 checks=doc.get('checks',[])
 need(len(checks)==7 and len({c['feature'] for c in checks})==7 and all(c.get('clear_within_stated_edge_exclusion') is True and c.get('intersecting_triangles')==0 and c.get('actual_foreground_occluder_parts')==[] and c.get('union_obstruction_area_m2')==0 for c in checks),'Aperture review includes an obstruction or missing aperture')
 need(doc.get('aperture_edge_exclusion_m')==.025 and doc.get('view_scope'),'Aperture review finite boundary/scope differs')
 feature=[r for path,r in bound.items() if Path(path).name=='feature-manifest.json'];need(len(feature)==1,'Actual reviewed feature manifest missing')
 return desc,feature[0]
def write(p,value):
 need(not p.exists() and not p.is_symlink(),'Refuse existing output: '+str(p))
 data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 need(0<len(data)<100_000_000,'Generated file exceeds strict size limit')
 need(not re.search(rb'data:(?:image|application/(?:pdf|octet-stream))[^,]*,|[A-Za-z0-9+/]{512,}={0,2}',data,re.I),'Encoded private snapshots are not public documents')
 with p.open('xb') as f:f.write(data)
 return descriptor(p)
def source_files(source):
 freeze=json_file(source/'source-freeze.json')
 need(freeze.get('schema')=='sihang-warehouse-author-source-freeze-v12' and freeze.get('id')==ID and freeze.get('source_geometry_sha256')==GEOMETRY_SHA,'Actual Sihang source freeze required')
 need(freeze.get('private_reference_pixels_distributed') is False,'Private image distribution forbidden')
 allow=json_file(HERE/'public-binary-source-allowlist.json');actual(allow['licensed_reference_provenance'])
 rows=[];names=set()
 for row in freeze['files']:
  name=row['path'];p=PurePosixPath(name)
  need(not p.is_absolute() and '..' not in p.parts and str(p)==name and name not in names and '__pycache__' not in p.parts,'Unsafe/duplicate frozen source path')
  path=source/name;need(path.is_file() and not path.is_symlink() and meta(path)==identity(row),'Author source freeze changed: '+name)
  if p.suffix.lower() in ('.jpg','.jpeg','.png'):
   need(p.parts[0]=='references' and len(p.parts)==2 and identity(row)==allow['reference_images'].get(p.name),'Only the nine verified licensed Commons image bytes may be public')
  elif p.suffix.lower()=='.otf':need(name==allow['font']['path'] and identity(row)==identity(allow['font']),'Only the verified licensed font subset may be public')
  else:
   need(p.suffix in ('.py','.json','.md','.txt') or p.name=='LICENSE','Unreviewed binary source payload')
   content=path.read_bytes();content.decode('utf-8')
   need(not re.search(rb'data:(?:image|application/(?:pdf|octet-stream))[^,]*,|[A-Za-z0-9+/]{512,}={0,2}',content,re.I),'Encoded private source pixels are forbidden')
  rows.append({**descriptor(path),'file':'source/precise/'+ID+'/'+name,'kind':'public-author-source'});names.add(name)
 rows.append({**descriptor(source/'source-freeze.json'),'file':'source/precise/'+ID+'/source-freeze.json','kind':'public-source-freeze'})
 return rows
def source_photos(source):
 register=json_file(source/'photo-reference-register.json');photos=[]
 primary=next(p for p in register['photos'] if p.get('pageid')==148812398)
 for row in register['photos']:
  need(row.get('embedded_as_texture') is False and row.get('viewed_by_author') is True,'Reference image usage/author view missing')
  inherited=primary if row.get('file')=='references/commons-148812398-1920.jpg' else row
  if inherited is not row:need(row.get('source_license')=='CC0' and row.get('unmodified_image_response') is True,'High-resolution original provenance differs')
  name=Path(row['file']).name;need(name.startswith('commons-') and name.endswith('.jpg'),'Only licensed Commons reference pixels may be delivered')
  image={**descriptor(source/row['file']),'file':'assets/references/precise/'+ID+'/'+name}
  need(identity(image)==identity(row),'Actual licensed reference bytes differ')
  author=html.unescape(re.sub('<[^>]+>','',inherited['author'])).strip()
  photos.append({'id':name[:-4],'author':author,'license':{'CC BY-SA 4.0':'CC-BY-SA-4.0','CC BY 4.0':'CC-BY-4.0','CC0':'CC0-1.0'}[inherited['license']],'license_url':inherited['license_url'],'source_url':inherited['url'],'date':inherited['date'],'embedded_as_texture':False,'image':image})
 need(len(photos)==9 and len({p['id'] for p in photos})==9,'All nine actual licensed reference files required')
 return photos
def package_spec(source,out):
 rows=source_files(source);photos=source_photos(source)
 source_license=[{'id':'ODbL-1.0','url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors; Overture Maps 2026-10-21.0','role':'Original frozen map owner boundary and source identity; not surveyed architectural walls.'}]
 asset_license=[{'id':'MIT','url':'https://opensource.org/license/mit','attribution':'Copyright (c) 2026 agent','role':'Original model geometry and authoring code, as declared in author LICENSE.'},{'id':'OFL-1.1','url':'https://openfontlicense.org/open-font-license-official-text/','attribution':'Noto Sans CJK contributors','role':'Bundled Noto Sans CJK subset font; original license retained separately.'}]
 paths={r:'assets/models/precise/'+MACRO+'/'+ID+'/'+ID+'-'+r+'.glb' for r in ('raw','web','lod')};paths['native']='assets/native/precise/'+MACRO+'/'+ID+'/'+ID+'.blend'
 spec={'schema':'precise-building-package-input-v1','id':ID,'paths':paths,'provenance':{'id':ID,'name':'四行仓库（含毗邻大陆银行仓库）','district':{'id':'310106','name':'静安区'},'source_provider':'OpenStreetMap via Overture Maps','source_url':'https://www.openstreetmap.org/way/73897418/history','source_license':source_license,'asset_license':asset_license,'source_photos':photos,'geometry_input_sha256':GEOMETRY_SHA,'appearance_epoch':'2015 restored exterior, cross-checked against 2017–2026 licensed photographs; not a 1937 battlefield reconstruction.','browser_accepted':False},'required_copyright_tokens':['OpenStreetMap contributors','Overture Maps','SIL OFL1.1'],'model_accepted':False,'browser_accepted':False}
 # Validate against the actual selected packaging tool before exposing the spec.
 tool=V12/'packaging/toolchain-v1/package_modern.py';sys.path.insert(0,str(tool.parent));module_spec=importlib.util.spec_from_file_location('sihang_package_format',tool);module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
 module.validate_spec(spec,HERE)
 need(out.resolve().parent==HERE and not out.exists(),'Use a fresh source/provenance revision inside registration-v1');out.mkdir()
 package=write(out/'package-spec.json',spec)
 whitelist=write(out/'public-author-source-whitelist.json',{'schema':'sihang-public-author-source-whitelist-v12','building_id':ID,'source_freeze':descriptor(source/'source-freeze.json'),'files':rows,'file_count':len(rows),'source_photos':photos,'private_reference_pixels_included':False,'model_accepted':False,'browser_accepted':False,'scope':'Only exact frozen author public files; licensed Commons pixels and font are explicit. Private design-publication images are excluded.'})
 return {'package_spec':package,'public_author_source_whitelist':whitelist,'actual_photo_count':len(photos),'model_accepted':False,'browser_run':False}
def registration(request_path,out):
 request=json_file(request_path)
 need(request.get('schema')=='sihang-actual-registration-request-v12' and request.get('building_id')==ID,'Actual Sihang registration request required')
 need(out.resolve().parent==HERE and not out.exists(),'Registration output must be a new registration-v1 child')
 required=('target_spec','source_geometry','source_freeze','package_record','decoded_report','independent_raw_review','native_report','root_native_review','navigation','source_delivery_whitelist','prebrowser_review','model_metadata')
 for key in required:actual(request.get(key))
 need(request['source_geometry']['sha256']==GEOMETRY_SHA,'Original frozen source geometry required')
 # Reuse the already tested V11 generic document/finite contracts directly.
 # The Museum-specific supplement dispatcher and ID defaults are not invoked.
 old,contracts,report_adapters,reused=contract_modules()
 inputs=contracts.Inputs()
 for row in reused['files']:inputs.file(row)
 target=inputs.json(request['target_spec']);package=inputs.json(request['package_record']);decoded=inputs.json(request['decoded_report']);geometry=inputs.json(request['source_geometry'])
 need(target.get('id')==ID and target.get('status')=='ready' and target.get('source_geometry')==request['source_geometry'],'Actual ready source-bound target required')
 need(target['actual']['source_freeze']==request['source_freeze'] and package.get('building_id')==ID and package.get('packaging_passed') is True,'Actual source/package binding differs')
 need(package.get('modern_target',{}).get('sha256')==request['target_spec']['sha256'],'Package and registration target differ')
 source=actual(request['source_freeze']).parent;frozen=source_files(source)
 aperture,feature_manifest=aperture_review(target,source)
 whitelist=inputs.json(request['source_delivery_whitelist'])
 need(whitelist.get('schema')=='sihang-public-author-source-whitelist-v12' and whitelist.get('source_freeze')==request['source_freeze'] and whitelist.get('files')==frozen and whitelist.get('private_reference_pixels_included') is False,'Final public author whitelist differs')
 photos=source_photos(source);need(photos==whitelist['source_photos']==package['provenance']['source_photos'],'Actual package/reference provenance differs')
 request['source_roles']={'calibration':descriptor(source/'calibration.json')}
 checked_package,checked_photos=contracts.package_and_photos(request,target,inputs)
 need(checked_package==package and checked_photos==photos,'Full generic package/photo contract differs')
 raw_report,structure=report_adapters.validate_independent_raw(request,target,package,inputs)
 report_adapters.validate_finite_decoded(decoded,request,target,package,inputs)
 nav=contracts.navigation(request,target,geometry,package,inputs)
 review=contracts.prebrowser_review(request,target,package,photos,decoded,inputs)
 need(review.get('reviewer')=='root','Root actual nine-section review required')
 visual=inputs.json(request['root_native_review']);native=inputs.json(request['native_report'])
 need(visual.get('schema')=='sihang-root-native-visual-v12' and visual.get('passed') is True and visual.get('actually_viewed') is True and visual.get('final') is True and visual.get('reviewer')=='root','Actual root native review is pending')
 metadata=inputs.json(request['model_metadata']);need(metadata.get('schema')=='sihang-warehouse-model-v12' and metadata.get('id')==ID,'Final author model metadata required')
 for role,asset in package['registration_assets'].items():
  actual(asset);need(identity(asset)==identity(package['assets'][role]),'Actual packaged role changed')
 inputs.recheck()
 out.mkdir();marker=out/'INCOMPLETE';marker.write_text('Actual document validation has not finished. Never install this directory.\n')
 limitations=list(dict.fromkeys(review['limitations']+visual['limitations']+nav['limitations']))
 summary={'schema':'sihang-prebrowser-acceptance-summary-v12','building_id':ID,'prebrowser_scope_passed':True,'browser_accepted':False,'registered':False,'request':descriptor(request_path),'review':request['prebrowser_review'],'evidence':{key:request[key] for key in required},'raw_sha256':package['assets']['raw']['sha256'],'limitations':limitations,'scope':'Nine existing source/model reviews copied only after actual file, independent raw/decoded finite, root image and navigation checks. No photographic survey, full-route collision or browser acceptance.'}
 summary.update(copy.deepcopy(review['sections']));summary_desc=write(out/'prebrowser-acceptance-summary.json',summary)
 provenance=package['provenance'];entry={key:copy.deepcopy(provenance[key]) for key in ('id','name','district','source_provider','source_url','source_license','asset_license','appearance_epoch')}
 entry.update(geometry_input=request['source_geometry'],assets=package['registration_assets'],source_photos=photos,primary_photo=review['registration']['primary_photo'],source_package='source/precise/'+ID,height={'metres':review['sections']['height_evidence']['height_m'],'estimated':True,'note':review['sections']['height_evidence']['scope']},uncertainty=limitations,navigation=nav['navigation'],navigation_evidence=request['navigation'],architecture_style=review['registration']['architecture_style'],detail_note=review['registration']['detail_note'])
 entry['acceptance']={key:{'status':'passed','evidence':summary_desc,'section':key} for key in sorted(PREBROWSER)}
 entry['acceptance']['browser_proof']={'status':'pending','reason':'Actual candidate static browser and root screenshot review are required.'}
 registration_desc=write(out/'registration.draft.json',{'schema':'precise-registration-input-v1','buildings':[entry]})
 model={'registration_input':registration_desc,'package':request['package_record'],'model_metadata':request['model_metadata'],'navigation_input':request['navigation'],'prebrowser_summary':summary_desc,'actual_decoded':request['decoded_report'],'native_render':request['native_report'],'root_native_review':request['root_native_review']}
 model_input={'schema':'sihang-browser-model-inputs-v12','status':'READY_FOR_PROFILE','targets':IDS,'runtime_baseline':json_file(INTEGRATION/'qa-v1/runtime-reference.json'),'osm_evidence_set':descriptor(INTEGRATION/'osm-observation-v1/fixture-v1/sihang-osm-fixture-set.json'),'model_evidence_gate':descriptor(INTEGRATION/'qa-v1/sihang_model_gate.py'),'models':{ID:model},'model_accepted':False,'browser_accepted':False}
 model_input_desc=write(out/'model-inputs.actual.json',model_input)
 sys.path.insert(0,str(INTEGRATION/'app-v1'))
 from prepare_sihang import context
 from sihang_inputs import load_model_inputs
 lock,_,registry,registrar,ordinary,districts=context(Path('/workspace/shanghai_project'))
 row,copies=registrar.normalize(entry,out,Path('/workspace/shanghai_project'),districts)
 need(row['pending_stages']==['browser_proof'] and not row['accepted'],'Only actual browser stage may remain pending')
 # Use actual author, package, finite/native/root evidence gate before emitting
 # an application spec; a failed document run keeps its INCOMPLETE marker.
 binding=load_model_inputs(actual(model_input_desc),{ID:row},Path('/workspace/shanghai_project'))
 public=list(frozen)
 def add(file,desc,kind):
  actual(desc);public.append({**desc,'file':file,'kind':kind})
 prefix='source/precise/'+ID+'/delivery/'
 add(prefix+'evidence/all-aperture-occluders.json',aperture,'actual-aperture-evidence');add(prefix+'evidence/raw-feature-manifest.json',feature_manifest,'actual-feature-manifest')
 for role,asset in package['registration_assets'].items():add(asset['file'],asset,'model-asset')
 for photo in photos:add(photo['image']['file'],photo['image'],'licensed-reference')
 for name,desc in [('registration.draft.json',registration_desc),('prebrowser-acceptance-summary.json',summary_desc),('model-inputs.actual.json',model_input_desc),('request.json',descriptor(request_path)),('prepare_actual.py',descriptor(Path(__file__)))]:add(prefix+name,desc,'actual-delivery-document')
 for key in required:
  if key not in ('source_geometry','source_freeze','source_delivery_whitelist'):add(prefix+'evidence/'+key+'.json',request[key],'actual-evidence')
 suite=inputs.json(decoded['finite_actual_decoded_report']);add(prefix+'evidence/finite-suite.json',decoded['finite_actual_decoded_report'],'actual-evidence')
 add(prefix+'evidence/raw-structure.json',target['actual']['source_structure_report'],'actual-evidence')
 add(prefix+'evidence/finite-requests.json',target['actual']['probe_set'],'actual-evidence')
 for role,document in suite['roles'].items():
  for key in ('finite_report','array_manifest','chunk_retention'):add(prefix+'evidence/decoded-'+role+'-'+key+'.json',document[key],'actual-decoded-evidence')
 for image in native['images']:
  source_path=image.get('source') or str(actual(request['native_report']).parent/image['file'])
  add(prefix+'previews/'+Path(image['file']).name,{'source':source_path,**identity(image)},'actual-native-preview')
 for item in request.get('public_evidence_files',[]):
  need(item['file'].startswith('source/precise/'+ID+'/') and Path(item['file']).suffix in ('.json','.py','.mjs','.js','.md','.txt'),'Additional evidence must be explicit public text/code, not private pixels')
  public_text_source(item)
  add(item['file'],item,'explicit-public-evidence')
 names=[r['file'].casefold() for r in public];need(len(names)==len(set(names)),'Public delivery destinations collide')
 manifest_desc=write(out/'delivery-manifest.json',{'schema':'sihang-model-stage-delivery-manifest-v12','building_id':ID,'files':public,'file_count':len(public),'exclusive_per_file_bytes':100_000_000,'source_whitelist':request['source_delivery_whitelist'],'private_reference_pixels_included':False,'model_accepted':False,'browser_accepted':False,'registered':False,'installed':False})
 spec={'schema':'sihang-app-input-v12','registration_input':registration_desc,'package':request['package_record'],'model_metadata':request['model_metadata'],'navigation_input':request['navigation'],'model_inputs':model_input_desc,'model_source_delivery_manifest':manifest_desc,'public_evidence_files':[]}
 spec_desc=write(out/'app-spec.actual.json',spec)
 dependency_files=[descriptor(old/name) for name in ('contracts.py','report_adapters.py','public_dependency_compat.py')]
 input_lock=write(out/'actual-input-lock.json',{'schema':'sihang-actual-registration-input-lock-v12','request':descriptor(request_path),'frozen_generic_document_contracts':dependency_files,'files':[{'source':source,**value} for source,value in sorted(inputs.bound.items())],'outputs':[registration_desc,summary_desc,model_input_desc,manifest_desc,spec_desc],'browser_accepted':False,'registered':False,'installed':False})
 inputs.recheck();marker.unlink()
 return {'registration':registration_desc,'model_inputs':model_input_desc,'delivery_manifest':manifest_desc,'app_spec':spec_desc,'input_lock':input_lock,'browser_accepted':False,'candidate_created':False,'main_written':False}
def model_delivery(request_path,out):
 request=json_file(request_path)
 need(request.get('schema')=='sihang-model-only-delivery-request-v12' and request.get('building_id')==ID,'Actual model-only request required')
 need(out.resolve().parent==HERE and not out.exists(),'Model delivery output must be new')
 required=('target_spec','source_geometry','source_freeze','package_record','decoded_report','independent_raw_review','native_report','root_native_review','source_delivery_whitelist','model_metadata')
 docs={key:read(request.get(key)) for key in required};package=docs['package_record'];target=docs['target_spec'];decoded=docs['decoded_report'];native=docs['native_report'];visual=docs['root_native_review'];metadata=docs['model_metadata']
 need(target.get('id')==ID and target.get('status')=='ready' and target['source_geometry']==request['source_geometry'] and request['source_geometry']['sha256']==GEOMETRY_SHA,'Actual final model target/source required')
 need(target['actual']['source_freeze']==request['source_freeze'] and package.get('building_id')==ID and package.get('packaging_passed') is True and package['modern_target']['sha256']==request['target_spec']['sha256'],'Actual package/source identity differs')
 need(decoded.get('schema')=='modern-actual-decoded-package-v11' and decoded.get('passed') is True and decoded.get('building_id')==ID and decoded.get('package_record_sha256')==request['package_record']['sha256'] and decoded.get('target_sha256')==request['target_spec']['sha256'],'Actual final decoder/package proof required')
 need(decoded.get('web_exact_oriented_position_material_triangle_multiset') is True and decoded.get('modern_material_properties_preserved') is True and decoded.get('lod_mode')=='authored-subtraction' and decoded.get('browser_accepted') is False,'Actual decoder scope differs')
 source=actual(request['source_freeze']).parent;frozen=source_files(source);photos=source_photos(source)
 aperture,feature_manifest=aperture_review(target,source)
 need(docs['source_delivery_whitelist'].get('files')==frozen and docs['source_delivery_whitelist'].get('source_freeze')==request['source_freeze'] and docs['source_delivery_whitelist'].get('private_reference_pixels_included') is False,'Public final source whitelist differs')
 need(photos==package['provenance']['source_photos'],'Actual public reference provenance differs')
 for role,asset in package['registration_assets'].items():
  actual(asset);need(identity(asset)==identity(package['assets'][role]),'Actual packaged asset differs')
  if role!='native':need(identity(asset)==identity(decoded['assets'][role]),'Actual decoded asset differs')
 old,contracts,report_adapters,reused=contract_modules()
 inputs=contracts.Inputs();request['source_roles']={'calibration':descriptor(source/'calibration.json')}
 for row in reused['files']:inputs.file(row)
 checked_package,checked_photos=contracts.package_and_photos(request,target,inputs)
 need(checked_package==package and checked_photos==photos,'Full generic package/photo contract differs')
 report_adapters.validate_independent_raw(request,target,package,inputs);suite=report_adapters.validate_finite_decoded(decoded,request,target,package,inputs)
 need(metadata.get('schema')=='sihang-warehouse-model-v12' and metadata.get('id')==ID and metadata.get('height_estimate_m')==27.7 and metadata.get('height_is_project_nominal_not_surveyed') is True and identity(metadata.get('raw'))==identity(package['assets']['raw']),'Actual authored model metadata differs')
 need(native.get('schema')=='sihang-warehouse-native-render-v12' and native.get('source_glb_sha256')==package['assets']['raw']['sha256'] and identity(native.get('native'))==identity(package['assets']['native']),'Actual native render/current model differs')
 need(native.get('source_freeze_sha256')==request['source_freeze']['sha256'] and native.get('builder_sha256')==meta(source/'build_model.py')['sha256'] and native.get('renderer_sha256')==meta(source/'render_previews.py')['sha256'] and native.get('calibration_sha256')==meta(source/'calibration.json')['sha256'],'Native final source dependency differs')
 need(native.get('model_images')==0 and native.get('ground_base_m')==0 and native.get('human_visual_review_passed') is False and native.get('browser_passed') is False,'Author native report scope differs')
 native_bounds=contracts.bounds(native.get('bounds_enu_m'));decoded_bounds=contracts.bounds(decoded['assets']['raw'].get('bounds_enu_m'))
 need(all(abs(native_bounds[i][j]-decoded_bounds[i][j])<=.0001 for i in (0,1) for j in range(3)) and abs(native_bounds[0][2])<=.0001 and abs(native_bounds[1][2]-27.7)<=.0001,'Native actual bounds/ground differ from decoded authored model')
 need(visual.get('schema')=='sihang-root-native-visual-v12' and visual.get('passed') is True and visual.get('final') is True and visual.get('actually_viewed') is True and visual.get('reviewer')=='root' and visual.get('browser_accepted') is False,'Root actual final native review pending')
 need(identity(visual.get('raw'))==identity(package['assets']['raw']) and identity(visual.get('native'))==identity(package['assets']['native']) and visual.get('native_report_sha256')==request['native_report']['sha256'],'Root reviewed different model/native evidence')
 images=visual.get('actually_viewed_images',[]);need(len(images)==3 and {i.get('role') for i in images}=={'full','detail','rear'},'Root must actually view all three native roles')
 native_images={i['role']:i for i in native['images']};need(len(native['images'])==3 and len({i['sha256'] for i in native['images']})==3 and set(native_images)=={'full','detail','rear'},'Native report requires exactly three distinct views')
 public=list(frozen);prefix='source/precise/'+ID+'/delivery/'
 def add(name,desc,kind):actual(desc);public.append({**desc,'file':name,'kind':kind})
 add(prefix+'evidence/all-aperture-occluders.json',aperture,'actual-aperture-evidence');add(prefix+'evidence/raw-feature-manifest.json',feature_manifest,'actual-feature-manifest')
 for image in images:
  need(image.get('actually_viewed') is True and Path(image['file']).name==image['file'] and identity(image)==identity(native_images[image['role']]),'Root/native image differs')
  viewed=image.get('source') or str(actual(request['root_native_review']).parent/image['file']);actual({'source':viewed,**identity(image)})
  original=native_images[image['role']];rendered=original.get('source') or str(actual(request['native_report']).parent/original['file'])
  with Path(rendered).open('rb') as stream:need(stream.read(8)==b'\x89PNG\r\n\x1a\n','Actual native preview is not a PNG')
  add(prefix+'previews/'+Path(original['file']).name,{'source':rendered,**identity(original)},'actual-native-preview')
 need(visual.get('scope') and isinstance(visual.get('limitations'),list) and visual['limitations'],'Root review scope/limitations required')
 for asset in package['registration_assets'].values():add(asset['file'],asset,'model-asset')
 for photo in photos:add(photo['image']['file'],photo['image'],'licensed-reference')
 for key in required:
  if key not in ('source_geometry','source_freeze','source_delivery_whitelist'):add(prefix+'evidence/'+key+'.json',request[key],'actual-evidence')
 add(prefix+'public-author-source-whitelist.json',request['source_delivery_whitelist'],'public-whitelist')
 add(prefix+'evidence/finite-suite.json',decoded['finite_actual_decoded_report'],'actual-evidence')
 add(prefix+'evidence/raw-structure.json',target['actual']['source_structure_report'],'actual-evidence')
 add(prefix+'evidence/finite-requests.json',target['actual']['probe_set'],'actual-evidence')
 for role,item in suite['roles'].items():
  for key in ('finite_report','array_manifest','chunk_retention'):add(prefix+'evidence/decoded-'+role+'-'+key+'.json',item[key],'actual-decoded-evidence')
 for key in ('raw_geometry','authored_lod_geometry'):add(prefix+'evidence/'+key+'.json',target['actual'][key],'author-geometry-sidecar')
 for item in request.get('public_evidence_files',[]):
  need(item['file'].startswith('source/precise/'+ID+'/') and Path(item['file']).suffix in ('.json','.py','.mjs','.js','.md','.txt'),'Additional model evidence must be explicit public text/code')
  public_text_source(item)
  add(item['file'],item,'explicit-public-evidence')
 add(prefix+'model-only-request.json',descriptor(request_path),'actual-delivery-request')
 names=[r['file'].casefold() for r in public];need(len(names)==len(set(names)),'Model-only destinations collide')
 project=Path('/workspace/shanghai_project')
 for row in public:
  contracts.safe_relative(row['file'])
  need(row['file'].startswith(('source/precise/'+ID+'/', 'assets/models/precise/'+MACRO+'/'+ID+'/', 'assets/native/precise/'+MACRO+'/'+ID+'/', 'assets/references/precise/'+ID+'/')),'Model-only delivery escaped new model namespaces')
  dest=project/row['file'];need(not dest.exists() and not dest.is_symlink(),'Model-only destination is no longer new: '+row['file']);need(all(not p.is_symlink() for p in dest.parents),'Model-only destination parent is linked')
  row['old_main']=None
 inputs.recheck();out.mkdir()
 manifest=write(out/'model-source-delivery-manifest.json',{'schema':'sihang-reviewed-model-only-manifest-v12','building_id':ID,'files':public,'file_count':len(public),'all_destinations_new':True,'actual_decoded_geometry_passed':True,'actual_root_native_review_passed':True,'browser_accepted':False,'navigation_registered':False,'main_written':False,'private_reference_pixels_included':False})
 plan_rows=public+[{'file':prefix+'model-source-delivery-manifest.json',**manifest,'old_main':None,'kind':'model-delivery-manifest'}]
 need(not (project/plan_rows[-1]['file']).exists() and not (project/plan_rows[-1]['file']).is_symlink(),'Manifest destination already exists')
 plan=write(out/'model-delivery.install-plan.json',{'schema':'sihang-reviewed-model-only-install-plan-v12','building_id':ID,'status':'ACTUAL_MODEL_AND_NATIVE_REVIEW_READY_FOR_ROOT_MODEL_BACKUP','files':plan_rows,'file_count':len(plan_rows),'all_destinations_new':True,'exclusive_per_file_bytes':100_000_000,'production_guard_project':str(project),'actual_decoded_geometry_passed':True,'actual_root_native_review_passed':True,'browser_accepted':False,'navigation_registered':False,'catalog_accepted':False,'main_written':False,'private_reference_pixels_included':False,'scope':'New editable model/source/reference/evidence backup only. No navigation, registry, catalog, HTML or runtime changes.'})
 return {'plan':plan,'manifest':manifest,'file_count':len(plan_rows),'browser_accepted':False,'main_written':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 q=sub.add_parser('package-spec');q.add_argument('--author-source',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q=sub.add_parser('registration');q.add_argument('--request',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q=sub.add_parser('model-delivery');q.add_argument('--request',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 a=p.parse_args();result=package_spec(a.author_source.resolve(),a.output) if a.command=='package-spec' else registration(a.request,a.output) if a.command=='registration' else model_delivery(a.request,a.output);print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
