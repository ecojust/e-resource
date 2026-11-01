"""Final lightweight exact-file/QA binding gate; no browser or geometry rerun.
Usage: repository-root output.json
"""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys, runpy
from urllib.parse import urlsplit

root, out = map(Path, sys.argv[1:3])
base='93e3cb2d0ddeba1a7db7d435bf66c2f61492326e'
prefix='projects/shanghai/'
audit_rel=prefix+'data/audit/city-museum-v1/'
audit=root/audit_rel
mid='yangpu-former-shanghai-city-museum'
def read(name): return json.loads((audit/name).read_text())
def binding(path):
    path=Path(path)
    if not path.is_absolute(): path=root/path
    try:rel=str(path.relative_to(root))
    except ValueError:rel=str(path)
    if path.exists(): data=path.read_bytes(); method='working-tree bytes'
    else: data=subprocess.check_output(['git','show',':'+rel],cwd=root); method='current index bytes for nonmaterialized original city path'
    return {'file':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'read_method':method}
def require(record,path):
    actual=binding(path)
    assert actual['sha256']==record['sha256'], (path,'SHA changed')
    if 'bytes' in record: assert actual['bytes']==record['bytes'], (path,'size changed')
    return actual

navigation=runpy.run_path(str(Path(__file__).with_name('independent-navigation-exceptions.py')))['validate_navigation'](root)
navigation_existing={r['file']for r in navigation['existing_readme_files']}
navigation_new=set(navigation['new_navigation_audit_files'])
assert not (audit/'pre-height-fix-disposition.json').exists(), 'Pre-height-fix run is not final evidence; explicitly bind the repaired run before enabling this gate'
browser=read('browser.json'); qa=read('qa-visual-review.json')
assert browser.get('stage')=='fragment-rebased-final' and browser.get('final_acceptance') is True, 'Only the fresh fragment-rebased final run can pass this gate'
root_visual=read('browser-visual-review.json'); root_native=read('native-visual-review.json')
native=read('independent-native-visual-review.json'); host=read('qa-host-completion.json')
independent=read('independent-review.json'); metadata=read('independent-metadata-review.json')
runtime=read('runtime-checks.json'); root_checks=read('root-checks.json')
assert browser['completed'] and browser['browserClosed'] and browser['modelId']==mid
raw_host_path=Path('/workspace/shanghai-city-museum-qa/fragment-rebased-final-raw-host.json')
raw_host_bytes=raw_host_path.read_bytes();raw_host=json.loads(raw_host_bytes)
raw_host_binding={'file':str(raw_host_path),'bytes':len(raw_host_bytes),'sha256':hashlib.sha256(raw_host_bytes).hexdigest(),'read_method':'actual retained raw host bytes'}
assert raw_host_binding['sha256']==browser['raw_host_report_sha256']
assert raw_host['stage']=='fragment-rebased-final' and raw_host['completed'] and raw_host['browserClosed']
assert raw_host['final_acceptance'] is False
assert 'final_acceptance_scope'not in raw_host and 'raw_host_report_sha256'not in raw_host
host_projection=dict(browser);host_projection.pop('final_acceptance_scope');host_projection.pop('raw_host_report_sha256');host_projection['final_acceptance']=False
assert host_projection==raw_host,'Final QA may only annotate actual raw host acceptance, never change captures/errors/state'

assert qa['passed'] and root_visual['passed'] and root_native['passed'] and native['passed']
assert qa.get('stage')=='fragment-rebased-final' and qa.get('final_acceptance') is True
assert independent['passed'] and metadata['passed'] and runtime['passed'] and root_checks['passed']
assert host['status'] in ['completed','completed-with-camera-recovery'] and host['browser_closed']
verification_report_inputs=[]
for record in root_checks['bindings']:
    verification_report_inputs.append({'report':'root-checks.json',**require(record,record['path'])})
for record in runtime['bindings']:
    verification_report_inputs.append({'report':'runtime-checks.json',**require(record,prefix+record['file'])})
integration=read('global-integration-checks.json')
assert integration['passed']==7
for record in integration.get('bindings',[]):
    verification_report_inputs.append({'report':'global-integration-checks.json',**require(record,prefix+record['file'])})
assert host['normal_node_exit_code_observed']==0
assert not host['active_browser_host_or_server'] and host['active_control_files_absent']
def report_binding(record):
    name=record['file']
    return require(record, name if Path(name).is_absolute() or name.startswith(prefix) else (prefix+name if '/'in name else audit_rel+name))
