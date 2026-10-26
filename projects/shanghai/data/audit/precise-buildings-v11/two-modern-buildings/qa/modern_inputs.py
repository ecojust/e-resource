"""Strict metadata/provenance gates for modern app29 QA. Never a geometry decoder."""
from pathlib import Path
import hashlib,json
from modern_model_gate import actual,read,identity,verify_modern_model
from osm_evidence_set import read_fixture_set
from reviewed_tool_selection import load_selection,check_dependencies,check_model
HERE=Path(__file__).resolve().parent
IDS=['jiading-shanghai-auto-museum','minhang-baoyugang-library']
CONFIG={IDS[0]:{'macro':'14-13706-6691','local':870,'neighbors':[735,797]},IDS[1]:{'macro':'14-13718-6705','local':201,'neighbors':[35,60,299,333,375,466,947]}}
def need(ok,message):
 if not ok:raise ValueError(message)
def meta(path):
 path=Path(path)
 with path.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return {'bytes':path.stat().st_size,'sha256':h}
def descriptor(path):return {'source':str(Path(path).resolve()),**meta(path)}
def runtime_reference():return json.loads((HERE/'runtime-reference.json').read_text())
def selected_tools():return load_selection(HERE/'reviewed-modern-tools.json',IDS,actual=actual)
def selection_descriptor():return descriptor(HERE/'reviewed-modern-tools.json')
def check_integration_selection(doc,selected):
 need(doc.get('reviewed_tool_selection')==selection_descriptor(),'QA reviewed per-building selection identity differs')
 check_dependencies(doc,selected)
 integration=read(doc.get('integration_spec'));dependencies=read(doc.get('integration_dependencies'))
 need(integration.get('schema')=='two-modern-app-input-v11' and integration.get('status')=='READY_FOR_CANDIDATE','Actual ready integration spec required')
 need(dependencies.get('schema')=='two-modern-app-dependencies-v11' and dependencies.get('status')=='READY_ACTUAL_BOUND_TOOLS','Actual ready integration dependencies required')
 need(integration.get('dependencies')==doc.get('integration_dependencies'),'Integration dependency identity differs')
 check_dependencies(dependencies,selected)
 for field in ('models','runtime_baseline','osm_evidence_set'):
  need(integration.get(field)==doc.get(field),'Model inputs changed integration declaration: '+field)
 return dependencies
def check_runtime_binding(value):
 need(value==runtime_reference(),'Exact current31-file runtime baseline must be bound')
 doc=read(value)
 need(doc.get('schema')=='modern-app-immutable-runtime-baseline-v11' and doc.get('file_count')==31 and len(doc['files'])==31,'Current31-file runtime baseline required')
 return doc
def check_runtime_tree(project,value):
 doc=check_runtime_binding(value);project=Path(project).resolve()
 expected={r['file']:r for r in doc['files']}
 got={p.relative_to(project).as_posix() for p in (project/'src').rglob('*') if p.is_file()}
 need(len(expected)==31 and got==set(expected),'Candidate runtime filename inventory differs')
 for n,row in expected.items():need(meta(project/n)==identity(row),'Candidate runtime bytes differ: '+n)
def validate_registry(registry,targets=IDS):
 need(targets==IDS,'Modern static target order is fixed')
 need(registry.get('complete') is True and len(registry['landmarks'])==15 and len(registry['macros'])==9 and sum(len(m['near']) for m in registry['macros'])==13,'Actual15-owner/9-macro/13-near registry required')
 for ident in IDS:
  expected=CONFIG[ident];groups=[(m,n,g) for m in registry['macros'] for n in m['near'] for g in n['groups'] if g['landmark_id']==ident]
  need(len(groups)==1,'Unique modern source owner required')
  m,n,g=groups[0]
  need(m['id']==expected['macro'] and g['local_ids']==[expected['local']] and set(n['featureLocalIds'])==set([expected['local']]+expected['neighbors']),'Modern owner/complete neighbor identities differ')
