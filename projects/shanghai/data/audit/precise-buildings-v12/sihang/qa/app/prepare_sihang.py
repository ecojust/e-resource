#!/usr/bin/env python3
"""Isolated one-building composition; no installer, browser, model generation or acceptance shortcuts."""
import argparse, copy, hashlib, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
INTEGRATION=HERE.parent.parent
BASE_APP=INTEGRATION/'app-v1'
sys.path.insert(0,str(HERE.parent))
sys.path.insert(0,str(HERE.parent/'qa'))
import runtime_delta
from qa_evidence import check_capture_evidence,evidence_record,add_qa_files
from sihang_inputs import load_model_inputs,validate_profile_binding,check_runtime_binding,validate_registry as validate_sihang_registry
ID='jingan-sihang-warehouse'; MACRO='14-13720-6693'; PUBLIC='data/audit/precise-buildings-v12/sihang'
LIMIT=100_000_000

def need(ok,message):
    if not ok: raise ValueError(message)
def read(p): return json.loads(Path(p).read_bytes())
def encoded(d): return (json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def meta(p):
    b=Path(p).read_bytes(); return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def verify(p,d):
    need(meta(p)=={k:d[k] for k in ('bytes','sha256')},'File byte/SHA mismatch: '+str(p)); return Path(p)
def referenced(d): return verify(Path(d['source']),d)
def module(d,name):
    p=referenced(d);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);verify(p,d);return m

def context(project):
    lock=read(BASE_APP/'inputs.lock.json'); project=project.resolve()
    baseline=read(INTEGRATION/'minimal-tools-v1/baseline-lock.json')
    need(lock['files']==baseline['files'] and lock['runtime_files']==baseline['runtime_files'] and len(lock['runtime_files'])==31,'Current frozen MAIN files/31 runtime files required')
    qa_lock=read(HERE/'qa-tools.lock.json');need(not(set(qa_lock['tools'])&set(lock['tools'])),'QA lock cannot replace original production contracts')
    for d in list(qa_lock['tools'].values())+qa_lock.get('observation_files',[]):referenced(d)
    lock['qa_observation_files']=qa_lock.get('observation_files',[])
    lock['tools'].update(qa_lock['tools']);lock['qa_tools_lock']={'source':str(HERE/'qa-tools.lock.json'),**meta(HERE/'qa-tools.lock.json')}
    for f in lock['files']+lock['runtime_files']:verify(project/f['file'],f)
    runtime_delta.plan_entry(project)  # Actual vendor/root proof and unchanged MAIN31 are mandatory.
    lock['runtime_delta']=runtime_delta.evidence_record()
    lock['effective_runtime_files']=runtime_delta.effective_runtime()['files']
    old=read(project/'data/precise-buildings-v6.json'); nav=read(project/'data/landmarks.json')
    need(len(nav)==len({r['id'] for r in nav})==29 and ID not in {r['id'] for r in nav},'Expected unchanged29-navigation baseline')
    need(old.get('complete') is True and len(old['landmarks'])==15 and len(old['macros'])==9 and sum(len(m['near']) for m in old['macros'])==13,'Expected exact old15-owner/9-macro/13-near baseline')
    oldcatalog=read(project/'data/precise-buildings/catalog.json')
    need(oldcatalog['record_count']==10 and oldcatalog['macro_count']==len(oldcatalog['macros'])==8 and sum(e['record_count'] for e in oldcatalog['macros'])==10,'Expected exact old10 ordinary records/8 catalog macros')
    need(MACRO not in {m['id'] for m in old['macros']} and MACRO not in {m['id'] for m in oldcatalog['macros']},'Sihang macro already exists in baseline')
    owner=lock['owner_inputs']; registry=read(referenced(owner['registry']))
    need(read(referenced(owner['geometry_report']))['pass'] is True,'Owner geometry proof failed')
    runtime=read(referenced(owner['runtime_report']));need(runtime['pass'] is True and runtime['registry_sha256']==owner['registry']['sha256'],'Owner lifecycle proof mismatch')
    need(registry['complete'] and len(registry['landmarks'])==16 and len(registry['macros'])==10 and sum(len(m['near']) for m in registry['macros'])==14,'Expected16targets/10macros/14near')
    validate_sihang_registry(registry)
    need([m for m in registry['macros'] if m['id']!=MACRO]==old['macros'],'Existing complete macro geometry changed')
    need([r for r in registry['landmarks'] if r['id']!=ID]==old['landmarks'],'Existing precise boundaries changed')
    need(registry['baseline_configuration_sha256']==old['baseline_configuration_sha256'],'Baseline configuration differs')
    for ident,g in old['geometry_inputs'].items():need(registry['geometry_inputs'][ident]==g,'Existing geometry input changed')
    registry['ordinary_catalog']=copy.deepcopy(old['ordinary_catalog'])
    registry['integration_scope']='Candidate30: existing29 navigation records and accepted previous catalog remain unchanged; Sihang static browser is pending and has no active catalog entry.'
    registry['validation']['file']='source/city/precise-overrides-v12/sihang/evidence/geometry-validation.json'
    registrar=module(lock['tools']['registrar'],'sihang_frozen_registrar')
    ordinary=module(lock['tools']['ordinary_assets'],'sihang_production_contract')
    districts={str(d['id']):d['name'] for d in read(project/'data/districts.json')['districts']}
    return lock,nav,registry,registrar,ordinary,districts