report_binding(qa['browser_report'])
report_binding(root_visual['browser_report'])
report_binding(host['browser_report'])
for document in [host]:
    for key in ['script','contract']:
        report_binding(document[key])
report_binding(host['qa_visual_review'])
fixture=browser['fragmentCoordinateFixture']
assert fixture['passed'] and fixture['stage']==browser['stage'] and fixture['runId']==browser['runId']
assert fixture['fixtureScript']==browser['fragmentFixtureInputs']['fixtureScript']
assert fixture['fixtureScript']['file']=='data/audit/city-museum-v1/qa-clip-gpu-fixture.cjs'
assert fixture['productionBindings']==browser['fragmentFixtureInputs']['productionBindings']
assert set(fixture['productionBindings'])=={'clipper','three'}
assert fixture['productionBindings']['clipper']['file']=='src/candidate-city-clipping.js'
assert fixture['productionBindings']['three']['file']=='vendor/three.module.js'
report_binding(fixture['fixtureScript'])
for record in fixture['productionBindings'].values():report_binding(record)
fixture_result=fixture['result']
assert fixture_result['passed'] and not fixture_result['glErrors'] and not fixture_result['shaderErrors']
assert fixture_result['mainSceneUnchanged'] is True
fixture_receipts=fixture_result['sourceReceipts']
assert len(fixture_receipts)==2
for key,query in [('clipper','v=city-height-clips-v2'),('three','')]:
    expected=fixture['productionBindings'][key]
    matching=[r for r in fixture_receipts if urlsplit(r['url']).path=='/'+expected['file']]
    assert len(matching)==1
    receipt=matching[0]
    assert receipt['status']==200 and receipt['sha256']==expected['sha256'] and receipt['bytes']==report_binding(expected)['bytes']
    assert urlsplit(receipt['url']).query==query
fixture_cases=fixture_result['cases']
assert len(fixture_cases)==4 and all(r['passed']for r in fixture_cases)
assert {r['name']for r in fixture_cases}=={'shared-material-translated-objects','instanced-depth-material','instanced-distance-material','physical-transmission-material'}
assert all(fixture_result['cleanup'][k] is True for k in ['rendererDisposed','canvasDetached','contextLostRequested'])
fixture_programs={r['id']:r for r in fixture_result['programs']}
assert len(fixture_programs)==4 and all(r['linked'] and all(s['compiled']for s in r['shaders'])for r in fixture_programs.values())
for case in fixture_cases:
    assert case['passes']
    for render_pass in case['passes']:
        samples=render_pass['samples']
        assert len(samples)==4 and [r['expected']for r in samples]==['clear','retained','retained','clear']
        assert all(r['passed'] and ((r['rgba']==[0,0,0,0])==(r['expected']=='clear'))for r in samples)
        assert render_pass['draws']
        for draw in render_pass['draws']:
            assert draw['program']in fixture_programs and draw['candidateClipCount']==4
            assert draw['modelTranslation']==draw['objectPosition']==draw['modelMatrix'][12:15]
    if case['name']=='shared-material-translated-objects':
        assert case['oneLinkedProgram'] and len(case['passes'])==2
        assert [r['rgba']for r in case['passes'][0]['samples']]==[r['rgba']for r in case['passes'][1]['samples']]
        assert len({d['program']for p in case['passes']for d in p['draws']})==1
    if case['name'].startswith('instanced-'):
        assert all(d['instanceCount']==2 for p in case['passes']for d in p['draws'])
        assert any(s['useInstancing']for p in case['passes']for d in p['draws']for s in fixture_programs[d['program']]['shaders'])
    if case['name']=='physical-transmission-material':
        assert case['transmission']>0
        assert all(any(s['useTransmission']for s in fixture_programs[d['program']]['shaders'])for p in case['passes']for d in p['draws'])
