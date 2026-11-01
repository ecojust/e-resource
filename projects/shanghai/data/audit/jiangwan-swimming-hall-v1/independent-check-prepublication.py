"""Final lightweight exact-file/QA binding gate; no browser or geometry rerun.
Usage: repository-root output.json
"""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys

root, out = map(Path, sys.argv[1:3])
base='225af1b75c235177ca23c775b9a9d3483eb032ba'
prefix='projects/shanghai/'
audit_rel=prefix+'data/audit/jiangwan-swimming-hall-v1/'
audit=root/audit_rel
mid='yangpu-jiangwan-swimming-hall'
def read(name): return json.loads((audit/name).read_text())
def binding(path):
    path=Path(path)
    if not path.is_absolute(): path=root/path
    rel=str(path.relative_to(root))
    if path.exists(): data=path.read_bytes(); method='working-tree bytes'
    else: data=subprocess.check_output(['git','show',':'+rel],cwd=root); method='current index bytes for nonmaterialized original city path'
    return {'file':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'read_method':method}
def require(record,path):
    actual=binding(path)
    assert actual['sha256']==record['sha256'], (path,'SHA changed')
    if 'bytes' in record: assert actual['bytes']==record['bytes'], (path,'size changed')
    return actual

browser=read('browser.json'); qa=read('qa-visual-review.json')
root_visual=read('browser-visual-review.json'); root_native=read('native-visual-review.json')
native=read('independent-native-visual-review.json'); host=read('qa-host-completion.json')
independent=read('independent-review.json'); metadata=read('independent-metadata-review.json')
runtime=read('runtime-checks.json'); root_checks=read('root-checks.json')
assert browser['completed'] and browser['browserClosed'] and browser['modelId']==mid
assert qa['passed'] and root_visual['passed'] and root_native['passed']
assert independent['passed'] and metadata['passed'] and runtime['passed'] and root_checks['passed']
assert host['status'] in ['completed','completed-with-camera-recovery'] and host['browser_closed']
assert host['normal_node_exit_code_observed']==0
assert not host['active_browser_host_or_server'] and host['active_control_files_absent']
def report_binding(record):
    name=record['file']
    return require(record, name if name.startswith(prefix) else (prefix+name if '/'in name else audit_rel+name))
report_binding(qa['browser_report'])
report_binding(root_visual['browser_report'])
report_binding(host['browser_report'])
for document in [host]:
    for key in ['script','contract']:
        report_binding(document[key])
report_binding(host['qa_visual_review'])
environment_review=None
# This delivery must be judged from its own retained errors, not prior-run exceptions.
# If recovery is needed, independently review and bind a new explicit recovery report.
assert not browser['errors'] and not browser['warnings'] and not browser.get('responseCheckFailures'), 'Retained errors require delivery-specific independent recovery review'
assert not [r for r in browser['http']if r.get('status',200)>=400], 'HTTP errors require explicit recovery evidence'
initial_failures=browser.get('failures',[])
failed_continuations=[row for row in browser.get('continuations',[])if row['type']=='continuation-failed']
assert not failed_continuations, 'A failed continuation requires delivery-specific resolution'
roof_recovery=None
if initial_failures:
    assert len(initial_failures)==1 and initial_failures[0]['phase']=='global'
    failure=initial_failures[0]
    assert 'validateVisualState'in failure['message'] and mid in failure['message'] and 'strictly deep-equal'in failure['message']
    report_binding(failure['script'])
    recovery=browser['roofCameraRecovery'];assert recovery['sameHost'] and recovery['resolved']
    assert recovery['initialProbe']['beaconsAtPoint']==[mid] and recovery['initialProbe']['uiAtPoint']==[]
    assert recovery['initialState']['lighting']['enabled']is False
    corrected=recovery['correctedState'];probe=next(r for r in corrected['visualProbes']if r['key']=='roof')
    initial_probe=next(r for r in recovery['initialState']['visualProbes']if r['key']=='roof')
    assert probe['probe']==initial_probe['probe'], 'The frozen roof geometry probe must not be moved'
    assert probe['projection']['insideViewport'] and not probe['projection']['beaconsAtPoint'] and not probe['projection']['uiAtPoint']
    assert corrected['asset']['visible'] and corrected['asset']['status']=='loaded' and corrected['asset']['cityIntegration']
    assert corrected['asset']['verifiedAsset']['sha256']==json.loads((root/prefix/('assets/models/candidates/'+mid+'/manifest.json')).read_text())['assets']['full']['sha256']
    assert recovery['sourceScript']==browser['qaScript'];report_binding(recovery['sourceScript'])
    capture=next(c for c in browser['captures']if c['file']==recovery['capture']['file']);assert capture['sha256']==recovery['capture']['sha256'];report_binding(capture['captureScript'])
    starts=[r for r in browser['continuations']if r['type']=='continuation-started'];assert len(starts)==1 and Path(starts[0]['module']).name=='qa-resume-roof.cjs'
    assert 'camera'in starts[0]['reason'].lower()
    roof_recovery={'resolved':True,'same_original_host':True,'initial_failure_retained':failure,'original_probe_unchanged':True,'initial_own_label_intersection':recovery['initialProbe'],'corrected_projection':probe['projection'],'accepted_capture':capture,'continuation_script':binding(starts[0]['module']),'scope':'Only roof camera changed to separate the unchanged geometry target from its own persistent beacon. Initial QA assertion remains retained; production assets/source/contracts remain frozen.'}