def validate_captured_screenshots(browser,report_path,expected_images):
    images=[]
    for capture in browser['captures']:
        need(capture.get('capture_completed') is True,'Incomplete actual capture: '+capture['name'])
        if not capture.get('image'):continue
        name=capture['image'];shot=capture.get('screenshot_complete') or {}
        need(isinstance(name,str) and Path(name).name==name and shot.get('file')==name,'Unsafe/mismatched completed screenshot')
        need(type(shot.get('bytes')) is int and 0<shot['bytes']<LIMIT,'Actual screenshot must be strictly below100MB')
        verify(Path(report_path).parent/name,shot);images.append(name)
    need(len(images)==len(set(images))==expected_images,'Wrong actual completed screenshot count')

def validate_catalog_extension(catalog,project):
    old=read(Path(project)/'data/precise-buildings/catalog.json')
    need(catalog['macro_count']==len(catalog['macros'])==9 and catalog['record_count']==sum(e['record_count'] for e in catalog['macros'])==11,'Expected new11 ordinary records/9 catalog macros')
    need([e for e in catalog['macros'] if e['id']!=MACRO]==old['macros'],'Existing8 catalog entries changed')

class Plan:
    def __init__(self,out,project):
        self.out=out.resolve();self.project=project.resolve();self.files={}
        need(not out.is_symlink() and self.out.is_relative_to(HERE) and self.out!=HERE and not self.out.exists(),'Output must be a NEW isolated child directory')
        self.out.mkdir();self.payload=self.out/'payload'
    def add(self,name,*,source=None,data=None):
        p=Path(name);need(not p.is_absolute() and p.as_posix()==name and '..' not in p.parts and '\\' not in name and ':' not in name and all(ord(c)>=32 and ord(c)!=127 for c in name),'Unsafe output path')
        need(name.startswith(('data/','source/','assets/')) or name=='src/map-scene.js','Unexpected destination namespace')
        if name=='src/map-scene.js':
            expected=runtime_delta.plan_entry(self.project)
            need(data is None and source is not None and Path(source).resolve()==Path(expected['source']).resolve(),'Runtime source must be the exact reviewed payload')
        if data is not None:
            source=self.payload/name;source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(data)
        source=Path(source).resolve();desc=meta(source);need(0<desc['bytes']<LIMIT,'Single-file size limit')
        target=self.project/name;old=meta(target) if target.is_file() else None
        row={'file':name,'source':str(source),**desc,'old_main':old}
        if name=='src/map-scene.js':need(row==expected,'Runtime entry differs from exact reviewed delta/old MAIN bytes')
        if name in self.files:need(self.files[name]['sha256']==desc['sha256'],'Conflicting destination '+name)
        else:self.files[name]=row
        return {'file':name,**desc}
    def manifest(self,desc):
        p=referenced(desc);doc=read(p);need(isinstance(doc.get('files'),list) and doc['files'],'Missing explicit delivery whitelist')
        for f in doc['files']:
            source=referenced(f);name=f['file']
            need(name.startswith(('source/precise/'+ID+'/', 'source/city/precise-overrides-v12/sihang/', 'assets/models/precise/'+MACRO+'/'+ID+'/', 'assets/native/precise/'+MACRO+'/'+ID+'/', 'assets/references/precise/'+ID+'/', 'assets/city-overrides-v6/'+MACRO+'/', PUBLIC+'/')),'Delivery escapes new building/source scope: '+name)
            target=self.project/name
            if target.exists():need(meta(target)==meta(source),'Delivery would overwrite a different published asset: '+name)
            self.add(name,source=source)
        return doc
    def finish(self,doc):
        runtime_rows=[r for r in self.files.values() if r['file'].startswith('src/')]
        expected_count=0 if doc['schema']=='sihang-accepted-delta-plan-v1' else 1
        need(len(runtime_rows)==expected_count,'Candidate/final must carry exactly one reviewed runtime file; accepted metadata delta carries none')
        if runtime_rows:need(runtime_rows==[runtime_delta.plan_entry(self.project)],'Plan runtime entry changed')
        doc['runtime_delta']=runtime_delta.evidence_record()
        for row in self.files.values():verify(row['source'],row)
        doc.update(files=list(self.files.values()),file_count=len(self.files),main_written=False,browser_run=False,blender_run=False)
        p=self.out/'installation-plan.json';p.write_bytes(encoded(doc));print(json.dumps({'plan':str(p),**meta(p),'status':doc['status'],'file_count':len(self.files)},indent=2));return p