fixture_summary={'passed':True,'stage':fixture['stage'],'runId':fixture['runId'],'fixtureScript':fixture['fixtureScript'],'productionBindings':fixture['productionBindings'],'actual_cases':[{'name':r['name'],'passes':len(r['passes']),'pixel_samples':sum(len(p['samples'])for p in r['passes'])}for r in fixture_cases],'actual_linked_and_compiled_programs':4,'per_draw_object_matrix_and_clip_retain_pixels_verified':True,'mainSceneUnchanged':True,'cleanup':fixture_result['cleanup'],'raw_gpu_evidence_location':'browser.json fragmentCoordinateFixture'}
environment_review=None
# This delivery must be judged from its own retained errors, not prior-run exceptions.
# If recovery is needed, independently review and bind a new explicit recovery report.
assert not browser['errors'] and not browser['warnings'] and not browser.get('responseCheckFailures'), 'Retained errors require delivery-specific independent recovery review'
assert not [r for r in browser['http']if r.get('status',200)>=400], 'HTTP errors require explicit recovery evidence'
initial_failures=browser.get('failures',[])
failed_continuations=[row for row in browser.get('continuations',[])if row['type']=='continuation-failed']
assert not failed_continuations, 'A failed continuation requires delivery-specific resolution'
# No historical camera/error exception is inherited. A real current-run
# failure must be independently explained and this gate updated with its exact
# retained recovery evidence before it can pass.
assert not initial_failures, 'Current delivery failures require explicit independent recovery review'
assert not browser.get('roofCameraRecovery')
for row in browser.get('continuations',[]):
    if 'module'in row:
        actual=binding(row['module']);assert actual['sha256']==row['moduleSha256']==row['expectedModuleSha256']
frozen={}
def frozen_row(record,path=None):
    rel=path or prefix+record['file']
    actual=require(record,rel)
    if rel in frozen: assert frozen[rel]==actual
    frozen[rel]=actual

for key in ['catalog','manifest','footprint','qaScript','qaContract','continuationHelper','placementBinding','viewerRegistry']:
    frozen_row(browser[key])
for key in ['expectedSourceBindings','referenceDocuments','documentBindings']:
    for record in browser[key]: frozen_row(record)
for name,record in browser['sourceBindings'].items():
    frozen_row(record,prefix+'src/'+name)
contract=read('qa-contract.json')
assert contract['frozen'] and contract['model_id']==mid
assert contract['clip_capacity']==288 and contract['expected_global_clip_triangles']==262
assert contract['expected_global_planar_clip_triangles']==258 and contract['expected_display_height_triangles']==4
for record in contract['source_bindings']: frozen_row(record,record['repository_path'])
manifest=json.loads((root/prefix/('assets/models/candidates/'+mid+'/manifest.json')).read_text())
assets=[{'role':role,**require(record,prefix+'assets/models/candidates/'+mid+'/'+record['file'])}
        for role,record in manifest['assets'].items()]
assert len(assets)==4
assert root_visual['manifest_sha256']==browser['manifest']['sha256']
assert root_visual['catalog_sha256']==browser['catalog']['sha256']
root_native_assets={r['file']:r for r in root_native['assets']}
assert set(root_native_assets)=={r['file']for r in manifest['assets'].values()}
for record in root_native_assets.values(): require(record,prefix+'assets/models/candidates/'+mid+'/'+record['file'])
assert native['raw_sha256']==manifest['assets']['raw']['sha256']
assert native['native_sha256']==manifest['assets']['native']['sha256']
assert root_native['reviewer']in('root','/root') and all(r['actually_viewed_by_root']for r in root_native['images'])
for role in ['full','lod']:
    scene=browser['global'][role]
    asset=scene['asset']; assert asset['status']=='loaded' and asset['visible'] and asset['cityIntegration']
    assert asset['verifiedAsset']['sha256']==manifest['assets'][role]['sha256']
    shader=scene['candidate']['shader']
    assert shader['triangleLimit']==288 and shader['clippingTexture']['height']==288
    assert shader['clippingTexture']['bytes']==18432 and shader['triangles']<=262
    catalogue_rows=browser['clipCatalogueAudit']['rows']
    assert browser['clipCatalogueAudit']['total']==262 and browser['clipCatalogueAudit']['capacity']==288
    row_counts={r['id']:r['triangles']for r in catalogue_rows}
    assert len(row_counts)==len(catalogue_rows) and sum(row_counts.values())==262
    active_ids=[clip['id']for clip in scene['candidate']['displayClips']]
    assert len(set(active_ids))==len(active_ids) and set(active_ids)<=set(row_counts)
    active_triangles=sum(row_counts[ident]for ident in active_ids)
    assert shader['triangles']==active_triangles
    assert browser['clipCatalogueAudit']['planarTotal']==258 and browser['clipCatalogueAudit']['heightTotal']==4
    assert {c['id']for c in scene['candidate']['clips']}<set(active_ids)