else:
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
assert contract['clip_capacity']==224 and contract['expected_global_clip_triangles']==218
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
assert 'view_image' in root_native['method'] and root_native['reviewer']in('root','/root')
for role in ['full','lod']:
    scene=browser['global'][role]
    asset=scene['asset']; assert asset['status']=='loaded' and asset['visible'] and asset['cityIntegration']
    assert asset['verifiedAsset']['sha256']==manifest['assets'][role]['sha256']
    shader=scene['candidate']['shader']
    assert shader['triangleLimit']==224 and shader['clippingTexture']['height']==224
    assert shader['clippingTexture']['bytes']==14336 and shader['triangles']<=218
    active_triangles=0
    for clip in scene['candidate']['clips']:
        geometry=clip['geometry']; assert geometry['type']=='Polygon' and len(geometry['coordinates'])==1
        active_triangles+=len(geometry['coordinates'][0])-3
    assert shader['triangles']==active_triangles
beacons=browser['beacons']
assert beacons['state']['count']==80 and beacons['state']['viewportLabelCount']==80
assert beacons['allSpritesPresent'] and len(beacons['picks'])==80
assert all(row['id']==row['hit']for row in beacons['picks'])
touch=beacons['touch']; assert touch['id']==mid and touch['changedDestination'] and touch['targetAssetVisibleAfterTouch']

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
    assert qa_images[name]['accepted']==root_images[name]['accepted_for_scope']
    assert root_images[name].get('actually_viewed_by_root',root_images[name].get('actually_viewed'))
    images.append({'kind':'final_browser' if qa_images[name]['accepted'] else 'retained_insufficient_process_frame','qa_and_root_actual_view_records_agree':True,**actual})
assert len([r for r in images if r['kind']=='retained_insufficient_process_frame'])==qa['insufficient_process_images_retained']
root_native_images={r['file']:r for r in root_native['images']}
assert len(native['images'])>=7 and set(root_native_images)=={r['file']for r in native['images']}
for record in native['images']:
    actual=require(record,audit_rel+record['file']); other=root_native_images[record['file']]
    assert other['sha256']==actual['sha256'] and other['bytes']==actual['bytes']
    assert record['actually_viewed'] and other['passed']
    images.append({'kind':'final_native','independent_and_root_actual_view_records_agree':True,**actual})
for record in root_checks['mapping_images_actually_viewed_by_root']:
    assert record['passed']; images.append({'kind':'final_mapping','root_actual_view_record_bound':True,**require(record,audit_rel+record['file'])})
assert not any((audit/n).exists()for n in ['visual-control.json','visual-review-control.json','continuation-control.json'])
for record in host['archived_controls']:report_binding(record)
assert host['failures']==len(initial_failures)and host['failed_continuations']==len(failed_continuations)

# Reports bind actual frozen bytes, rather than relying on the presence of a pass label.
for record in independent['reports']: require(record,audit_rel+record['file'])
require(independent['final_footprint'],audit_rel+'footprint-review.json')
require(independent['final_manifest'],prefix+'assets/models/candidates/'+mid+'/manifest.json')
for key in ['source_code_files','reference_records_unchanged_from_independent_content_review','new_public_assets']:
    for record in metadata[key]: require(record,record['file'])
for record in metadata['readme_district_and_link_checks']: require(record['binding'],record['file'])