def candidate(a):
    lock,nav,registry,registrar,ordinary,districts=context(a.project)
    spec=read(a.spec);need(spec.get('schema')=='sihang-app-input-v12','Unexpected input schema')
    declarations_path=referenced(spec['registration_input']);declarations=read(declarations_path)
    need(len(declarations['buildings'])==1 and declarations['buildings'][0]['id']==ID,'Only Sihang declaration permitted')
    declaration=declarations['buildings'][0]; proposal=read(referenced(spec['navigation_input']))
    need(declaration['navigation']==proposal['navigation'],'Navigation differs from explicit frozen exterior-view proposal')
    row,copies=registrar.normalize(declaration,declarations_path.parent,a.project.resolve(),districts)
    need(not row['accepted'] and row['pending_stages']==['browser_proof'],'Nine real scoped proofs required; actual browser must remain pending')
    need(row['geometry_input_sha256']==registry['geometry_inputs'][ID]['sha256'] and row['anchor']==proposal['anchor'],'Frozen geometry/anchor differs from exact owner/navigation evidence')
    package_path=referenced(spec['package']);package=read(package_path)
    need(package['building_id']==ID and package.get('packaging_passed') is True,'Final actual successful package required')
    model_meta=read(referenced(spec['model_metadata']))
    need(model_meta['id']==ID and model_meta['raw']['sha256']==row['assets']['raw']['sha256'] and model_meta['raw']['bytes']==row['assets']['raw']['bytes'],'Model metadata/raw binding differs')
    need(abs(row['height_m']-model_meta['height_estimate_m'])<0.0001 and row['height_estimated'] is True and model_meta['ground_base_m']==0,'Estimated model height/ground mismatch')
    images={}
    for role,asset in row['assets'].items():
        need(all(asset[k]==package['assets'][role][k] for k in ('file','bytes','sha256')),'Package asset differs: '+role)
        if role!='native':
            p=registrar.local(declarations_path.parent,declaration['assets'][role]['source']);doc=registrar.glb_header(p)
            images[role]=len(doc.get('images',[]));need(images[role]==0,'This source-built warehouse path expects actual zero embedded images')
    row.update(candidate_only=True,browser_passed=False,catalog_lifecycle_browser_passed=False,
      triangles=package['assets']['web']['triangles'],raw_triangles=package['assets']['raw']['triangles'],lod_triangles=package['assets']['lod']['triangles'],
      lod_switch_in_m=300,lod_switch_out_m=400,photo_texture={'mode':'none','expected_images':images,'note':'Licensed original photographs are reference-only; actual raw/web/LOD contain no embedded images.'})
    ordinary.record_contract(row,districts,candidate_only=True);ordinary.bind(row,registry)
    need(row['owner']['macro_id']==MACRO and row['owner']['feature_local_id']==650 and set(row['owner']['preserve_neighbor_local_ids'])=={155,509,1640,2379,2743},'Sihang exact owner/5neighbor contract differs')
    model_inputs=referenced(spec['model_inputs'])
    model_binding=load_model_inputs(model_inputs,{ID:row})  # MAIN is the separately verified original baseline; profile checks the effective candidate31.
    for key in ('registration_input','package','model_metadata','navigation_input'):
        need(model_binding['models'][ID][key]==spec[key],'App spec differs from actual model input declaration: '+key)
    need(model_binding['osm_evidence_set']==lock['osm_evidence_set'],'Actual model source evidence differs from app lock')
    out=Plan(a.output,a.project);out.manifest(lock['owner_inputs']['source_manifest'])
    runtime_delta.add_files(out,PUBLIC)
    need(spec.get('model_source_delivery_manifest'),'Final source-delivery manifest is required before composition')
    out.manifest(spec['model_source_delivery_manifest'])
    for f in copies:out.add(f['file'],source=referenced(f))
    for f in spec.get('public_evidence_files',[]):
        need(f['file'].startswith(PUBLIC+'/'),'Evidence outside Sihang audit scope');out.add(f['file'],source=referenced(f))
    out.add('data/landmarks.json',data=encoded(nav+[row]));out.add('data/precise-buildings-v6.json',data=encoded(registry))
    out.add('data/precise-candidates/'+ID+'.json',data=encoded(row))
    out.add(PUBLIC+'/navigation-proposal.json',source=referenced(spec['navigation_input']))
    # Exact prior catalog/index/replacement bytes remain dependencies; no old macro files enter this plan.
    context(a.project)
    return out.finish({'schema':'sihang-candidate30-plan-v1','status':'prepared_static_browser_pending','spec':{'source':str(a.spec.resolve()),**meta(a.spec)},'baseline_lock':meta(BASE_APP/'inputs.lock.json'),'qa_tools_lock':meta(HERE/'qa-tools.lock.json'),'navigation_count':30,'registry_targets':16,'registry_near':14,'registry_macros':10,'ordinary_catalog':'unchanged accepted10 records/8 macros; Sihang not in catalog','pending_buildings':[ID],'existing_29_records_exact':True,'old_catalog_byte_dependencies':[f for f in lock['files'] if f['file'].startswith('data/precise-buildings/')],'sihang_input_binding':model_binding,'model_acceptance_claimed':False})