beacons=browser['beacons']
assert beacons['state']['count']==81 and beacons['state']['viewportLabelCount']==81
assert beacons['allSpritesPresent'] and len(beacons['picks'])==81
assert all(row['id']==row['hit']for row in beacons['picks'])
touch=beacons['touch']; assert touch['id']==mid and touch['changedDestination'] and touch['targetAssetVisibleAfterTouch']

def root_image_accepted(record):
    if 'accepted_for_scope' in record:
        accepted=record['accepted_for_scope'];assert isinstance(accepted,bool)
    elif 'accepted_as_target_geometry_evidence' in record:
        accepted=record['accepted_as_target_geometry_evidence'];assert isinstance(accepted,bool)
    else:
        assert record.get('passed')is True,'Root image row needs an explicit acceptance or insufficiency decision'
        accepted=True
    if not accepted:assert record.get('passed')is not True
    return accepted

# Retain this gate's actual first rejection and the exact two UI-scope
# annotations that resolve it. No application, browser or geometry failure is waived.
gate_history=Path('/workspace/shanghai-city-museum-review/fragment-rebase-history')
prior_gate_attempt=json.loads((gate_history/'final-gate-attempt-1.json').read_text())
assert prior_gate_attempt['exit_code']==1 and 'root_image_accepted' in prior_gate_attempt['stderr']
prior_root_path=gate_history/'root-visual-before-scope-annotation.json'
assert binding(prior_root_path)['sha256']=='a56fd03374efa703b0a4c5a4d6f58675cbb93c374a79e1b640775f23985036d2'
prior_root=json.loads(prior_root_path.read_text())
scope_rows={'browser-beacons-320-city-81-f57de261-db52b6e7.png','browser-beacons-320x548-worst-title-81-f57de261-db52b6e7.png'}
for row in prior_root['images']:
    if row['file']in scope_rows:
        assert row['passed']is True and row['accepted_as_target_geometry_evidence']is False
        assert 'accepted_for_scope'not in row
        row['accepted_for_scope']=True
assert prior_root==root_visual,'Only the two already-viewed beacon UI scope annotations resolve the first gate rejection'
prior_gate_recovery={'first_attempt':binding(gate_history/'final-gate-attempt-1.json'),'first_attempt_script':binding(gate_history/'final-gate-source-attempt-1.py'),'root_report_before_annotation':binding(prior_root_path),'root_report_after_annotation':binding(audit/'browser-visual-review.json'),'exact_annotation_delta':{'files':sorted(scope_rows),'added_field':'accepted_for_scope','value':True},'reason':'The two accepted beacon UI images explicitly remain unsuitable as target-building geometry evidence. Adding their positive UI-scope acceptance resolves the gate classification without changing images or observations.','application_browser_or_geometry_failures_waived':False}
qa_images={r['file']:r for r in qa['images']}
root_images={r['file']:r for r in root_visual['images']}
captures={r['file']:r for r in browser['captures']}
assert set(qa_images)==set(root_images)==set(captures)
images=[]
for name,capture in captures.items():
    actual=require(capture,audit_rel+name)
    report_binding(capture['captureScript'])
    for record in [qa_images[name],root_images[name]]:
        assert record['sha256']==actual['sha256'] and record['bytes']==actual['bytes']
    assert qa_images[name]['actually_viewed']
    assert qa_images[name]['accepted']==root_image_accepted(root_images[name])
    assert root_images[name].get('actually_viewed_by_root',root_images[name].get('actually_viewed'))
    images.append({'kind':'final_browser' if qa_images[name]['accepted'] else 'retained_insufficient_process_frame','qa_and_root_actual_view_records_agree':True,**actual})
