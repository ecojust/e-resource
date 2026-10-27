"""Actual one-compound evidence binding. Missing artifacts fail closed; no decoders."""
from pathlib import Path
import hashlib,json,re
from osm_evidence_set import read_fixture_set
HERE=Path(__file__).resolve().parent
import sys
sys.path.insert(0,str(HERE.parent))
import runtime_delta
ORIGINAL_GATE={"source":"/workspace/shanghai_expansion/building-by-building-v12/integration/qa-v1/sihang_model_gate.py","bytes":7030,"sha256":"ad61ba20701a8df8d6c23f1bd8e2655ea06d0b4c12303ac6511d36ee24218044"}
IDS=['jingan-sihang-warehouse']
CONFIG={IDS[0]:{'macro':'14-13720-6693','local':650,'neighbors':[155,509,1640,2379,2743]}}
GEOMETRY_SHA='c62077a2eb0f60d781998d427fcd5306dec54c94b96a2e376efc9cf53b1dc8b4'
CONTRACT={'id':'sihang-app30-v12','target_order':IDS,'navigation_count':30,'registry_counts':[16,10,14]}
PREBROWSER={'source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','uncertainty'}
def need(ok,message):
 if not ok:raise ValueError(message)
def meta(path):
 p=Path(path)
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return {'bytes':p.stat().st_size,'sha256':h}
def identity(value):
 need(isinstance(value,dict),'Missing actual file identity')
 return {k:value[k] for k in ('bytes','sha256')}
def descriptor(path):return {'source':str(Path(path).resolve()),**meta(path)}
def actual(value):
 need(isinstance(value,dict) and isinstance(value.get('source'),str),'Actual file descriptor pending')
 p=Path(value['source']);need(p.is_absolute() and p.is_file(),'Absolute actual source file required')
 need(type(value.get('bytes')) is int and 0<value['bytes']<100_000_000 and re.fullmatch('[0-9a-f]{64}',value.get('sha256','')),'Actual file descriptor invalid')
 need(meta(p)==identity(value),'Actual descriptor bytes/SHA differ: '+str(p));return p
def read(value):return json.loads(actual(value).read_bytes())
def check_runtime_binding(value):
 inputs,_,effective=runtime_delta.load_inputs()
 need(value==inputs['effective_runtime_baseline']==json.loads((HERE/'runtime-reference.json').read_text()),'Exact reviewed one-file effective31 runtime baseline must be bound')
 doc=read(value);need(doc.get('schema')=='modern-app-immutable-runtime-baseline-v11' and doc.get('file_count')==31 and len(doc.get('files',[]))==31,'Actual31 runtime baseline required');return doc
def check_runtime_tree(project,value):
 doc=check_runtime_binding(value);project=Path(project).resolve();expected={r['file']:r for r in doc['files']}
 got={p.relative_to(project).as_posix() for p in (project/'src').rglob('*') if p.is_file()}
 need(got==set(expected),'Candidate31 runtime filename inventory differs')
 for name,row in expected.items():need(meta(project/name)==identity(row),'Candidate runtime differs: '+name)
def validate_registry(registry,targets=IDS):
 need(targets==IDS,'Sihang single-target order required')
 need(registry.get('complete') is True and len(registry['landmarks'])==16 and len(registry['macros'])==10 and sum(len(m['near']) for m in registry['macros'])==14,'Actual16-owner/10-macro/14-near registry required')
 need(registry['geometry_inputs'][IDS[0]]['sha256']==GEOMETRY_SHA,'Frozen source boundary changed')
 c=CONFIG[IDS[0]];groups=[(m,n,g) for m in registry['macros'] for n in m['near'] for g in n['groups'] if g['landmark_id']==IDS[0]]
 need(len(groups)==1,'Complete compound must have exactly one source owner')
 m,n,g=groups[0]
 need(m['id']==c['macro'] and g['local_ids']==[c['local']] and set(n['featureLocalIds'])==set([c['local']]+c['neighbors']),'Sihang owner/complete5 neighbors differ')