def browser_gate(a,plan,nav,registry):
    profile=read(a.expectations);browser=read(a.browser);visual=read(a.visual)
    lock,*_=context(a.project); expect=module(lock['tools']['browser_expectations'],'sihang_browser_contract')
    need(browser.get('passed') is True and browser.get('technical_passed') is True and browser.get('finished_at'),'Actual browser incomplete')
    binding=validate_profile_binding(profile)
    need(binding==plan['sihang_input_binding']==browser.get('sihang_input_binding'),'Actual static model/native/source binding differs')
    need(plan.get('runtime_delta')==runtime_delta.evidence_record(),'Static plan runtime evidence changed')
    runtime_delta.check_visual(visual)
    need(browser.get('runtime_baseline_sha256')==binding['runtime_baseline']['sha256'] and browser.get('actual_runtime_file_audit')=={'passed':True,'files':check_runtime_binding(binding['runtime_baseline'])['files']},'Actual served31 runtime file proof differs')
    check_capture_evidence(lock,browser,ID,a.osm_evidence)
    validate_captured_screenshots(browser,a.browser,7)
    need(browser.get('script_sha256')==lock['tools']['browser_runner']['sha256'] and browser.get('expectations_sha256')==meta(a.expectations)['sha256'] and browser.get('expectations')==profile,'Frozen runner/profile binding differs')
    need(browser.get('targets')==[ID] and browser.get('expected_record_count')==30 and browser.get('reset_only') is False and browser.get('single_browser') is True,'Actual single-building full browser scope differs')
    row=nav[-1];need(row['id']==ID and browser.get('records')=={ID:row},'Tested actual record differs')
    expect.validate_record(row,profile['targets'][ID]);expect.validate_registry(registry,meta(a.candidate/'data/precise-buildings-v6.json')['sha256'],profile,[ID])
    for name in ('page_errors','shader_errors','asset_errors','request_failures','console_errors','external_http_errors'):need(browser.get(name)==[],'Actual browser errors: '+name)
    need(browser.get('webgl_context_losses')==0,'Context loss occurred')
    for key,file in [('landmarks','data/landmarks.json'),('registry','data/precise-buildings-v6.json')]:need({k:browser['metadata'][key][k] for k in ('bytes','sha256')}==meta(a.candidate/file),'Tested metadata differs')
    names=[ID+s for s in ('-walk-full','-windows-oblique','-distant-lod','-returned-full')]+['precise-owners-released','precise-owners-returned','after-city-manifest-reset']
    need([c['name'] for c in browser['captures']]==names,'Actual seven capture sequence missing')
    for c in browser['captures']:need(c['audit']['passed'] is True and c['audit']['errors']==[],'Actual owner audit failed')
    need(browser['captures'][4]['audit']['activePrecise']==[] and browser['captures'][-1]['audit']['heldReleased'] is True,'Actual release/reset proof missing')
    wanted={MACRO+':'+str(i) for i in row['owner']['preserve_neighbor_local_ids']}
    need(browser['neighbors']['passed'] is True and set(browser['neighbors']['expected'])==wanted and wanted.issubset(browser['neighbors']['observed']),'Five retained neighbors not observed')
    audits=browser['asset_audits'];need(len(audits)==2 and {x['variant'] for x in audits}=={'full','distant'},'Two actual web/LOD audits required')
    for audit in audits:
        role='web' if audit['variant']=='full' else 'lod';need(audit['id']==ID and audit['passed'] is True and audit['sha256']==row[role+'_sha256'] and audit['bytes']==row[role+'_bytes'] and audit['triangles']==row['triangles' if role=='web' else 'lod_triangles'] and audit['images']==[] and audit['externalResources'] is False,'Actual decoded model differs')
    need(visual.get('passed') is True and visual.get('final') is True and visual.get('reviewer')=='root' and visual.get('building_ids')==[ID],'Actual root final single-building visual review required')
    need(visual.get('browser_report_sha256')==meta(a.browser)['sha256'] and visual.get('expectations_sha256')==meta(a.expectations)['sha256'] and visual.get('web_sha256_by_id')=={ID:row['web_sha256']},'Root visual binding differs')
    viewed=visual.get('actually_viewed',[]);need(len(viewed)==7 and {v['file'] for v in viewed}=={c['image'] for c in browser['captures']},'Root must actually review all seven images')
    for v in viewed:
        need(Path(v['file']).name==v['file'] and v.get('actually_viewed') is True,'Unsafe/unviewed root image');verify(a.visual.parent/v['file'],v)
        need((a.browser.parent/v['file']).read_bytes()==(a.visual.parent/v['file']).read_bytes(),'Root viewed another screenshot')
    need(isinstance(visual.get('limitations'),list) and visual.get('scope'),'Visual scope and limitations required')
    return row,browser,visual

