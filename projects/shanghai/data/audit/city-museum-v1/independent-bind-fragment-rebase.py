"""Bind the narrow fragment-coordinate repair; no asset decoding or browser launch.
Usage: repository-root private-review-directory output.json
"""
from pathlib import Path
import datetime, hashlib, json, struct, subprocess, sys, tempfile

root, private, out = map(Path, sys.argv[1:4])
project = root/'projects/shanghai'
audit = project/'data/audit/city-museum-v1'
history = private/'fragment-rebase-history'
before = history/'frozen-before'
qa = Path('/workspace/shanghai-city-museum-qa')
stage = 'fragment-rebased-final'
baseline = '93e3cb2d0ddeba1a7db7d435bf66c2f61492326e'

def read(path): return json.loads(Path(path).read_text())
def digest(data): return hashlib.sha256(data).hexdigest()
def binding(path):
    path = Path(path)
    data = path.read_bytes()
    try: name = str(path.relative_to(root))
    except ValueError: name = str(path)
    return {'file': name, 'bytes': len(data), 'sha256': digest(data)}
def require(record, path=None):
    path = Path(path or record['file'])
    actual = binding(path if path.is_absolute() else root/path)
    assert actual['sha256'] == record['sha256'], (path, 'SHA mismatch')
    if 'bytes' in record: assert actual['bytes'] == record['bytes']
    return actual
def project_record(record):
    name=record['file']
    return require(record, root/name if name.startswith('projects/') else project/name)

delta = read(audit/'fragment-runtime-source-change.json')
source = read(audit/'runtime-height-source-change.json')
old_source_path = audit/'runtime-height-source-change-pre-fragment-rebase.json'
old_source = read(old_source_path)
expected = {'projects/shanghai/'+n for n in ['src/candidate-city-clipping.js', 'tests/candidate-city-clipping.test.mjs', 'src/app.js', 'src/map-scene.js', 'index.html']}
assert delta['stage'] == source['stage'] == stage
assert len(delta['files']) == 5 and {r['file'] for r in delta['files']} == expected
assert delta['previous_source_report_sha256'] == binding(old_source_path)['sha256']
assert delta['resulting_source_report_sha256'] == binding(audit/'runtime-height-source-change.json')['sha256']
assert len(source['files']) == len(old_source['files']) == 9
old_by_file = {r['file']: r for r in old_source['files']}
changed = set()
baseline_differences=[]
for row in source['files']:
    assert row['file'] in old_by_file
    raw = subprocess.check_output(['git', 'show', baseline+':'+row['file']], cwd=root)
    assert row['before_sha256'] == old_by_file[row['file']]['before_sha256']
    if digest(raw) != row['before_sha256']:
        baseline_differences.append({'file':row['file'],'baseline_sha256':digest(raw),'retained_pre_height_sha256':row['before_sha256']})
    actual = binding(root/row['file'])
    assert actual['sha256'] == row['after_sha256'] and actual['bytes'] == row['after_bytes']
    if row['after_sha256'] != old_by_file[row['file']]['after_sha256']: changed.add(row['file'])
assert changed == expected
assert {r['file'] for r in baseline_differences} == {'projects/shanghai/src/candidate-city-clipping.js','projects/shanghai/tests/candidate-city-clipping.test.mjs','projects/shanghai/index.html'}
patch = Path('/workspace/shanghai-city-museum-runtime/rebase/rebase-source.patch')
assert binding(patch)['sha256'] == delta['patch_sha256']
with tempfile.TemporaryDirectory(prefix='fragment-patch-replay-', dir=private) as scratch:
    scratch = Path(scratch)
    for row in delta['files']:
        data = (before/row['file']).read_bytes()
        assert digest(data) == row['before_sha256'] == old_by_file[row['file']]['after_sha256']
        dest = scratch/row['file']; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
    replay = subprocess.run(['patch', '--batch', '--forward', '-p1', '-i', str(patch)], cwd=scratch, capture_output=True, text=True)
    assert replay.returncode == 0, (replay.stdout, replay.stderr)
    for row in delta['files']:
        assert (scratch/row['file']).read_bytes() == (root/row['file']).read_bytes()

clipper = (project/'src/candidate-city-clipping.js').read_text()
assert 'vCandidatePosition=mat3(modelMatrix)*candidatePosition.xyz;' in clipper
assert '#ifndef USE_TRANSMISSION\nuniform mat4 modelMatrix;\n#endif' in clipper
assert 'bool candidateInside(vec3 candidateWorldPosition)' in clipper
assert 'if(candidateInside(vCandidatePosition+modelMatrix[3].xyz))discard;' in clipper
assert 'candidate-city-clip-v3' in clipper
assert clipper.index('candidatePosition=batchingMatrix*candidatePosition;') < clipper.index('candidatePosition=instanceMatrix*candidatePosition;') < clipper.index('vCandidatePosition=mat3(modelMatrix)')

