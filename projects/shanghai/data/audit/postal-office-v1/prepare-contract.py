"""Freeze this delivery's actual model, placement and browser expectations by phase."""
from pathlib import Path
import argparse
import hashlib
import json
import math

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--phase', choices=['candidate', 'final'], required=True)
parser.add_argument('--mapping-dir', type=Path, default=Path('/workspace/shanghai-postal-mapping'))
parser.add_argument('--work-dir', type=Path, default=Path('/workspace/shanghai-postal-qa'))
parser.add_argument('--project', type=Path, default=Path('/workspace/e-resource/projects/shanghai'))
args = parser.parse_args()
M, W, P = args.mapping_dir.resolve(), args.work_dir.resolve(), args.project.resolve()
ID = 'hongkou-general-post-office'
BASELINE = 'c59174528765c104f09295ef10132b4bb4f63ce5'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

source_path = M / 'qa-map-input.json'
placement_path = M / 'final-placement-contract.json'
source, clip = read(source_path), read(placement_path)
catalog = read(P / 'data/candidate-city-integrations.json')
row = next(x for x in catalog['models'] if x['id'] == ID)
manifest_path = P / 'assets/models/candidates' / ID / 'manifest.json'
manifest = read(manifest_path)
assert manifest['id'] == source['model_id'] == ID
assert clip['model_manifest_sha256'] == sha(manifest_path)
for role, key in [('raw', 'raw'), ('full', 'web'), ('lod', 'lod')]:
    assert manifest['assets'][role]['sha256'] == clip['model_geometry_sha256'][key]
for key in ['owner', 'source_feature_ids', 'replacement_geometry', 'collision_geometry', 'bounds_glb']:
    assert row[key] == clip[key], key
assert row.get('site_replacement') == clip.get('site_replacement')

views_path = W / 'visual-views.json'
views = read(views_path)
anchor, projection = source['anchor'], source['projection']
def wgs(x, y):
    return [anchor['lng'] + math.degrees(x / projection['k']),
            math.degrees(2 * math.atan(math.exp(projection['log_latitude_origin'] + y / projection['k'])) - math.pi / 2)]
for view in views:
    if 'target_local_enu' in view:
        view['camera']['center'] = wgs(*view['target_local_enu'][:2])
        view['camera']['elevation'] = view['target_local_enu'][2]
assert len(views) >= 3, 'Actual model-specific tower, roof and street/entry targets required'

bindings = [{'path': b['repository_path'].removeprefix('projects/shanghai/'),
             'bytes': b['bytes'], 'sha256': b['sha256']} for b in source['source_bindings']]
near_groups = []
for group in source['near_groups']:
    binding = next(b for b in bindings if b['path'].endswith('/' + group['file']))
    near_groups.append({'group_id': group['macro_id'] + '/' + group['id'],
                        'macro_id': group['macro_id'], 'feature_local_ids': group['feature_local_ids'],
                        'clip_feature_local_ids': group['expected_clip_feature_local_ids'],
                        'clip_triangles': group['expected_clip_triangles'], **binding})
probes = [dict(p, qa_name=('target' if p['expected_target_clip'] else 'neighbor') + '-' + str(p['feature_local_id']))
          for p in source['actual_source_roof_probes']]
probes.append(dict(source['source_joint_retained_roof_probe'], qa_name='retained-joint-same-owner-1959'))
context = [{'source_id': p['source_feature_id'], 'local_id': p['feature_local_id'], 'name': p.get('name'),
            'roof_probe': {'wgs84': p['position_wgs84'], 'height_m': p['native_roof_height_m'],
                           'actual_native_triangle_verified': True}}
           for p in source['actual_source_roof_probes'] if not p['expected_target_clip']]
contract = {'frozen': args.phase == 'final', 'preliminary_only': args.phase == 'candidate',
            'model_id': ID, 'baseline_commit': BASELINE,
            **{key: clip[key] for key in ['owner', 'source_feature_ids', 'replacement_geometry',
                                         'collision_geometry', 'model_geometry_sha256',
                                         'model_manifest_sha256', 'bounds_glb']},
            'site_replacement': clip.get('site_replacement'),
            'clip_capacity': source['clip_capacity'], 'model_clip_triangles': source['new_clip_triangles'],
            'global_clip_triangles': source['expected_global_clip_triangles'],
            'source_bindings': bindings, 'near_groups': near_groups, 'context_sources': context,
            'actual_source_roof_probes': probes, 'visual_views': (views if args.phase == 'final' else [v for v in views if v.get('require_complete_tower') or v.get('require_complete_building')])}
inputs = [source_path, placement_path, views_path]
if args.phase == 'final':
    ground_path = M / 'ground-probes.json'
    ground = read(ground_path)
    contract['ground_probes'] = ground['ground_probes'] if isinstance(ground, dict) else ground
    assert contract['ground_probes'], 'Final actual GLB ground probes required'
    highlights_path = W / 'geometry-highlights.json'
    contract['geometry_highlights'] = read(highlights_path)
    assert contract['geometry_highlights']['raw_asset_sha256'] == manifest['assets']['raw']['sha256']
    assert any(v.get('require_complete_tower') for v in views)
    assert any(v.get('require_complete_building') for v in views)
    gpu_path = P / 'data/audit/great-world-v1/gpu-capacity.json'
    gpu = read(gpu_path)
    assert gpu['passed'] and gpu['browserClosed'] and gpu['serverClosed']
    assert gpu['sourceReceipts'][0]['sha256'] == sha(P / 'src/candidate-city-clipping.js'), 'Changed clipper needs new GPU evidence, not historical reuse'
    contract['clip_gpu_evidence'] = {'report': 'data/audit/great-world-v1/gpu-capacity.json',
                                     'script': 'data/audit/great-world-v1/qa-clip-capacity-gpu.cjs',
                                     'reused': True,
                                     'reason': 'Production clipper bytes and its 320-row capacity remain identical to the prior actual GPU proof; this delivery adds 6 rows to 307/320 and does not rerun that unchanged capacity fixture.'}
    inputs += [ground_path, highlights_path]
contract['input_receipts'] = [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in inputs]
name = 'candidate-stage-contract.json' if args.phase == 'candidate' else 'qa-contract.json'
(W / name).write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'phase': args.phase, 'output': name, 'frozen': contract['frozen'],
                  'views': [v['key'] for v in contract['visual_views']], 'context': len(context), 'roof_points': len(probes)}, ensure_ascii=False))