def load_model_inputs(path,records=None,project=None):
 need(path is not None,'Actual model/native/decoded/MVT declaration pending')
 path=Path(path);doc=json.loads(path.read_bytes())
 need(doc.get('schema')=='sihang-browser-model-inputs-v12' and doc.get('status')=='READY_FOR_PROFILE','Pending evidence cannot create browser expectations')
 need(doc.get('targets')==IDS and set(doc.get('models',{}))==set(IDS),'Exact one-compound model declaration required')
 check_runtime_binding(doc.get('runtime_baseline'))
 need(doc.get('reviewed_runtime_delta')==runtime_delta.evidence_record(),'Model input must bind actual vendor/root one-file runtime review')
 if project is not None:check_runtime_tree(project,doc['runtime_baseline'])
 _,fixtures=read_fixture_set(actual(doc.get('osm_evidence_set')),IDS)
 need(records is not None and all(isinstance(records.get(i),dict) for i in IDS),'Actual candidate records required')
 outputs={}
 for ident in IDS:
  model=doc['models'][ident]
  fields=('registration_input','package','model_metadata','navigation_input','prebrowser_summary','actual_decoded','native_render','root_native_review')
  values={k:read(model.get(k)) for k in fields}
  declaration_doc=values['registration_input'];need(len(declaration_doc.get('buildings',[]))==1 and declaration_doc['buildings'][0]['id']==ident,'Standalone Sihang declaration required')
  declaration=declaration_doc['buildings'][0];package=values['package'];metadata=values['model_metadata'];row=records[ident]
  need(package.get('building_id')==ident and package.get('packaging_passed') is True,'Actual packaging is incomplete')
  need(set(package.get('assets',{}))=={'raw','web','lod','native'},'Four actual model assets required')
  need(metadata.get('id')==ident and row.get('height_estimated') is True and row.get('height_m')==metadata.get('height_estimate_m'),'Estimated project nominal height required')
  need(row.get('geometry_input_sha256')==GEOMETRY_SHA and declaration['geometry_input']['sha256']==GEOMETRY_SHA,'Exact immutable replacement source required')
  actual(declaration['geometry_input'])
  need(declaration['navigation']==row['navigation']==values['navigation_input']['navigation'],'Actual exterior observation navigation differs')
  for role,asset in package['assets'].items():
   actual(declaration['assets'][role])
   need(identity(asset)==identity(declaration['assets'][role])==identity(row['assets'][role]),'Actual model bytes differ: '+role)
   need(asset['file']==declaration['assets'][role]['file']==row['assets'][role]['file'],'Actual model destination differs: '+role)
  need(set(declaration['acceptance'])==PREBROWSER|{'browser_proof'},'Exactly nine pre-browser stages plus browser stage required')
  for stage,item in declaration['acceptance'].items():
   if stage=='browser_proof':need(item['status']=='pending','Standalone browser remains pending until actual run');continue
   need(item['status']=='passed' and item['evidence']==model['prebrowser_summary'] and item['section']==stage,'Stage must bind actual summary: '+stage)
   section=values['prebrowser_summary'][stage]
   need(section.get('passed') is True and section.get('building_id')==ident and section.get('geometry_input_sha256')==GEOMETRY_SHA,'Actual scoped prebrowser section missing: '+stage)
  # The author/package-specific decoder/native gate is an explicit reviewed
  # dependency, never guessed from generic boolean fields or inherited models.
  gate_desc=doc.get('model_evidence_gate');gate_path=actual(gate_desc)
  need(gate_desc==ORIGINAL_GATE and gate_path.resolve()==Path(ORIGINAL_GATE['source']).resolve(),'Exact original reviewed Sihang model gate required')
  import importlib.util
  spec=importlib.util.spec_from_file_location('sihang_actual_model_gate',gate_path);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
  gate.verify_model(model,values,declaration,row)
  need(meta(gate_path)==identity(gate_desc),'Model gate changed during verification')
  outputs[ident]={k:model[k] for k in fields}
 return {'reviewed_runtime_delta':runtime_delta.evidence_record(),'model_inputs':descriptor(path),'model_evidence_gate':doc['model_evidence_gate'],'runtime_baseline':doc['runtime_baseline'],'osm_evidence_set':fixtures['set'],'osm_evidence_by_target':fixtures['targets'],'models':outputs,'browser_accepted':False,'model_evidence_only':True}
def validate_profile_binding(profile,records=None):
 need(profile.get('sihang_contract')==CONTRACT,'Missing Sihang app30 contract')
 need(profile.get('expected_record_count')==30 and list(profile.get('targets',{}))==IDS,'Sihang profile identity/count/order differs')
 binding=profile.get('sihang_input_binding') or {};source=actual(binding.get('model_inputs'))
 selected={i:profile['targets'][i].get('actual_candidate_record') for i in IDS} if records is None else records
 need(load_model_inputs(source,selected)==binding,'Actual model/native/decoder/fixture binding changed');return binding