height = read(audit/'independent-height-clip-review.json')
runtime = read(audit/'height-clipping-checks.json')
assert height['passed'] and runtime['passed'] and not runtime['private_preflight']
assert [runtime[k] for k in ['old_rows','pre_height_rows','added_height_rows','total_rows','capacity']] == [218,258,4,262,288]
assert runtime['old_rows_identical'] and runtime['pre_height_rows_identical']
payload = require(height['actual_gpu_rows'])
assert payload['sha256'] == 'ce4d45d3a9472b07790959cdb6052c715ea4411334d6399e2bccf9baac0feb09'
assert payload['sha256'] == runtime['data_payload']['sha256'] and payload['bytes'] == 16768
for record in runtime['bindings']: project_record(record)
for key in ['final_footprint','final_contract','final_manifest','final_catalog','final_additional_placement']:
    require(height[key])
historical = []
seen = set()
for record in [height['final_runtime']]+height['numeric_final_input_bindings']:
    if record['file'] in seen: continue
    seen.add(record['file'])
    current = binding(root/record['file'])
    if current['sha256'] == record['sha256']:
        require(record)
    else:
        archived = require(record, before/record['file'])
        historical.append({'recorded_file': record['file'], 'archive_binding': archived})
assert {r['recorded_file'] for r in historical} == expected-{'projects/shanghai/tests/candidate-city-clipping.test.mjs'} | {'projects/shanghai/data/audit/city-museum-v1/height-clipping-checks.json'}

varying = read(qa/'north-interface-varying-diagnostic.json')
gpu = read(qa/'north-interface-gpu-diagnostic.json')
rays = read(qa/'north-interface-dark-pixels-diagnostic.json')
draw = read(qa/'north-interface-draw-pixels-diagnostic.json')
variant = read(qa/'north-interface-rebase-diagnostic.json')
viewed = read(history/'diagnostic-visual-review.json')
assert varying['result']['constantControlsPassed']
assert varying['result']['materialRestored'] and varying['result']['hooksRestored']
assert varying['result']['before'] == varying['result']['after']
assert not varying['result']['errors'] and not varying['result']['stateViolations']
frames = {r['label']:r for r in varying['result']['frames']}
assert frames['constant-1']['pixels'] == [[68,51,34,17]]*3
assert frames['constant-2']['pixels'] == [[136,170,204,238]]*3
assert frames['position-x']['pixels'] == frames['position-x-repeat']['pixels']
rows = next(s for s in gpu['result']['samples'] if s['object']['name']=='mesh_10')['gpuTextureReadback']['rows']
assert len(rows)==44 and len(draw['result']['changes'])==1
assert draw['result']['changes'][0]['draw']==24 and draw['result']['changes'][0]['object']['name']=='mesh_10'
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
def cross(ax,az,bx,bz): return f32(f32(ax*bz)-f32(az*bx))
def inside(point,row):
    x,y,z=point; a,b,c=[row[0:2],row[2:4],row[4:6]]
    cs=[cross(f32(v[0]-u[0]),f32(v[1]-u[1]),f32(x-u[0]),f32(z-u[1])) for u,v in [(a,b),(b,c),(c,a)]]
    return row[8]<=x<=row[10] and row[9]<=z<=row[11] and row[6]<=y<=row[7] and (all(v>=-f32(.001) for v in cs) or all(v<=f32(.001) for v in cs)),cs
points=[]
for index,ray in enumerate(rays['result']['rays']):
    point=[struct.unpack('<f',bytes(frames['position-'+axis]['pixels'][index]))[0] for axis in 'xyz']
    original=ray['hits'][0]['pointWorld']; matching=[i for i,row in enumerate(rows) if inside(point,row)[0]]
    assert not matching and inside([f32(v) for v in original],rows[42])[0]
    points.append({'pixel':ray['pixel'],'actual_fragment_xyz':point,'same_pixel_ray_xyz':original,'actual_minus_ray_m':[a-b for a,b in zip(point,original)],'actual_matching_rows':matching,'row42_cross':inside(point,rows[42])[1]})
assert variant['result']['rebasedFrame']['pixels']==[[217,221,216,255]]*3
assert not variant['result']['errors'] and not variant['result']['stateViolations']
assert variant['restoration']['materialRestored'] and variant['restoration']['hooksRestored']
assert variant['restoration']['before']==variant['restoration']['after']
assert variant['restoredScreenshot']['sha256']==varying['screenshot']['sha256']=='72b24e6ea1d6fc02db4fe6e2620007619c42a2576b511cd23774fbc9d3b581da'
assert viewed['diagnostic_variant_visually_resolves_observed_fragment'] and not viewed['final_visual_acceptance']
for row in viewed['images']: require(row); assert row['actually_viewed_by_independent_reviewer']

