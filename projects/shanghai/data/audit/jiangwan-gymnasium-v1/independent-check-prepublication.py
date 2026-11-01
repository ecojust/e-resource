"""Final lightweight exact-file/QA binding gate; no browser or geometry rerun.
Usage: repository-root output.json
"""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys

root, out = map(Path, sys.argv[1:3])
base='a47e69e9cbde689266855d573aa8d1f25b02944d'
prefix='projects/shanghai/'
audit_rel=prefix+'data/audit/jiangwan-gymnasium-v1/'
audit=root/audit_rel
mid='yangpu-jiangwan-gymnasium'
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
assert host['status'] in ['completed','completed-with-recovered-environment-errors'] and host['browser_closed']
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
if browser['errors'] or browser['warnings'] or browser.get('responseCheckFailures'):
    env=read('env-recovery.json')
    assert env==browser['environmentRecovery']
    assert env['sameHostSuccessfulRetry'] and env['unresolved_application_errors']==0
    assert env['runGeneratedAt']==browser['generatedAt'] and env['retainedHostPid']==9429
    assert browser['errors']==env['original']['errors'] and browser['warnings']==env['original']['warnings']
    assert browser['responseCheckFailures']==env['original']['responseCheckFailures']
    assert len(env['original']['errors'])==len(env['original']['warnings'])==1
    assert len(env['original']['responseCheckFailures'])==2
    assert all('response.body' in row['message']for row in env['original']['responseCheckFailures'])
    assert 'No earlier unknown response URL is recovered or invented' in env['observer_policy']
    for key in ['input','module','previousRecoveryModule','sourceTrace']: report_binding(env[key])
    trace=json.loads((audit/env['sourceTrace']['file']).read_text())
    paths={row['path']for row in trace if row['status']==200}
    assert paths==set(env['sourceTrace']['matchedUniquePaths'])
    assert set(env['sourceTrace']['knownSuccessfulBrowserResponsePaths'])<=paths
    expected={row['path']:row for row in env['bodyReverificationSources']}
    retries={row['path']:row for row in env['retries']}
    assert set(expected)==set(retries)==paths|{env['resource']['path']}
    assert len(retries)==12
    verified=[]
    for path,row in expected.items():
        assert row['baseline_commit']==base
        data=Path(row['cache_path']).read_bytes()
        sha=hashlib.sha256(data).hexdigest()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        tree=subprocess.check_output(['git','ls-tree',base,'--',prefix+path],cwd=root,text=True).strip()
        assert tree==row['git_tree_query'] and tree.split()[2]==blob==row['git_blob']==row['actual_git_blob']
        assert len(data)==row['bytes'] and sha==row['sha256']
        retry=retries[path]
        assert retry['status']==200 and retry['sha256']==sha and retry['bytes']==len(data) and retry['git_blob']==blob
        verified.append({'path':path,'bytes':len(data),'sha256':sha,'git_blob':blob,'cache_bytes_independently_checked':True,'same_page_retry_status':200})
    resource=env['resource']; fallback=env['publicFallback']
    assert fallback['status']==200 and '/'+base+'/'in fallback['url']
    for key in ['sha256','bytes','git_blob','actual_git_blob']: assert fallback[key]==resource[key]
    assert any(row['id']=='14-13723-6690' and row['visible']for row in env['reloadedScene']['stream']['active'])
    current=env['currentSceneAfterSynchronousVerification']
    assert current['glError']==0 and current['asset']['visible'] and current['asset']['status']=='loaded'
    assert 'landmark='+mid in current['hash']
    bad_http=[{k:row[k]for k in ['phase','status','url']}for row in browser['http']if row.get('status',200)>=400]
    assert bad_http==env['original']['http']
    environment_review={'report':binding(audit/'env-recovery.json'),
        'resource_404_recovered_by_baseline_verified_immutable_http_and_actual_same_host_reload':True,
        'prior_console_errors_retained':env['original']['errors'],
        'prior_warnings_retained':env['original']['warnings'],
        'historical_observer_protocol_failures_retained':env['original']['responseCheckFailures'],
        'historical_failed_response_urls_recovered':False,
        'observer_policy':env['observer_policy'],'verified_sources':verified,
        'unresolved_application_errors':0,
        'scope':'Two historical Playwright body-observer evidence gaps remain explicitly bounded. Later synchronous in-page fetch verifies all12 bound source paths; it does not retrospectively identify either unknown failed URL.'}
else:
    assert not browser.get('responseCheckFailures')
initial_failures=browser.get('failures',[])
failed_continuations=[row for row in browser.get('continuations',[])if row['type']=='continuation-failed']
if initial_failures:
    assert len(initial_failures)==1 and '55 !== 202' in initial_failures[0]['message']
    assert 'All final clip rows' in initial_failures[0]['message']
    report_binding(initial_failures[0]['script'])
for row in browser.get('continuations',[]):
    if 'module' in row:
        actual=binding(row['module'])
        assert actual['sha256']==row['moduleSha256']==row['expectedModuleSha256']