assert len([r for r in images if r['kind']=='retained_insufficient_process_frame'])==qa['insufficient_process_images_retained']
# Every required viewpoint needs a final positive pixel decision and both final
# reviewers' acceptance. Rejected process frames alone cannot satisfy a view.
required_view_acceptance=[]
assert len(contract['visual_views'])==8
for view in contract['visual_views']:
    selected=browser['global']['visualAcceptance'][view['key']]
    assert selected['accepted'] and selected['key']==view['key']
    capture=captures[selected['capture']]
    assert capture['sha256']==selected['captureSha256']
    assert capture['label']==view['label'] or capture['label'].startswith(view['label']+'-adjusted-')
    assert qa_images[capture['file']]['accepted'] and root_image_accepted(root_images[capture['file']])
    decision=selected['decision']
    assert decision['accepted'] and decision['viewKey']==view['key']
    if view.get('upper_fragment_display_height_clip_id'):
        h=decision['heightFixVerification']
        assert h['clip_id']==view['upper_fragment_display_height_clip_id']
        assert h['upper_fragment_removed'] is True and h['retained_neighbor_roof_intact'] is True
        assert qa_images[capture['file']]['height_fix_verification']==h
    assert decision['captureFile']==capture['file'] and decision['captureSha256']==capture['sha256']
    assert decision['scriptSha256']==capture['captureScript']['sha256']
    assert decision['captureControlSha256']==capture['captureScript'].get('controlSha256')
    assert decision['runGeneratedAt']==browser['generatedAt']
    control=report_binding(selected['control'])
    assert json.loads((root/control['file']).read_text())==decision
    assert any(r['key']==view['key']and r['control']['sha256']==selected['control']['sha256']for r in browser['visualPixelReviews'])
    assert browser['global']['visualViews'][view['key']]==capture['state']
    required_view_acceptance.append({'key':view['key'],'capture':capture['file'],'sha256':capture['sha256'],'qa_and_root_accepted':True,'pixel_control':control})
height_views=read('independent-browser-height-visual-review.json')
assert height_views['passed'] and height_views['stage']=='fragment-rebased-final'
assert len(height_views['images'])==2
assert {r['view_key']for r in height_views['images']}=={'retained-interface-3','retained-interface-4'}
for record in height_views['images']:
    selected=browser['global']['visualAcceptance'][record['view_key']]
    assert record['view_key'] in ['retained-interface-3','retained-interface-4']
    assert record['file']==selected['capture'] and record['sha256']==selected['captureSha256']
    require(record,audit_rel+record['file'])
    assert record['actually_viewed_by_independent_reviewer'] and record['passed']
    assert record['upper_fragment_removed'] is True and record['retained_neighbor_roof_intact'] is True
base_labels=['auxiliary-desktop-full','auxiliary-desktop-lod','auxiliary-mobile-full','global-default-desktop','global-default-mobile','beacons-320-city-81']
for label in base_labels:
    assert any((c['label']==label or c['label'].startswith(label+'-adjusted-'))and qa_images[c['file']]['accepted']and root_image_accepted(root_images[c['file']])for c in captures.values()),label
if browser['beacons'].get('worstTitleViewport'):
    height=browser['beacons']['worstTitleViewport']['scene']['viewport'][1]
    assert any(c['label'].startswith('beacons-320x')and c['state']['viewport'][1]==height and qa_images[c['file']]['accepted']and root_image_accepted(root_images[c['file']])for c in captures.values())
if browser['beacons'].get('postTouchCardComparison',{}).get('requiresAdditionalCityCapture'):
    assert any(c['label']=='beacons-320-city-museum-city-81'and qa_images[c['file']]['accepted']and root_image_accepted(root_images[c['file']])for c in captures.values())
input_rejections=browser.get('visualReviewInputErrors',[])
assert not input_rejections,'Fresh final run does not inherit the rejected height-fixed run empty-control exception'
assert not (audit/'independent-control-input-recovery.json').exists(),'The previous-run recovery belongs in its private failed-run archive'


root_native_images={r['file']:r for r in root_native['images']}
assert len(native['images'])==8 and set(root_native_images)=={r['file']for r in native['images']}
for record in native['images']:
    actual=require(record,audit_rel+record['file']); other=root_native_images[record['file']]
    assert other['sha256']==actual['sha256'] and other['bytes']==actual['bytes']
    assert record['actually_viewed'] and record['accepted_for_scope'] and other['passed'] and other['actually_viewed_by_root']
    images.append({'kind':'final_native','independent_and_root_actual_view_records_agree':True,**actual})
for record in root_checks['mapping_images_actually_viewed_by_root']:
    assert record['passed'] and record['actually_viewed_by_root']; images.append({'kind':'final_mapping','root_actual_view_record_bound':True,**require(record,audit_rel+record['file'])})