# A subtle entry-view line artifact was reviewed separately from geometry acceptance.
plane=read('north-front-plane-investigation.json')
assert plane['passed_for_geometric_planar_coverage_only'] and plane['rendering_artifact_cause_confirmed']is False
assert plane['raw_sha256']==manifest['assets']['raw']['sha256']
geometry=read('independent-geometry-review.json');assert plane['triangle_payload_sha256']==geometry['assets']['raw']['actualTrianglesENU']['sha256']
assert plane['planar_triangles']==133 and len(plane['controls'])==3
assert all(r['missing_face_area_m2']==0 and r['coplanar_overlap_pair_area_m2']==0 for r in plane['controls'])
assert plane['browser_capture_actually_viewed_by_reviewer']['actually_viewed']
entry_diagnostic_capture=report_binding(plane['browser_capture_actually_viewed_by_reviewer']);report_binding(plane['script'])
visual_diagnostic={'report':binding(audit/'north-front-plane-investigation.json'),'capture':entry_diagnostic_capture,'actual_planar_geometry_regions_have_no_missing_faces_or_coplanar_overlap':True,'cause_confirmed':False,'limitation':'Faint segmented vertical lines are visible in the browser stone face; the independent geometric union excludes a physical hole or overlap in the three sampled wall regions. The exact display cause remains unconfirmed and is not represented as a recovered runtime error.'}

tracked=subprocess.check_output(['git','diff','--name-status',base,'--'],cwd=root,text=True).splitlines()
assert not any(line.startswith('D\t')for line in tracked)
old_audits=[line for line in tracked if '\t'+prefix+'data/audit/'in line and '\t'+audit_rel not in line]
old_assets=[line for line in tracked if '\t'+prefix+'assets/'in line and '\t'+prefix+'assets/models/candidates/'+mid+'/'not in line]
assert not old_audits and not old_assets
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
added={line.split('\t',1)[1]for line in tracked if line.startswith('A\t')}|{name for name in untracked if name}
for name in added:
    if name.startswith(prefix+'data/audit/'): assert name.startswith(audit_rel),name
    if name.startswith(prefix+'assets/'): assert name.startswith(prefix+'assets/models/candidates/'+mid+'/'),name
    if name.startswith(prefix+'source/precise/'): assert name.startswith(prefix+'source/precise/'+mid+'/'),name
status=subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=root).decode().split('\0')
assert not [line for line in status if line and 'D'in line[:2]]
self_rel=str(out.relative_to(root))
new_files=[binding(name)for name in sorted(added)if name!=self_rel]
reports={name:binding(audit/name)for name in ['browser.json','qa-visual-review.json','browser-visual-review.json','native-visual-review.json','independent-review.json','qa-host-completion.json','README.md','root-checks.json','runtime-checks.json']}
result={'schema':'jiangwan-swimming-hall-independent-prepublication-v1','passed':True,
        'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_commit':base,
        'scope':'Final lightweight exact-file inventory, QA input/capture binding and previous completed independent-review binding. No browser, model reconstruction, native reopen, occupancy rerun or historical mesh matrix.',
        'final_reports':reports,'all_qa_frozen_inputs_match_current_bytes':True,
        'frozen_inputs':list(frozen.values()),'final_four_assets':assets,'final_images':images,
        'browser_saved_image_count':len(captures),'browser_final_accepted_image_count':sum(r['accepted'] for r in qa_images.values()),
        'insufficient_process_images_retained':qa['insufficient_process_images_retained'],'native_final_image_count':len(native['images']),
        'mapping_final_image_count':len(root_checks['mapping_images_actually_viewed_by_root']),
        'image_review_scope':'Browser images were actually reviewed by QA and root; native images by reviewer and root. This final pass checks exact image-byte bindings without claiming another image view.',
        'browser_closed_and_normal_host_exit_recorded':True,
        'no_unresolved_application_errors':True,'environment_recovery_and_observer_limitations':environment_review,'roof_camera_assertion_recovery':roof_recovery,'entry_rendering_diagnostic_and_limit':visual_diagnostic,
        'historical_qa_assertion_correction':{'initial_failures_retained':initial_failures,
            'explanation':'The retained roof visibility assertion was resolved within the same browser host by changing only camera pitch; the unchanged roof probe is no longer under its own label. The GPU active triangle count is independently checked from actual clip geometry.',
            'failed_continuation_count_retained':len(failed_continuations)},
        'actual_browser_gpu_triangle_limit':224,'catalog_mask_triangles':218,
        'beacons_80_visible_and_independently_pickable':True,
        'actual_native_touch_changed_destination_and_showed_target':True,
        'global_models':80,'yangpu_models':5,'new_file_count_excluding_this_self_report':len(new_files),
        'new_files':new_files,'self_report_path':self_rel,'self_digest_omitted_to_avoid_recursion':True,
        'tracked_diff':tracked,'no_deletions':True,'no_old_audit_or_old_model_asset_changes':True,
        'old_record_preservation_evidence':binding(audit/'independent-metadata-review.json'),
        'limits':'Publication HTTP bytes and any files added after this gate require the separate publication record. Source/geometry uncertainty and exterior-only scope remain unchanged.'}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'frozen_inputs':len(frozen),'browser_images':len(captures),'new_files':len(new_files)}))