def accepted(a):
    lock,oldnav,_,registrar,ordinary,districts=context(a.project)
    plan=read(a.candidate_plan);need(plan['schema']=='sihang-candidate30-plan-v1' and plan['status']=='prepared_static_browser_pending' and plan['baseline_lock']==meta(BASE_APP/'inputs.lock.json'),'Wrong candidate plan/baseline')
    need(plan['qa_tools_lock']==meta(HERE/'qa-tools.lock.json'),'Candidate QA tool lock changed')
    for f in plan['files']:verify(f['source'],f);verify(a.candidate/f['file'],f)
    runtime_delta.check_candidate(a.candidate)
    nav=read(a.candidate/'data/landmarks.json');registry=read(a.candidate/'data/precise-buildings-v6.json');need(nav[:-1]==oldnav and len(nav)==30,'Old29 navigation changed')
    row,browser,visual=browser_gate(a,plan,nav,registry)
    out=Plan(a.output,a.candidate);add_qa_files(out,lock,a.osm_evidence,ID,PUBLIC)
    summary={'building_id':ID,'passed':True,'geometry_input_sha256':row['geometry_input_sha256'],'web_sha256':row['web_sha256'],'lod_sha256':row['lod_sha256'],'scope':visual['scope'],'limitations':visual['limitations'],'browser':meta(a.browser),'root_visual':meta(a.visual),'catalog_workflow_tested':False,'qa_evidence':evidence_record(lock,a.osm_evidence,ID)}
    desc=out.add(PUBLIC+'/acceptance/browser-proof.json',data=encoded(summary))
    row=copy.deepcopy(row);row['acceptance']['browser_proof']={'status':'passed','evidence_sha256':desc['sha256'],'evidence_bytes':desc['bytes'],'scope':summary['scope']}
    row.update(accepted=True,candidate_only=False,browser_passed=True,pending_stages=[],catalog_lifecycle_browser_passed=False)
    ordinary.record_contract(row,districts);ordinary.bind(row,registry);nav[-1]=row
    out.add('data/landmarks.json',data=encoded(nav));out.add(PUBLIC+'/acceptance/accepted-runtime-record.json',data=encoded(row))
    for name,p in [('browser.json',a.browser),('visual-review.json',a.visual),('expectations.json',a.expectations)]:out.add(PUBLIC+'/acceptance/'+name,source=p)
    for v in visual['actually_viewed']:out.add(PUBLIC+'/acceptance/'+v['file'],source=a.visual.parent/v['file'])
    inner=copy.deepcopy(registry);inner.pop('ordinary_catalog',None);inner.pop('integration_scope',None)
    inner['macros']=[m for m in registry['macros'] if m['id']==MACRO];inner['landmarks']=[m for m in registry['landmarks'] if m['id']==ID];inner['geometry_inputs']={ID:registry['geometry_inputs'][ID]}
    replacement=out.add('data/precise-buildings/macros/'+MACRO+'/replacement.json',data=encoded(inner))
    index={'schema':'precise-building-macro-v1','url_base':'project-root','macro_id':MACRO,'record_count':1,'models':[row],'replacement_registry':replacement}
    idx=out.add('data/precise-buildings/macros/'+MACRO+'/index.json',data=encoded(index))
    catalog=read(a.project/'data/precise-buildings/catalog.json');need(MACRO not in {m['id'] for m in catalog['macros']},'Sihang macro already exists')
    catalog['macros'].append({'id':MACRO,'record_count':1,'bbox':row['bbox'],**idx});catalog['macro_count']=9;catalog['record_count']=11
    validate_catalog_extension(catalog,a.project)
    catalog['scope']='Eleven individually accepted ordinary records in nine complete macros. Existing previous index/replacement bytes remain unchanged; new Sihang catalog lifecycle requires its separate actual test.'
    cat=out.add('data/precise-buildings/catalog.json',data=encoded(catalog));registry['ordinary_catalog']=cat
    registry['integration_scope']='Accepted static30: Sihang actual seven-capture/root visual proof is bound separately; new Sihang catalog lifecycle remains pending. Existing29 records and previous complete macro data remain unchanged.'
    out.add('data/precise-buildings-v6.json',data=encoded(registry))
    out.add('data/precise-buildings/by-id/'+ID+'.json',data=encoded({'schema':'precise-building-pointer-v1','id':ID,'macro_id':MACRO,'macro_index':idx['file'],'feature_local_id':650}))
    contract=module(lock['tools']['catalog_expectations'],'sihang_complete_macro_contract');checked=contract.macro_contract(nav,registry,index,inner,ID)
    need(checked['static_navigation_count']==30 and checked['dynamic_navigation_count']==29 and len(checked['preserved_neighbor_ids'])==5,'New Sihang complete macro contract differs')
    context(a.project)
    return out.finish({'schema':'sihang-accepted-delta-plan-v1','status':'prepared_actual_static_pass_catalog_lifecycle_pending','parent_candidate_plan':{'source':str(a.candidate_plan.resolve()),**meta(a.candidate_plan)},'browser':{'source':str(a.browser.resolve()),**meta(a.browser)},'visual':{'source':str(a.visual.resolve()),**meta(a.visual)},'navigation_count':30,'catalog_records':11,'catalog_macros':9,'new_catalog_macro':MACRO,'old_catalog_indices_unchanged':True,'catalog_browser_passed':False,'new_catalog_technical_contract':checked,'sihang_input_binding':plan['sihang_input_binding'],'qa_evidence':evidence_record(lock,a.osm_evidence,ID)})

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('preflight');q.add_argument('--project',type=Path,required=True)
    q=sub.add_parser('candidate')
    for key in ('project','spec','output'):q.add_argument('--'+key,type=Path,required=True)
    q=sub.add_parser('accepted')
    for key in ('project','candidate','candidate-plan','browser','visual','expectations','output'):q.add_argument('--'+key,type=Path,required=True)
    q.add_argument('--osm-evidence',type=Path,required=True,help='The actual one-target OSM evidence SET used by the static browser')
    a=p.parse_args()
    if a.command=='preflight':context(a.project);print(json.dumps({'input_contracts_valid':True,'model_or_browser_passed':False,'output_created':False}))
    elif a.command=='candidate':candidate(a)
    else:accepted(a)
if __name__=='__main__':main()