processes=subprocess.check_output(['ps','-eo','stat=,comm=,args='],text=True).splitlines()
active_browsers=[line for line in processes if not line.lstrip().startswith('Z') and len(line.split(None,2))>=2 and line.split(None,2)[1]in('chromium','chrome','google-chrome')]
assert not active_browsers,active_browsers
active_hosts=[line for line in processes if not line.lstrip().startswith('Z') and ('node projects/shanghai/data/audit/city-museum-v1/qa-browser.cjs --run' in line or 'python /workspace/shanghai-city-museum-qa/server.py' in line)]
assert not active_hosts,active_hosts
listeners=subprocess.check_output(['ss','-ltnp','sport = :8782 or sport = :9223'],text=True)
assert len(listeners.strip().splitlines())==1,listeners
assert not any((audit/n).exists()for n in ['visual-control.json','visual-review-control.json','visual-review-control.pending','continuation-control.json'])
for record in host['archived_controls']:report_binding(record)
assert host['failures']==len(initial_failures)and host['failed_continuations']==len(failed_continuations)

# Reports bind actual frozen bytes, rather than relying on the presence of a pass label.
for record in independent['reports']: require(record,audit_rel+record['file'])
require(independent['final_footprint'],audit_rel+'footprint-review.json')
require(independent['final_manifest'],prefix+'assets/models/candidates/'+mid+'/manifest.json')
for key in ['source_code_files','reference_records_unchanged_from_independent_content_review','new_public_assets']:
    for record in metadata[key]: require(record,record['file'])
for record in metadata['readme_district_and_link_checks']: require(record['binding'],record['file'])
for key in ['author_portable_rebuild_receipt','final_source_readme','final_manifest','final_catalog','final_additional_placement','final_footprint','restoration_progress']:
    require(metadata[key],metadata[key]['file'])

height=read('independent-height-clip-review.json')
assert height['passed'] and height['required_final_browser_stage']=='height-fixed-final'
assert height['clip_rows']=={'base_2d':40,'height':4,'museum_gpu':44,'all_city':262,'capacity':288}
assert height['actual_final_browser_pixels_required'] and not height['fragment_interpolation_certified']
fragment=read('independent-fragment-rebase-review.json')
assert fragment['passed'] and fragment['required_final_browser_stage']=='fragment-rebased-final'
assert fragment['prior_height_review']['sha256']==binding(audit/'independent-height-clip-review.json')['sha256']
assert fragment['gpu_rows_byte_identical'] and fragment['authored_assets_and_2d_geometry_unchanged']
assert set(fragment['changed_files'])=={prefix+n for n in ['src/candidate-city-clipping.js','tests/candidate-city-clipping.test.mjs','src/app.js','src/map-scene.js','index.html']}
for record in fragment['current_input_bindings']+fragment['diagnostic_bindings']:
    require(record,record['file'])
archives={r['recorded_file']:r['archive_binding']for r in fragment['historical_input_bindings']}
assert len(archives)==len(fragment['historical_input_bindings'])==5
assert set(archives)=={prefix+n for n in ['data/audit/city-museum-v1/height-clipping-checks.json','src/candidate-city-clipping.js','src/map-scene.js','src/app.js','index.html']}
def require_historical_input(record):
    if record['file']in archives:
        archived=archives[record['file']]
        assert archived['sha256']==record['sha256'] and archived['bytes']==record['bytes']
        return require(archived,archived['file'])
    return require(record,record['file'])
for key in ['script','final_footprint','final_contract','final_manifest','final_catalog','final_additional_placement','actual_gpu_rows','prior_placement_review']:
    require(height[key],height[key]['file'])
require_historical_input(height['final_runtime'])
for record in height['reports']:
    require(record,record['file'])
for record in height['numeric_final_input_bindings']:
    require_historical_input(record)
assert independent['final_height_fix']['sha256']==binding(audit/'independent-height-clip-review.json')['sha256']
assert independent['final_fragment_rebase']['sha256']==binding(audit/'independent-fragment-rebase-review.json')['sha256']
tracked=subprocess.check_output(['git','diff','--name-status',base,'--'],cwd=root,text=True).splitlines()
assert not any(line.startswith('D\t')for line in tracked)
old_audits=[line for line in tracked if '\t'+prefix+'data/audit/'in line and '\t'+audit_rel not in line and line.split('\t',1)[1]not in navigation_existing|navigation_new]
old_assets=[line for line in tracked if '\t'+prefix+'assets/'in line and '\t'+prefix+'assets/models/candidates/'+mid+'/'not in line]
old_sources=[line for line in tracked if '\t'+prefix+'source/'in line and '\t'+prefix+'source/precise/'+mid+'/'not in line and line.split('\t',1)[1]not in navigation_existing]
assert not old_audits and not old_assets and not old_sources
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
added={line.split('\t',1)[1]for line in tracked if line.startswith('A\t')}|{name for name in untracked if name}
for name in added:
    if name.startswith(prefix+'data/audit/'): assert name.startswith(audit_rel)or name in navigation_new,name
    if name.startswith(prefix+'assets/'): assert name.startswith(prefix+'assets/models/candidates/'+mid+'/'),name
    if name.startswith(prefix+'source/'): assert name.startswith(prefix+'source/precise/'+mid+'/'),name
