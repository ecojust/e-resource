#!/usr/bin/env python3
"""Finalize only real Sihang catalog evidence; merge reviewed plans with fresh MAIN guards."""
import argparse,copy
from pathlib import Path
from prepare_sihang import HERE,BASE_APP,runtime_delta,ID,MACRO,PUBLIC,Plan,context,read,meta,encoded,need,verify,referenced,module,validate_captured_screenshots,validate_catalog_extension,check_runtime_binding,load_model_inputs
from qa_evidence import check_capture_evidence,evidence_record

def finalize(a):
    lock,oldnav,_,_,ordinary,districts=context(a.project)
    static=read(a.static_plan);accepted=read(a.accepted_plan)
    need(static['schema']=='sihang-candidate30-plan-v1' and accepted['schema']=='sihang-accepted-delta-plan-v1','Wrong parent plan schemas')
    need(static['baseline_lock']==meta(BASE_APP/'inputs.lock.json'),'Wrong baseline lock')
    need(static['qa_tools_lock']==meta(HERE/'qa-tools.lock.json'),'Static QA lock differs')
    need(accepted.get('qa_evidence')==evidence_record(lock,a.osm_evidence,ID,catalog=True),'Accepted/final QA tool/fixture binding differs')
    need(accepted['parent_candidate_plan']=={'source':str(a.static_plan.resolve()),**meta(a.static_plan)},'Accepted plan does not descend from supplied static plan')
    merged={}
    for plan in (static,accepted):
        for row in plan['files']:verify(row['source'],row);merged[row['file']]=row
    for row in merged.values():verify(a.candidate/row['file'],row)
    runtime_delta.check_candidate(a.candidate)
    need(static.get('runtime_delta')==accepted.get('runtime_delta')==runtime_delta.evidence_record(),'Parent plans runtime evidence differs')
    nav=read(a.candidate/'data/landmarks.json');registry=read(a.candidate/'data/precise-buildings-v6.json')
    catalog=read(a.candidate/'data/precise-buildings/catalog.json');entry=next(e for e in catalog['macros'] if e['id']==MACRO)
    validate_catalog_extension(catalog,a.project)
    index=read(verify(a.candidate/entry['file'],entry));replacement=index['replacement_registry'];inner=read(verify(a.candidate/replacement['file'],replacement))
    need(nav[:-1]==oldnav and len(nav)==30 and nav[-1]['id']==ID and nav[-1]['catalog_lifecycle_browser_passed'] is False,'Expected accepted30 with only Sihang lifecycle pending')
    row=nav[-1];need(index['models']==[row],'Static and index Sihang records already differ')
    ordinary.record_contract(row,districts);ordinary.bind(row,registry)
    contracts=module(lock['tools']['catalog_expectations'],'final_sihang_catalog_contract');contract=contracts.macro_contract(nav,registry,index,inner,ID)
    inputs=read(a.inputs);browser=read(a.browser);visual=read(a.visual)
    runtime_delta.check_visual(visual)
    binding=load_model_inputs(referenced(static['sihang_input_binding']['model_inputs']),{ID:row},a.candidate)
    need(binding==static['sihang_input_binding']==accepted.get('sihang_input_binding')==inputs.get('sihang_input_binding')==browser.get('sihang_input_binding'),'Actual catalog model/native/source input binding differs')
    need(inputs.get('runtime_baseline_sha256')==browser.get('runtime_baseline_sha256')==binding['runtime_baseline']['sha256'] and browser.get('actual_runtime_file_audit')=={'passed':True,'files':check_runtime_binding(binding['runtime_baseline'])['files']},'Actual catalog served31 runtime proof differs')
    need(inputs['schema']=='ordinary-macro-browser-inputs-v1' and inputs['primary_target']==ID and browser['schema']=='ordinary-macro-catalog-browser-v7','Wrong actual Sihang input/report schema')
    need(browser.get('passed') is True and browser.get('technical_passed') is True and browser.get('finished_utc') and browser.get('single_browser') is True and browser.get('sequential_pages') is True,'Actual Sihang browser incomplete')
    need(browser['inputs_sha256']==meta(a.inputs)['sha256'] and browser.get('targets')==[ID] and browser.get('records')=={ID:row},'Actual Sihang record/input binding differs')
    for field,key in [('script_sha256','catalog_runner'),('probe_sha256','catalog_base_probe'),('extension_sha256','catalog_extension_probe')]:
        relative={'catalog_runner':'catalog/browser-catalog.py','catalog_base_probe':'catalog/catalog-base-probe.js','catalog_extension_probe':'catalog/catalog-extension-probe.js'}[key]
        referenced(lock['tools'][key]);need(browser[field]==lock['tools'][key]['sha256'],'Actual frozen/reviewed catalog tool differs')
    check_capture_evidence(lock,browser,ID,a.osm_evidence,catalog=True)
    validate_captured_screenshots(browser,a.browser,5)
    for key,value in contract.items():need(browser['contract'][key]==value and inputs['contract'][key]==value,'Actual whole-macro contract differs: '+key)
    paths={'registry':'data/precise-buildings-v6.json','navigation':'data/landmarks.json','districts':'data/districts.json','catalog':'data/precise-buildings/catalog.json','index':entry['file'],'replacement':replacement['file']}
    for key,path in paths.items():
        actual=meta(a.candidate/path)
        need({k:browser['metadata'][key][k] for k in ('bytes','sha256')}==actual and {k:inputs['metadata'][key][k] for k in ('bytes','sha256')}==actual,'Actual signed metadata differs: '+key)
    need(browser.get('page_errors')==[] and browser.get('shader_errors')==[] and browser.get('http_errors')==[],'Actual browser errors')
    phases=browser['phases'];need([p['name'] for p in phases]==['static_adoption','dynamic_only','dynamic_hash_failure'] and all(p['passed'] is True and p['target_ids']==[ID] for p in phases),'Actual three phases missing')
    for key in ('single_records_reused','warm_reset_same_object_no_new_model_request','unload_static_records_retained','owner_restored'):need(phases[0][key] is True,'Static adoption failed: '+key)
    for key in ('runtime_records_added','records_removed_on_unload','returned_new_objects','owner_restored'):need(phases[1][key] is True,'Dynamic lifecycle failed: '+key)
    resource=phases[1]['geometry_disposal_by_target'][ID];need(resource['detached'] is True and resource['geometryCount']>0 and resource['geometriesDisposed']==resource['geometryCount'],'Actual dynamic geometries not disposed')
    need([p['static_navigation_count'] for p in phases]==[30,29,29] and phases[2]['precise_model_requests']==0 and phases[2]['no_new_records_or_registry'] is True,'Corrupt-index recovery differs')
    wanted={n['near_id']:n['baseline_ids'] for n in contract['near_contracts'].values()}
    need(phases[2]['baseline_complete_owner_ids_by_near']==wanted,'Corrupt-index baseline owners incomplete')
    images=['static-'+ID+'-loaded.png','static-'+ID+'-returned.png','dynamic-'+ID+'-loaded.png','dynamic-'+ID+'-returned.png','dynamic-'+ID+'-index-hash-rejected-baseline-visible.png']
    need([c['image'] for c in browser['captures'] if c.get('image')]==images,'Actual Sihang five screenshot sequence differs')
    for capture in browser['captures']:need(capture['audit']['passed'] is True and capture['audit']['errors']==[],'Actual capture owner check failed')
    need(visual.get('passed') is True and visual.get('final') is True and visual.get('reviewer')=='root' and visual.get('macro_id')==MACRO and visual.get('target_ids')==[ID],'Final root Sihang visual review missing')
    need(visual['browser_report_sha256']==meta(a.browser)['sha256'] and visual['inputs_sha256']==meta(a.inputs)['sha256'],'Actual root report binding differs')
    viewed=visual['actually_viewed'];need(len(viewed)==5 and {v['file'] for v in viewed}==set(images),'Root must actually view all five Sihang images')
    for v in viewed:
        need(Path(v['file']).name==v['file'] and v.get('actually_viewed') is True,'Unsafe/unviewed image');verify(a.visual.parent/v['file'],v)
        need((a.browser.parent/v['file']).read_bytes()==(a.visual.parent/v['file']).read_bytes(),'Root viewed another screenshot')
    need(visual.get('scope') and isinstance(visual.get('limitations'),list),'Actual visual scope/limitations required')
    out=Plan(a.output,a.project)
    changed={'data/landmarks.json','data/precise-buildings-v6.json','data/precise-buildings/catalog.json',entry['file'],PUBLIC+'/acceptance/accepted-runtime-record.json'}
    for path,source in merged.items():
        if path not in changed:out.add(path,source=source['source'])
    proof={'schema':'sihang-catalog-lifecycle-proof-v1','building_id':ID,'passed':True,'macro_id':MACRO,'scope':visual['scope'],'limitations':visual['limitations'],'browser':meta(a.browser),'root_visual':meta(a.visual),'inputs':meta(a.inputs),'web_sha256':row['web_sha256'],'lod_sha256':row['lod_sha256'],'tested_record_state':'accepted static record with catalog_lifecycle_browser_passed=false; only evidence status/hash links are now finalized','original_runtime_lock':lock['runtime_files'],'runtime_files_unchanged':[r for r in lock['runtime_files'] if r['file']!='src/map-scene.js'],'effective_runtime_files':runtime_delta.effective_runtime()['files'],'runtime_delta':runtime_delta.evidence_record(),'qa_evidence':evidence_record(lock,a.osm_evidence,ID,catalog=True),'old_catalog_indices_unchanged':True}
    proofref=out.add(PUBLIC+'/catalog/lifecycle-proof.json',data=encoded(proof))
    row=copy.deepcopy(row);row['catalog_lifecycle_browser_passed']=True;row['catalog_lifecycle_proof']=proofref
    ordinary.record_contract(row,districts);ordinary.bind(row,registry);nav[-1]=row;index['models']=[row]
    out.add('data/landmarks.json',data=encoded(nav));out.add(PUBLIC+'/acceptance/accepted-runtime-record.json',data=encoded(row))
    newindex=out.add(entry['file'],data=encoded(index))
    for e in catalog['macros']:
        if e['id']==MACRO:e.update(newindex)
    catalog['scope']='Eleven individually accepted ordinary records in nine complete macros. Sihang actual catalog load/unload/return, bad-index fallback and root visual review are complete within the bound evidence scope; existing previous records and index/replacement bytes are unchanged.'
    newcatalog=out.add('data/precise-buildings/catalog.json',data=encoded(catalog));registry['ordinary_catalog']=newcatalog
    registry['integration_scope']='Accepted30: Sihang static and catalog lifecycle/visual proof complete within their recorded limits. Old29 records and previous complete macro/index/replacement bytes are unchanged; citywide photographic completion is not claimed.'
    out.add('data/precise-buildings-v6.json',data=encoded(registry))
    for name,source in [('browser.json',a.browser),('visual-review.json',a.visual),('inputs.json',a.inputs)]:out.add(PUBLIC+'/catalog/'+name,source=source)
    for v in viewed:out.add(PUBLIC+'/catalog/'+v['file'],source=a.visual.parent/v['file'])
    need(nav[:-1]==oldnav,'Existing29 records changed during finalize')
    contracts.macro_contract(nav,registry,index,inner,ID);context(a.project)
    return out.finish({'schema':'sihang-complete-production-install-plan-v1','status':'actual_static_and_Sihang_catalog_passed_ready_for_root_review','parent_static_plan':{'source':str(a.static_plan.resolve()),**meta(a.static_plan)},'parent_accepted_plan':{'source':str(a.accepted_plan.resolve()),**meta(a.accepted_plan)},'production_guard_project':str(a.project.resolve()),'old_main_policy':'Every merged file was re-guarded against current actual MAIN, never an intermediate candidate. Installation is root-only; this tool did not install.','navigation_count':30,'ordinary_records':11,'catalog_macros':9,'catalog_lifecycle_browser_passed':True,'zip_browser_passed':False,'old29_and_catalog_exact':True,'sihang_input_binding':binding,'qa_evidence':evidence_record(lock,a.osm_evidence,ID,catalog=True)})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('project','candidate','static-plan','accepted-plan','browser','visual','inputs','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--osm-evidence',type=Path,required=True,help='The actual single-target fixture used by the catalog browser, from the same evidence SET as static acceptance')
    finalize(p.parse_args())
if __name__=='__main__':main()