stability=read(audit/'fragment-coordinate-stability.json')
assert stability['passed'] and stability['stage']==stage
focused=read(audit/'height-focused-tests.json');assert focused['passed']
checks=read(audit/'runtime-checks.json');assert checks['passed'] and not checks['historical_asset_matrix_rerun']
integration=read(audit/'global-integration-checks.json');assert integration['passed']==7
for report in [focused,checks,integration,stability]:
    for record in report.get('bindings',[]): project_record(record)
current_paths=[audit/n for n in ['fragment-runtime-source-change.json','runtime-height-source-change.json','runtime-height-source-change-pre-fragment-rebase.json','fragment-coordinate-stability.json','height-clipping-checks.json','height-focused-tests.json','runtime-checks.json','global-integration-checks.json','gpu-height-rows.f32']]
current_paths += [root/r['file'] for r in source['files']]
current_paths += [root/height[k]['file'] for k in ['final_footprint','final_contract','final_manifest','final_catalog','final_additional_placement']]
current_paths += [root/r['file'] if r['file'].startswith('projects/') else project/r['file'] for r in stability['bindings']]
current_paths=list(dict.fromkeys(current_paths))
diagnostic_paths=[qa/n for n in ['north-interface-draw-pixels-diagnostic.json','north-interface-gpu-diagnostic.json','north-interface-dark-pixels-diagnostic.json','north-interface-varying-diagnostic.json','north-interface-rebase-diagnostic.json','north-interface-rebase-diagnostic-normal-color.png','north-interface-after-rebase-restored.png']]
diagnostic_paths += [history/'diagnostic-visual-review.json',patch]
result={'schema':'city-museum-independent-fragment-rebase-v1','passed':True,'script':binding(Path(__file__)),'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'required_final_browser_stage':stage,'final_browser_pending':True,'scope':'Independent five-file exact patch replay, shader semantics and actual failed-fragment/readback/reversible-variant evidence. Original four authored assets/native and source geometry were not decoded or rerun. Fresh final browser views and its four real-GL fixtures are still required.','changed_files':sorted(expected),'all_existing_runtime_source_files_exactly_pinned':9,'exact_patch_replay_equals_production':True,'prior_height_review':binding(audit/'independent-height-clip-review.json'),'current_input_bindings':[binding(p) for p in current_paths]+[binding(Path(__file__))],'historical_input_bindings':historical,'diagnostic_bindings':[binding(p) for p in diagnostic_paths],'actual_fragment_replay':points,'diagnostic_cause':'Large world coordinates interpolated across the long thin source triangle produced 21–24 mm Z drift at the three surviving fragments. Actual uploaded rows rejected those fragment positions at their triangle half-planes; same-pixel ray geometry passed. Moving object translation after interpolation, with unchanged clipping rows and source geometry, removed the fragment in the reversible normal-colour diagnostic.','gpu_rows_byte_identical':True,'gpu_rows':{'global':262,'museum':44,'planar_global':258,'height':4,'capacity':288},'authored_assets_and_2d_geometry_unchanged':True,'native_3d_reopen_or_model_matrix_repeated':False,'browser_launched_by_reviewer':False,'historical_numeric_scope':'The unchanged height proof bounds source vertices, rows and geometry only; its original changed-code/runtime inputs are bound to exact retained snapshots. It never certified GPU fragment interpolation.','static_shader_review':{'object_translation_added_after_interpolation':True,'batch_then_instance_order_preserved':True,'three_builtin_modelMatrix_uploaded_per_object':True,'shared_program_uniform_updates_supported':True,'depth_distance_same_upload_path':True,'physical_transmission_declaration_and_order_preserved':True,'program_cache_key':'candidate-city-clip-v3','public_version_chain':'city-height-clips-v2'},'limits':['The reversible one-material diagnostic is not the final production browser acceptance.','The final fresh run must pass actual northern interfaces 3 and 4, retained-neighbor protection, all required views, and the four actual GPU fixture cases.','The failed height-fixed run, its rejected image and single empty-control input recovery remain privately archived; no failure exception is inherited.']}
result['baseline_and_pre_height_epoch_distinction']={'differences':baseline_differences,'reason':'The retained source receipt before hashes refer to the pre-height museum stage. Its clipper/test already used capacity 288 and its index already counted 81. They are not claimed to be the earlier baseline bytes. The fresh rebase is independently replayed against all five exact pre-rebase files.','initial_checker_rejection':binding(history/'bind-attempt-1.json'),'production_failure_waived':False}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'changed_files':5,'historical_bindings':len(historical),'actual_fragment_points':len(points),'geometry_or_asset_decode':False}))
