"""Lightweight exact-byte bridge from completed numeric proof to actual public catalog.

No source GLB decode, geometry, numeric replay, browser or test is run here.
Usage: previous-numeric.json public-runtime.json public-preflight.json repository-root output.json
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

prior_path, runtime_path, preflight_path, root, output = map(Path, sys.argv[1:6])
project = root / 'projects/shanghai'

def bind(p):
    p = p.resolve()
    b = p.read_bytes()
    return {'file': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def check(record):
    actual = bind(Path(record['file']))
    assert actual['bytes'] == record['bytes'] and actual['sha256'] == record['sha256'], record['file']
    return actual

prior_bytes = prior_path.read_bytes()
result = json.loads(prior_bytes)
assert result['schema'] == 'city-museum-independent-height-numeric-v1' and result['passed']
assert result['fragment_interpolation_certified'] is False
assert result['actual_final_browser_pixels_required'] is True
check(result['script'])
old_bridge = result.get('numeric_execution_bridge_inputs', result['final_bridge_inputs'])
old_runtime_record = check(old_bridge['runtime_receipt'])
old_runtime = json.loads(Path(old_runtime_record['file']).read_text())
current = json.loads(runtime_path.read_text())
assert current['schema'] == 'city-museum-height-clipping-runtime-v1'
assert current['passed'] and current['private_preflight'] is False
for key in ['data_payload', 'source_transform', 'rows', 'height_clip_ids', 'preflight_sha256',
            'bindings', 'old_rows', 'pre_height_rows', 'added_height_rows', 'total_rows', 'capacity',
            'sample_checks', 'shader_checks', 'source_vector_collision_unchanged', 'debug_clips_separate']:
    assert current[key] == old_runtime[key], f'Numerical input/result changed: {key}'
old_rows = check(old_bridge['gpu_row_payload'])
new_rows = bind(runtime_path.parent / current['data_payload']['file'])
assert new_rows['sha256'] == old_rows['sha256'] == current['data_payload']['sha256']
assert new_rows['bytes'] == old_rows['bytes'] == 262 * 16 * 4
source_bindings = []
for record in current['bindings']:
    source_bindings.append(check({**record, 'file': str(project / record['file'])}))
assert source_bindings == old_bridge['actual_production_code_bindings']
preflight_record = bind(preflight_path)
assert preflight_record['sha256'] == current['preflight_sha256'] == old_bridge['preflight']['sha256']
spec = json.loads(preflight_path.read_text())
model_id = 'yangpu-former-shanghai-city-museum'
catalog_path = project / 'data/candidate-city-integrations.json'
placement_path = project / 'data/global-models/additional-placement.json'
footprint_path = project / 'data/audit/city-museum-v1/footprint-review.json'
catalog = json.loads(catalog_path.read_text())
model = next(r for r in catalog['models'] if r['id'] == model_id)
placement = next(r for r in json.loads(placement_path.read_text())['records'] if r['id'] == model_id)
footprint = json.loads(footprint_path.read_text())['proposed_placement_contract']
for record in [model, placement, footprint]:
    assert record['display_height_clips'] == spec['display_height_clips']
assert placement == footprint, 'Actual placement must equal final reviewed footprint contract'
public_bindings = [bind(p) for p in [runtime_path, catalog_path, placement_path, footprint_path]]
attempt_path = Path(__file__).with_name('attempt-1-binding-failure.json')
attempt_record = bind(attempt_path)
archive = prior_path.with_name(prior_path.stem + '-before-final-binding-' + hashlib.sha256(prior_bytes).hexdigest()[:12] + prior_path.suffix)
if not archive.exists():
    archive.write_bytes(prior_bytes)
original_numeric_record = result.get('final_public_binding', {}).get('original_numeric_report_preserved', bind(archive))
result['numeric_execution_runtime_private_preflight'] = result['runtime_private_preflight']
result['numeric_execution_bridge_inputs'] = old_bridge
result['final_binding_utc'] = datetime.now(timezone.utc).isoformat()
result['final_binding_script'] = bind(Path(__file__))
result['final_public_binding'] = {
    'passed': True,
    'method': 'Exact current production code, full262-row bytes, source matrix, row/sample/shader results and preflight SHA comparison to the completed independent source numeric proof; actual catalog/placement/footprint height clips equal the numeric inputs. No new source decode or geometry replay.',
    'private_preflight': False,
    'public_runtime_receipt': bind(runtime_path),
    'public_gpu_row_payload': new_rows,
    'public_catalog': bind(catalog_path),
    'public_placement': bind(placement_path),
    'public_footprint': bind(footprint_path),
    'preflight': preflight_record,
    'actual_production_code_bindings': source_bindings,
    'rows_and_source_matrix_identical_to_completed_numeric_proof': True,
    'public_height_clips_equal_completed_numeric_inputs': True,
    'original_numeric_report_preserved': original_numeric_record,
    'immediately_prior_report_preserved': bind(archive),
    'original_private_runtime_receipt_preserved': old_runtime_record,
    'first_binding_rejection_preserved': attempt_record,
    'original_source_decoded_again': False,
    'fragment_interpolation_certified': False,
    'actual_final_browser_pixels_required': True,
}
result['final_bridge_inputs'] = {
    **old_bridge,
    'runtime_receipt': bind(runtime_path),
    'gpu_row_payload': {**old_bridge['gpu_row_payload'], **new_rows},
    'preflight': preflight_record,
    'actual_production_code_bindings': source_bindings,
    'catalogue_overlay_scope': 'Final public runtime receipt is private_preflight:false; actual catalog/placement/footprint height clips exactly equal the completed numeric inputs. Earlier private overlay proof and failed binding attempt are retained separately.',
    'public_catalog': bind(catalog_path),
    'public_placement': bind(placement_path),
    'public_footprint': bind(footprint_path),
}
result['inputs'].extend(public_bindings + [new_rows, preflight_record, attempt_record, bind(archive)])
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': True, 'numeric_proof_reused_without_source_decode': True,
                  'public_runtime_sha256': bind(runtime_path)['sha256'], 'output': bind(output)}))