status=subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=root).decode().split('\0')
assert not [line for line in status if line and 'D'in line[:2]]
self_rel=str(out.relative_to(root))
new_files=[binding(name)for name in sorted(added)if name!=self_rel]
reports={name:binding(audit/name)for name in ['browser.json','qa-visual-review.json','browser-visual-review.json','native-visual-review.json','independent-review.json','qa-host-completion.json','README.md','root-checks.json','runtime-checks.json','independent-height-clip-review.json','independent-fragment-rebase-review.json','independent-browser-height-visual-review.json']}
result={'schema':'city-museum-independent-prepublication-v1','passed':True,
        'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_commit':base,
        'scope':'Final lightweight exact-file inventory, QA input/capture binding and previous completed independent-review binding. No browser, model reconstruction, native reopen, occupancy rerun or historical mesh matrix.',
        'final_reports':reports,'all_qa_frozen_inputs_match_current_bytes':True,
        'frozen_inputs':list(frozen.values()),'verification_report_input_bindings':verification_report_inputs,'final_four_assets':assets,'final_images':images,'required_view_acceptance':required_view_acceptance,'required_base_capture_labels':base_labels,
        'browser_saved_image_count':len(captures),'browser_final_accepted_image_count':sum(r['accepted'] for r in qa_images.values()),
        'insufficient_process_images_retained':qa['insufficient_process_images_retained'],'native_final_image_count':len(native['images']),
        'mapping_final_image_count':len(root_checks['mapping_images_actually_viewed_by_root']),
        'image_review_scope':'Browser images were actually reviewed by QA and root; the final northern interface3/4 images additionally by the independent reviewer; native images by reviewer and root. This final pass checks exact image-byte bindings without claiming another image view.',
        'fragment_gpu_fixture':fixture_summary,'raw_host_report':raw_host_binding,'final_browser_annotation_delta_only':['final_acceptance','final_acceptance_scope','raw_host_report_sha256'],'browser_closed_and_normal_host_exit_recorded':True,'independent_current_process_and_listener_check':{'active_browsers':active_browsers,'active_host_or_server':active_hosts,'listener_ports_checked':[8782,9223],'listeners_raw':listeners},
        'no_unresolved_application_errors':True,'environment_recovery_and_observer_limitations':environment_review,'current_delivery_recovery':environment_review,'visual_review_input_rejection_count':len(input_rejections),
        'retained_current_failures':initial_failures,'prior_gate_attempt_recovery':prior_gate_recovery,
        'actual_browser_gpu_triangle_limit':288,'catalog_mask_triangles':262,'planar_mask_triangles':258,'height_clip_triangles':4,'museum_gpu_triangles':44,'height_fix_actual_northern_image_review':binding(audit/'independent-browser-height-visual-review.json'),'fragment_rebase_review':binding(audit/'independent-fragment-rebase-review.json'),
        'beacons_81_visible_and_independently_pickable':True,
        'actual_native_touch_changed_destination_and_showed_target':True,
        'global_models':81,'yangpu_models':6,'new_file_count_excluding_this_self_report':len(new_files),
        'new_files':new_files,'self_report_path':self_rel,'self_digest_omitted_to_avoid_recursion':True,
        'tracked_diff':tracked,'no_deletions':True,'no_unapproved_old_audit_or_model_asset_changes':True,'approved_navigation_repair':{'receipt':binding(audit/'independent-navigation-review.json'),'existing_files':64,'new_files':sorted(navigation_new),'exact_sha_and_baseline_replay':True},
        'old_record_preservation_evidence':binding(audit/'independent-metadata-review.json'),
        'limits':'Publication HTTP bytes and any files added after this gate require the separate publication record. Source/geometry uncertainty and exterior-only scope remain unchanged.'}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'frozen_inputs':len(frozen),'browser_images':len(captures),'new_files':len(new_files)}))