for row in failed_continuations:
    assert 'response.body' in row['message']
    expected_message={'qa-resume-active-clips.cjs':'Actual HTTP body verification failed',
                      'qa-resume-environment.cjs':'New unresolved error in responseCheckFailures'}
    assert expected_message[Path(row['module']).name] in row['message']
assert len(failed_continuations)==2 if environment_review else not failed_continuations
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
assert contract['clip_capacity']==224 and contract['expected_global_clip_triangles']==202
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
assert 'view_image' in root_native['method'] and root_native['reviewer']=='root'
for role in ['full','lod']:
    scene=browser['global'][role]
    asset=scene['asset']; assert asset['status']=='loaded' and asset['visible'] and asset['cityIntegration']
    assert asset['verifiedAsset']['sha256']==manifest['assets'][role]['sha256']
    shader=scene['candidate']['shader']
    assert shader['triangleLimit']==224 and shader['clippingTexture']['height']==224
    assert shader['clippingTexture']['bytes']==14336 and shader['triangles']<=202
    active_triangles=0
    for clip in scene['candidate']['clips']:
        geometry=clip['geometry']; assert geometry['type']=='Polygon' and len(geometry['coordinates'])==1
        active_triangles+=len(geometry['coordinates'][0])-3
    assert shader['triangles']==active_triangles
beacons=browser['beacons']
assert beacons['state']['count']==79 and beacons['state']['viewportLabelCount']==79
assert beacons['allSpritesPresent'] and len(beacons['picks'])==79
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
assert len([r for r in images if r['kind']=='retained_insufficient_process_frame'])==qa['insufficient_process_images_retained']==1
root_native_images={r['file']:r for r in root_native['images']}
assert len(native['images'])==7 and set(root_native_images)=={r['file']for r in native['images']}
for record in native['images']:
    actual=require(record,audit_rel+record['file']); other=root_native_images[record['file']]
    assert other['sha256']==actual['sha256'] and other['bytes']==actual['bytes']
    assert record['actually_viewed'] and other['passed']
    images.append({'kind':'final_native','independent_and_root_actual_view_records_agree':True,**actual})
for record in root_checks['mapping_images_actually_viewed_by_root']:
    assert record['passed']; images.append({'kind':'final_mapping','root_actual_view_record_bound':True,**require(record,audit_rel+record['file'])})
assert not (audit/'visual-control.json').exists() and not (audit/'continuation-control.json').exists()

# Reports bind actual frozen bytes, rather than relying on the presence of a pass label.
for record in independent['reports']: require(record,audit_rel+record['file'])
require(independent['final_footprint'],audit_rel+'footprint-review.json')
require(independent['final_manifest'],prefix+'assets/models/candidates/'+mid+'/manifest.json')
for key in ['source_code_files','reference_records_unchanged_from_independent_content_review','new_public_assets']:
    for record in metadata[key]: require(record,record['file'])
for record in metadata['readme_district_and_link_checks']: require(record['binding'],record['file'])

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
result={'schema':'jiangwan-gymnasium-independent-prepublication-v1','passed':True,
        'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_commit':base,
        'scope':'Final lightweight exact-file inventory, QA input/capture binding and previous completed independent-review binding. No browser, model reconstruction, native reopen, occupancy rerun or historical mesh matrix.',
        'final_reports':reports,'all_qa_frozen_inputs_match_current_bytes':True,
        'frozen_inputs':list(frozen.values()),'final_four_assets':assets,'final_images':images,
        'browser_saved_image_count':len(captures),'browser_final_accepted_image_count':sum(r['accepted'] for r in qa_images.values()),
        'insufficient_process_images_retained':1,'native_final_image_count':7,
        'mapping_final_image_count':len(root_checks['mapping_images_actually_viewed_by_root']),
        'image_review_scope':'Browser images were actually reviewed by QA and root; native images by reviewer and root. This final pass checks exact image-byte bindings without claiming another image view.',
        'browser_closed_and_normal_host_exit_recorded':True,
        'no_unresolved_application_errors':True,'environment_recovery_and_observer_limitations':environment_review,
        'historical_qa_assertion_correction':{'initial_failures_retained':initial_failures,
            'explanation':'The initial assertion confused55 currently active clipping rows with202 catalogue rows. Final GPU capacity and actual active geometry are checked separately; production clipping was unchanged.',
            'failed_continuation_count_retained':len(failed_continuations)},
        'actual_browser_gpu_triangle_limit':224,'catalog_mask_triangles':202,
        'beacons_79_visible_and_independently_pickable':True,
        'actual_native_touch_changed_destination_and_showed_target':True,
        'global_models':79,'yangpu_models':4,'new_file_count_excluding_this_self_report':len(new_files),
        'new_files':new_files,'self_report_path':self_rel,'self_digest_omitted_to_avoid_recursion':True,
        'tracked_diff':tracked,'no_deletions':True,'no_old_audit_or_old_model_asset_changes':True,
        'old_record_preservation_evidence':binding(audit/'independent-metadata-review.json'),
        'limits':'Publication HTTP bytes and any files added after this gate require the separate publication record. Source/geometry uncertainty and exterior-only scope remain unchanged.'}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'frozen_inputs':len(frozen),'browser_images':len(captures),'new_files':len(new_files)}))