def load_model_inputs(path,records=None,project=None):
 need(path is not None,'Actual model/native/decoded/fixture input declaration is pending')
 path=Path(path);doc=json.loads(path.read_bytes())
 need(doc.get('schema')=='modern-browser-model-inputs-v11' and doc.get('status')=='READY_FOR_PROFILE','Pending model evidence cannot create actual browser expectations')
 need(doc.get('targets')==IDS and set(doc.get('models',{}))==set(IDS),'Exact two modern model declarations required')
 check_runtime_binding(doc.get('runtime_baseline'))
 if project is not None:check_runtime_tree(project,doc['runtime_baseline'])
 fixture=actual(doc.get('osm_evidence_set'));evidence,binding=read_fixture_set(fixture,IDS)
 selected=selected_tools();check_integration_selection(doc,selected)
 if records is not None:need(set(IDS).issubset(records),'Actual candidate records missing')
 outputs={}
 for ident in IDS:
  model=doc['models'][ident]
  check_model(model,ident,selected)
  declarations=read(model.get('registration_input'));need(len(declarations.get('buildings',[]))==1 and declarations['buildings'][0]['id']==ident,'Actual standalone modern registration required')
  declaration=declarations['buildings'][0]
  metadata=read(model.get('model_metadata'));package=read(model.get('package'));nav=read(model.get('navigation_input'))
  lock=read(model.get('modern_registration_input_lock'));request=read(lock.get('request'))
  need(metadata.get('id')==ident and package.get('building_id')==ident and package.get('packaging_passed') is True,'Actual selected modern package required')
  need(set(package.get('assets',{}))=={'raw','web','lod','native'},'Four actual model assets required')
  for role in ('raw','web','lod','native'):
   need(identity(package['assets'][role])==identity(declaration['assets'][role]),'Declaration/package asset differs')
   actual(declaration['assets'][role])
  for field,key in [('actual_decoded','decoded_report'),('native_render','native_report'),('native_visual','root_native_review')]:
   need(metadata.get(field)==request.get(key),'Modern metadata/request evidence differs: '+field)
  decoded=read(request.get('decoded_report'))
  need(decoded.get('schema')=='modern-actual-decoded-package-v11' and decoded.get('passed') is True and decoded.get('browser_accepted') is False,'Actual completed decoder proof required')
  need(decoded.get('package_record_sha256')==model['package']['sha256'],'Decoded/package binding differs')
  for role in ('raw','web','lod'):need(identity(decoded['assets'][role])==identity(package['assets'][role]),'Actual decoded role differs')
  native=read(request.get('native_report'));visual=read(request.get('root_native_review'))
  need(native.get('source_glb_sha256')==package['assets']['raw']['sha256'] and identity(native.get('native'))==identity(package['assets']['native']),'Native/current model differs')
  need(visual.get('schema')=='modern-root-native-visual-v11' and visual.get('passed') is True and visual.get('final') is True and visual.get('actually_viewed') is True and visual.get('reviewer')=='root' and visual.get('browser_accepted') is False,'Actual root three-view native review required')
  need(identity(visual['raw'])==identity(package['assets']['raw']) and identity(visual['native'])==identity(package['assets']['native']) and visual['native_report_sha256']==request['native_report']['sha256'],'Root/native bytes differ')
  need(len(visual['actually_viewed_images'])==3 and {r['role'] for r in visual['actually_viewed_images']}=={'full','detail','rear'},'Three distinct native review roles required')
  for image in visual['actually_viewed_images']:
   need(Path(image['file']).name==image['file'] and image.get('actually_viewed') is True,'Unviewed/unsafe native image')
   actual({'source':str(Path(request['root_native_review']['source']).parent/image['file']),**identity(image)})
  if records is not None:
   row=records[ident]
   need(row.get('height_estimated') is True and row['height_m']==metadata['height_estimate_m'] ,'Estimated height required')
   for role in package['assets']:need(identity(row['assets'][role])==identity(package['assets'][role]) and row['assets'][role]['file']==package['assets'][role]['file'],'Candidate changed model asset')
   need(declaration['navigation']==row['navigation'],'Candidate observation pose differs from standalone input')
   verify_modern_model(model,ident,declaration,row,nav,package,metadata)
   summary=model['prebrowser_summary']
   for stage,item in declaration['acceptance'].items():
    if stage=='browser_proof':need(item['status']=='pending','Standalone browser must remain pending');continue
    need(item['evidence']==summary and item['section']==stage,'Nine stages must bind the actual modern summary')
  else:
   # A runner never accepts metadata-free declarations: it must load a generated
   # actual profile or catalogue that includes selected records.
   need(False,'Current selected records required for model evidence validation')
  outputs[ident]={'registration_input':model['registration_input'],'input_lock':model['modern_registration_input_lock'],'package':model['package'],'decoded':request['decoded_report'],'native_report':request['native_report'],'root_native_review':request['root_native_review'],'source_freeze':request['source_freeze'],'summary':model['prebrowser_summary']}
 return {'model_inputs':descriptor(path),'reviewed_tool_selection':selection_descriptor(),'modern_tool_source_freezes':selected,'integration_dependencies':doc['integration_dependencies'],'runtime_baseline':doc['runtime_baseline'],'osm_evidence_set':binding['set'],'osm_evidence_by_target':binding['targets'],'models':outputs,'browser_accepted':False,'model_evidence_only':True}
def validate_profile_binding(profile,records=None):
 need(profile.get('modern_contract')=={'id':'modern-app29-v11','target_order':IDS,'navigation_count':29,'registry_counts':[15,9,13]},'Missing modern app29 profile contract')
 need(profile.get('expected_record_count')==29 and list(profile.get('targets',{}))==IDS,'Modern profile identity/count/order differs')
 binding=profile.get('modern_input_binding') or {};source=actual(binding.get('model_inputs'))
 selected={i:profile['targets'][i].get('actual_candidate_record') for i in IDS} if records is None else records
 need(all(isinstance(selected.get(i),dict) for i in IDS),'Actual candidate record binding missing')
 actual_binding=load_model_inputs(source,selected)
 need(actual_binding==binding,'Profile actual model/native/decoder/fixture input binding changed')
 return binding
