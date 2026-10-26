#!/usr/bin/env python3
"""Freeze this approved one-file stage; do not install or claim browser success."""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
V10 = HERE.parent
MAIN = Path('/workspace/shanghai_project')
EVIDENCE = HERE / 'evidence'

def identity(path):
    path = Path(path)
    with path.open('rb') as file:
        sha = hashlib.file_digest(file, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'sha256': sha}

def descriptor(path):
    path = Path(path).resolve()
    return {'source': str(path), **identity(path)}

def read(path):
    return json.loads(Path(path).read_bytes())

def write(path, value):
    assert not path.exists(), 'Preserve previous evidence: ' + str(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

old = {'bytes': 22727, 'sha256': 'd157ea58952b4bbf018ea75f64058cf988c349d980234a7eec598388973a858d'}
new = {'bytes': 23086, 'sha256': '6cb2fb4dc1cca564d70f2718014c11600ba5846915df4d707caa5b56a873838c'}
runtime = HERE / 'payload/src/realistic-lighting.js'
assert identity(MAIN / 'src/realistic-lighting.js') == identity(HERE / 'before/realistic-lighting.js') == old
assert identity(runtime) == new
baseline_path = V10 / 'two-district-integration/baseline-lock.json'
baseline = read(baseline_path)
for row in baseline['files'] + baseline['runtime_files']:
    assert identity(MAIN / row['file']) == {key: row[key] for key in ('bytes', 'sha256')}
all_runtime = [{'file': str(path.relative_to(MAIN)), **identity(path)} for path in sorted((MAIN / 'src').iterdir()) if path.is_file()]
assert len(all_runtime) == 31
write(EVIDENCE / 'runtime-baseline-all-src.json', {
    'schema': 'explicit-pre-shadow-fix-all-src-baseline-v1', 'file_count': 31, 'files': all_runtime,
    'scope': 'Additional immutable31-file MAIN source guard; existing42/13 baseline lock remains unchanged.'})
browser_path = V10 / 'qa-two-districts/browser.json'
rejected_sha = '6ad47f0b0d15e8f0a8b2e4996449e898e02be7023bebfb046e5cd7a5e2976abf'
browser = read(browser_path)
assert identity(browser_path) == {'bytes': 586796, 'sha256': rejected_sha}
assert browser['finished_at'] and browser['technical_passed'] and len(browser['captures']) == 11
rejected_copy = EVIDENCE / 'rejected-static-browser.json'
assert not rejected_copy.exists()
shutil.copyfile(browser_path, rejected_copy)
assert identity(rejected_copy) == identity(browser_path)
capture = next(row for row in browser['captures'] if row['name'] == 'putuo-zhenru-main-hall-windows-oblique')
image_path = browser_path.parent / (capture['name'] + '.png')
assert identity(image_path) == {'bytes': 452089, 'sha256': '6e7a0bfdb1b25ebd7a7f1706c11c14c75efd0805f6dbc7d81ba31afa716e2603'}
image_copy = EVIDENCE / 'rejected-zhenru-roof-window-leaks.png'
assert not image_copy.exists()
shutil.copyfile(image_path, image_copy)
write(EVIDENCE / 'diagnosis.json', {
    'schema': 'opaque-inferred-glazing-shadow-diagnosis-v1',
    'cause': 'Opaque inferred city glazing is excluded by allGlazing from castShadow; the retained east neighbor projects regular window-grid light leaks onto Zhenru roof.',
    'root_direction': 'Root explicitly rejected the leak image even if the completed functional report passes and authorized only opaque exact-name Inferred dark glazing caster eligibility.',
    'original_browser': descriptor(browser_path), 'rejected_browser_copy': descriptor(rejected_copy),
    'original_image': descriptor(image_path), 'image_copy': descriptor(image_copy),
    'actually_viewed_by_this_agent': True,
    'capture': {key: capture[key] for key in ('name', 'requested_camera', 'camera', 'actualShadow', 'shadow_check', 'source')},
    'actual_lighting': capture['realism']['lighting'],
    'source_neighbor': {'macro': '14-13716-6693', 'local_id': 1474,
        'key': 'building:aed4d177-6e8f-489a-a6ce-34c01d9b2e25', 'height_m': 26.854,
        'distance_from_target_anchor_to_source_boundary_m': 13.116430343564708,
        'role': 'Retained east neighbor intersects target solar direction; no geometry or owner removed.'},
    'shadow_check_limit': 'Existing technical check verifies4096map/48mhalfextent, not shadow appearance.2.34375cm map texels do not explain the observed metre-scale window pattern.',
    'ray_evidence': descriptor(EVIDENCE / 'compressed-near-169ray-differential.json'),
    'browser_visual_accepted': False, 'patched_browser_run': False,
    'limitations': ['CPU finite-grid evidence is not a pixel-exact GPU shadow proof.',
                    'Patched full11-frame browser and root image review remain required.']})
cpu = read(EVIDENCE / 'cpu-controls.json')
regressions = read(EVIDENCE / 'existing-regressions.json')
rays = read(EVIDENCE / 'compressed-near-169ray-differential.json')
assert cpu['passed'] and regressions['passed'] and rays['passed']
assert len(cpu['controls']) == 15 and cpu['disposalFlagCombinations'] == 4
assert rays['before']['counts']['leaks'] == 50 and rays['after']['counts']['leaks'] == 0
write(EVIDENCE / 'aggregate-cpu-checks.json', {
    'schema': 'opaque-inferred-glazing-shadow-cpu-acceptance-v1', 'passed': True,
    'narrow_controls': descriptor(EVIDENCE / 'cpu-controls.json'),
    'existing_regressions': descriptor(EVIDENCE / 'existing-regressions.json'),
    'ray_differential': descriptor(EVIDENCE / 'compressed-near-169ray-differential.json'),
    'control_count': 15, 'disposal_flag_combinations': 4, 'unchanged_existing_suites_passed': 4,
    'test_sources': [descriptor(HERE / name) for name in ['module-resolution.mjs',
        'tests/opaque-inferred-controls.mjs', 'tests/replay-compressed-near-rays.mjs', 'tests/run_existing_regressions.py']],
    'browser_passed': False, 'main_written': False,
    'scope': 'Actual narrow CPU comparisons plus four unchanged relevant production suites. No GPU/browser image acceptance.',
    'development_note': 'An initial ray-run static import could not resolve three before hook registration. No geometry ran on that attempt; changing the test loader to a dynamic import fixed test setup. Actual successful recorded replay is bound here.'})
delta = {
    'schema': 'opaque-inferred-glazing-shadow-reviewed-delta-v1',
    'scope': 'ONLY opaque exact-name Inferred dark glazing becomes shadow eligible; original casterFilter, all other glazing, visible geometry/materials, shadow settings and disposal behavior retained.',
    'review_authorization': 'Parent root explicitly requested this minimal one-runtime-file fix and an explicit old/new guarded integration revision after rejecting the original static roof light leaks.',
    'original_baseline_lock': descriptor(baseline_path),
    'additional_runtime_baseline': descriptor(EVIDENCE / 'runtime-baseline-all-src.json'),
    'files': [{'file': 'src/realistic-lighting.js', 'source': str(runtime), 'before': old, 'after': new}],
    'cpu_checks': descriptor(EVIDENCE / 'aggregate-cpu-checks.json'),
    'ray_evidence': descriptor(EVIDENCE / 'compressed-near-169ray-differential.json'),
    'diagnosis': descriptor(EVIDENCE / 'diagnosis.json'),
    'source_patch': descriptor(HERE / 'realistic-lighting.js.patch'),
    'rejected_static_browser': descriptor(rejected_copy),
    'rejected_static_visual_reason': 'False window-grid light leaks from excluded opaque city glazing.',
    'browser_passed': False, 'main_written': False, 'original_locks_modified': False,
    'required_future_validation': ['New complete two-target11-frame browser report and root visual review.',
                                  'Both independent catalog5-frame browser runs and root visual reviews.',
                                  'Root visual records explicitly bind this delta SHA and patched runtime SHA.']}
write(HERE / 'runtime-delta.json', delta)
write(HERE / 'runtime-only-installation-plan.json', {
    'schema': 'opaque-city-shadow-runtime-only-candidate-plan-v1',
    'status': 'prepared_candidate_install_only_browser_pending',
    'reviewed_runtime_delta': descriptor(HERE / 'runtime-delta.json'),
    'files': [{'file': 'src/realistic-lighting.js', 'source': str(runtime), **new, 'old_main': old}],
    'file_count': 1, 'main_written': False, 'browser_run': False,
    'scope': 'Root may apply to a NEW isolated candidate after source/delta review; this is not a MAIN publication plan.'})
for row in all_runtime:
    assert identity(MAIN / row['file']) == {key: row[key] for key in ('bytes', 'sha256')}
print(json.dumps({'delta': descriptor(HERE / 'runtime-delta.json'),
                  'runtime_only_plan': descriptor(HERE / 'runtime-only-installation-plan.json')}, indent=2))
