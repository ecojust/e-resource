"""Bind an actual runtime export into the independent numeric check's input schema."""
from pathlib import Path
import hashlib
import json
import sys

review = Path('/workspace/shanghai-city-museum-review')
project = Path('/workspace/e-resource/projects/shanghai')
report = Path(sys.argv[1])
preflight = Path(sys.argv[2])
output = Path(sys.argv[3])
runtime = json.loads(report.read_text())
assert runtime['schema'] == 'city-museum-height-clipping-runtime-v1'

def binding(p):
    b = p.read_bytes()
    return {'file': str(p.resolve()), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

assert binding(preflight)['sha256'] == runtime['preflight_sha256']
transform = runtime['source_transform']
receipt_binding = binding(report)
receipt_archive = output.parent / f"runtime-receipt-{receipt_binding['sha256']}.json"
if not receipt_archive.exists():
    receipt_archive.write_bytes(report.read_bytes())
row_path = report.parent / runtime['data_payload']['file']
row_binding = binding(row_path)
row_archive = output.parent / f"gpu-height-rows-{row_binding['sha256']}.f32"
if not row_archive.exists():
    row_archive.write_bytes(row_path.read_bytes())
result = {
    'schema': 'city-museum-height-runtime-numeric-export-v1',
    'runtime_report': binding(receipt_archive),
    'source_directory': str(review / 'city-input'),
    'decode_receipt': str(review / 'city-triangles/city-source-decode.json'),
    'cached_triangles': str(review / 'city-triangles/near1860-triangles.f64'),
    'meshopt_decoder': str(project / 'vendor/meshopt_decoder.module.js'),
    'possible_owner_indices': binding(review / 'height-fix-history/possible-owner-indices.json'),
    'preflight': binding(preflight),
    'rows': {
        **binding(row_archive),
        'count': runtime['data_payload']['rows'],
        'stride': runtime['data_payload']['columns'],
        'byte_order': 'little-endian',
    },
    'added_row_ranges': [
        {'id': ident, 'first': 258 + i * 2, 'count': 2}
        for i, ident in enumerate(runtime['height_clip_ids'])
    ],
    'source_transform': {
        'macro_id': transform['macro_id'],
        'height_reference': transform['height_reference'],
        'scene_origin': transform['scene_origin'],
        'matrix_column_major_f64': transform['model_matrix_double'],
        'matrix_column_major_f32': transform['model_matrix_float32'],
        'near_copies_far_transform': transform['near_inherits_far_matrix'],
        'matrix_observation': (
            'Runtime receipt executes actual frozen production prepareCityObject with the real macro anchor '
            'and exports sourceGroup.matrixWorld; near inherits the far matrix. '
            f"The bound runtime receipt explicitly records private_preflight={runtime['private_preflight']}."
        ),
    },
    'bindings': [{**r, 'file': str(project / r['file'])} for r in runtime['bindings']],
}
assert result['rows']['sha256'] == runtime['data_payload']['sha256']
if output.exists():
    old = output.read_bytes()
    old_hash = hashlib.sha256(old).hexdigest()
    archive = output.with_name(f'{output.stem}-before-{old_hash[:12]}{output.suffix}')
    if not archive.exists():
        archive.write_bytes(old)
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'prepared': True, 'runtime_private_preflight': runtime['private_preflight'],
                  'rows_sha256': result['rows']['sha256'], 'runtime_receipt_sha256': result['runtime_report']['sha256']}))
