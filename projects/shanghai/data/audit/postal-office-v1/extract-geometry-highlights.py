"""Read final serialized raw geometry for tower framing; never run the model builder."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import numpy as np
import trimesh

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project', type=Path, default=Path('/workspace/e-resource/projects/shanghai'))
parser.add_argument('--author-features', type=Path, required=True)
parser.add_argument('--output', type=Path, default=Path('/workspace/shanghai-postal-qa/geometry-highlights.json'))
args = parser.parse_args()
ID = 'hongkou-general-post-office'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest_path = args.project / 'assets/models/candidates' / ID / 'manifest.json'
manifest = json.loads(manifest_path.read_text())
asset = manifest_path.parent / manifest['assets']['raw']['file']
assert asset.stat().st_size == manifest['assets']['raw']['bytes']
assert sha(asset) == manifest['assets']['raw']['sha256']
raw = asset.read_bytes()
assert raw[:4] == b'glTF' and struct.unpack_from('<I', raw, 4)[0] == 2
size = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + size])
assert doc['extras']['id'] == ID
assert len(doc['scenes']) == 1 and doc['scenes'][0]['nodes'] == [0]
assert len(doc['nodes']) == 1 and doc['nodes'][0].get('mesh') == 0
assert not any(k in doc['nodes'][0] for k in ['translation', 'rotation', 'scale', 'matrix', 'children', 'extensions'])
assert not any('EXT_meshopt_compression' in v.get('extensions', {}) for v in doc.get('bufferViews', []))
scene = trimesh.load(asset, force='scene', process=False)
points = np.concatenate([mesh.vertices for mesh in scene.geometry.values()])
top = float(points[:, 1].max())
highest = np.unique(points[np.abs(points[:, 1] - top) < 1e-6], axis=0)
assert 1 <= len(highest) <= 100
features = json.loads(args.author_features.read_text())
tower = features['features']['tower']
bounds = tower['actual_component_bounds_enu_m']
margin = .0001
envelope = {'x': [bounds['min'][0] - margin, bounds['max'][0] + margin],
            'y': [bounds['min'][2] - margin, bounds['max'][2] + margin],
            'z': [-bounds['max'][1] - margin, -bounds['min'][1] + margin]}
for point in highest:
    assert all(envelope[axis][0] <= point[index] <= envelope[axis][1]
               for index, axis in enumerate(['x', 'y', 'z']))
report = {'model_id': ID, 'raw_asset_sha256': sha(asset),
          'manifest_sha256': sha(manifest_path), 'raw_asset_bytes': asset.stat().st_size,
          'highest_vertices_glb': highest.tolist(), 'actual_maximum_glb_y_m': top,
          'tower_glb_bounds': envelope, 'tower_center_enu': tower['center_enu_m'],
          'serialized_model_bounds_glb': {'min': points.min(axis=0).tolist(), 'max': points.max(axis=0).tolist()},
          'source': {'raw_file': asset.relative_to(args.project).as_posix(),
                     'author_features_file': args.author_features.name, 'author_features_sha256': sha(args.author_features),
                     'author_tower_component_bounds_enu_m': bounds,
                     'method': 'Highest vertices independently extracted from actual final uncompressed raw GLB. Tower envelope comes from author-measured component geometry before serialization and is conservatively padded 0.0001m for Float32 rounding; it is not a separate reconstruction from photos.',
                     'scene_identity_and_no_transforms_verified': True},
          'script_sha256': sha(Path(__file__)),
          'dependencies': {'numpy': np.__version__, 'trimesh': trimesh.__version__}}
args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'actual_maximum_y_m': top, 'highest_vertex_count': len(highest),
                  'raw_sha256': report['raw_asset_sha256']}))
