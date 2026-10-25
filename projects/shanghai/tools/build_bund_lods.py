#!/usr/bin/env python3
"""Build and verify distant Bund GLBs without modifying close-up or native assets.

Requires Python/numpy and gltfpack (npm package or native executable). Example:
  python tools/build_bund_lods.py --gltfpack /path/to/gltfpack
  python tools/build_bund_lods.py --verify-only

Every candidate is checked before publication. A rotated source is measured from
its transformed vertices, not the corners of its conservative local bounding box.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
import numpy as np

MAX_BYTES = 100_000_000
MAX_BOUNDS_CHANGE = .35
SWITCH_OUT = 400
SWITCH_IN = 300
LOD_KEYS = ('lod_model', 'lod_sha256', 'lod_bytes', 'lod_triangles',
            'lod_switch_out_m', 'lod_switch_in_m')
# Lower error first; an unchanged triangle budget is a valid preservation fallback.
ATTEMPTS = ((.35, .002, True), (.35, .0005, True), (.60, .0001, False), (1., 0., False))
DTYPES = {5120: np.dtype('i1'), 5121: np.dtype('u1'), 5122: np.dtype('<i2'),
          5123: np.dtype('<u2'), 5125: np.dtype('<u4'), 5126: np.dtype('<f4')}
COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_glb(path):
    data = path.read_bytes()
    if len(data) < 20 or struct.unpack_from('<4sII', data) != (b'glTF', 2, len(data)):
        raise ValueError(f'Invalid GLB 2.0 header: {path}')
    offset, doc, binary = 12, None, None
    while offset < len(data):
        size, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if offset + size > len(data):
            raise ValueError(f'Truncated GLB chunk: {path}')
        chunk = data[offset:offset + size]
        if kind == 0x4E4F534A:
            doc = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        offset += size
    if doc is None or binary is None:
        raise ValueError(f'Missing GLB JSON/BIN chunk: {path}')
    if any(item.get('uri') for item in doc.get('buffers', []) + doc.get('images', [])):
        raise ValueError(f'External GLB dependency: {path}')
    return doc, binary


def accessor_values(doc, binary, index):
    accessor = doc['accessors'][index]
    if 'sparse' in accessor:
        raise ValueError('Sparse source accessors need an explicit decoder')
    view = doc['bufferViews'][accessor['bufferView']]
    if any(ext in view.get('extensions', {}) for ext in ('EXT_meshopt_compression', 'KHR_meshopt_compression')):
        raise ValueError('Compressed accessor needs meshopt decoding')
    if view.get('buffer', 0) != 0:
        raise ValueError('Expected source vertices in the embedded GLB buffer')
    dtype = DTYPES[accessor['componentType']]
    width = COMPONENTS[accessor['type']]
    stride = view.get('byteStride', width * dtype.itemsize)
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    result = np.ndarray((accessor['count'], width), dtype=dtype, buffer=binary,
                        offset=offset, strides=(stride, dtype.itemsize))
    if accessor.get('normalized'):
        limits = np.iinfo(dtype)
        result = result.astype(np.float64) / limits.max
        if limits.min < 0:
            result = np.maximum(result, -1)
    return result


def node_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=np.float64).reshape(4, 4).T
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    matrix = np.eye(4)
    matrix[:3, :3] = np.array([
        [1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
        [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
        [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)],
    ]) @ np.diag(node.get('scale', [1, 1, 1]))
    matrix[:3, 3] = node.get('translation', [0, 0, 0])
    return matrix


def measure(path, source=False):
    """Exact source vertices; axis-aligned compressed output accessor extrema.

    Transforming a rotated source AABB overestimates its silhouette: for bund23
    the old method added 0.746 m even to an unsimplified web model. We transform
    the actual referenced source vertices. Compressed outputs may use accessor
    extrema only when the final transform has no rotation/shear, making this
    equivalent for their extrema; other output transforms fail explicitly.
    """
    doc, binary = read_glb(path)
    low, high = np.full(3, np.inf), np.full(3, -np.inf)
    triangles, primitives = 0, 0

    def visit(index, parent):
        nonlocal low, high, triangles, primitives
        node = doc['nodes'][index]
        if 'skin' in node:
            raise ValueError('Skinned architecture needs evaluated pose bounds')
        matrix = parent @ node_matrix(node)
        if 'EXT_mesh_gpu_instancing' in node.get('extensions', {}):
            raise ValueError('Instanced output needs expanded per-instance bounds')
        if 'mesh' in node:
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                if primitive.get('targets'):
                    raise ValueError('Morph-target architecture needs evaluated bounds')
                accessor_id = primitive['attributes']['POSITION']
                accessor = doc['accessors'][accessor_id]
                if 'sparse' in accessor:
                    raise ValueError('Sparse position accessor needs explicit decoding')
                count = doc['accessors'][primitive['indices']]['count'] if 'indices' in primitive else accessor['count']
                if primitive.get('mode', 4) != 4 or count % 3:
                    raise ValueError('Expected triangle-list architecture meshes')
                triangles += count // 3
                primitives += 1
                if source:
                    positions = accessor_values(doc, binary, accessor_id)
                    if 'indices' in primitive:
                        indices = accessor_values(doc, binary, primitive['indices']).reshape(-1)
                        positions = positions[indices]
                else:
                    linear = matrix[:3, :3]
                    if not np.allclose(linear, np.diag(np.diag(linear)), atol=1e-10):
                        raise ValueError('Output has rotated/sheared compressed positions; decode before validating bounds')
                    minimum, maximum = np.array(accessor['min'], float), np.array(accessor['max'], float)
                    if accessor.get('normalized'):
                        dtype = DTYPES[accessor['componentType']]
                        limits = np.iinfo(dtype)
                        minimum, maximum = minimum / limits.max, maximum / limits.max
                        if limits.min < 0:
                            minimum, maximum = np.maximum(minimum, -1), np.maximum(maximum, -1)
                    positions = np.array([[x, y, z] for x in (minimum[0], maximum[0])
                                          for y in (minimum[1], maximum[1]) for z in (minimum[2], maximum[2])])
                transformed = np.asarray(positions, dtype=np.float64) @ matrix[:3, :3].T + matrix[:3, 3]
                if not np.isfinite(transformed).all():
                    raise ValueError(f'Non-finite model vertices: {path}')
                low, high = np.minimum(low, transformed.min(0)), np.maximum(high, transformed.max(0))
        for child in node.get('children', []):
            visit(child, matrix)

    for index in doc['scenes'][doc.get('scene', 0)]['nodes']:
        visit(index, np.eye(4))
    if not triangles or not np.isfinite([low, high]).all():
        raise ValueError(f'Empty/invalid architecture: {path}')
    return np.array([low, high]), triangles, primitives


def near_assets(root, buildings):
    result = {}
    for item in buildings:
        for field, expected in (('editable_model', 'raw_sha256'), ('model', 'web_sha256'), ('native_model', 'native_sha256')):
            name = item[field]
            actual = sha256(root / name)
            if actual != item[expected]:
                raise ValueError(f'Close-up/native asset differs from source metadata: {name}')
            result[name] = actual
    return result


def lod_fields(row):
    return dict(zip(LOD_KEYS, (row['model'], row['sha256'], row['bytes'], row['triangles'], SWITCH_OUT, SWITCH_IN)))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def verify(root):
    result = json.loads((root / 'data/bund/lod-v4.json').read_text())
    manifest = json.loads((root / 'data/bund/manifest.json').read_text())
    landmarks = json.loads((root / 'data/landmarks.json').read_text())
    buildings = manifest['buildings']
    snapshots = near_assets(root, buildings)
    if len(result['models']) != len(buildings) or len(buildings) != 10:
        raise ValueError('The LOD release must contain exactly the 10 Bund buildings')
    by_id = {row['candidate_id']: row for row in result['models']}
    if len(by_id) != 10:
        raise ValueError('Duplicate LOD candidate IDs')
    for item in buildings:
        row = by_id[item['candidate_id']]
        path = root / row['model']
        if path.stat().st_size != row['bytes'] or row['bytes'] >= MAX_BYTES or sha256(path) != row['sha256']:
            raise ValueError(f'LOD size/hash mismatch: {path}')
        source_bounds, source_triangles, _ = measure(root / item['editable_model'], source=True)
        output_bounds, triangles, _ = measure(path)
        delta = float(abs(source_bounds - output_bounds).max())
        if delta >= MAX_BOUNDS_CHANGE or triangles != row['triangles'] or source_triangles != row['full_triangles']:
            raise ValueError(f'LOD geometry mismatch: {item["candidate_id"]}')
        if abs(delta - row['maximum_bounds_change_m']) > 1e-9:
            raise ValueError(f'LOD bound statistic mismatch: {item["candidate_id"]}')
        copies = [item, json.loads((root / f'data/bund/models/{item["candidate_id"]}-web.json').read_text())]
        matches = [x for x in landmarks if x['id'] == item['id']]
        if len(matches) != 1:
            raise ValueError(f'Landmark mapping missing/duplicate: {item["id"]}')
        copies += matches
        expected = lod_fields(row)
        for copy in copies:
            if any(copy.get(key) != value for key, value in expected.items()):
                raise ValueError(f'Inconsistent runtime LOD metadata: {item["candidate_id"]}')
        if row['full_model_unchanged_sha256'] != snapshots[item['editable_model']] or row['close_up_web_unchanged_sha256'] != snapshots[item['model']]:
            raise ValueError(f'Close-up preservation hash mismatch: {item["candidate_id"]}')
    return {'verified': True, 'models': len(buildings),
            'lod_bytes': sum(x['bytes'] for x in result['models']),
            'lod_triangles': sum(x['triangles'] for x in result['models']),
            'full_triangles': sum(x['full_triangles'] for x in result['models']),
            'maximum_bounds_change_m': max(x['maximum_bounds_change_m'] for x in result['models']),
            'unchanged_close_up_and_native_files': len(snapshots)}


def build(root, gltfpack):
    manifest_path = root / 'data/bund/manifest.json'
    landmark_path = root / 'data/landmarks.json'
    manifest = json.loads(manifest_path.read_text())
    landmarks = json.loads(landmark_path.read_text())
    buildings = manifest['buildings']
    if len(buildings) != 10 or len({x['candidate_id'] for x in buildings}) != 10:
        raise ValueError('Expected exactly 10 unique Bund architecture records')
    original = near_assets(root, buildings)
    native_lod_dir = root / 'assets/models/bund/lod-v4'
    native_lod_dir.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([gltfpack, '-v'], check=True, capture_output=True, text=True)
    version = (version.stdout + version.stderr).strip()
    rows, updates = [], {}
    with tempfile.TemporaryDirectory(prefix='.bund-lods-', dir=native_lod_dir) as directory:
        temporary = Path(directory)
        for item in buildings:
            ident, source = item['candidate_id'], root / item['editable_model']
            source_bounds, full_triangles, _ = measure(source, source=True)
            staged = temporary / f'{ident}.glb'
            history = []
            for ratio, error, permissive in ATTEMPTS:
                report = temporary / f'{ident}-report.json'
                parameters = ['-cc', '-vp', '16', '-vn', '12', '-km', '-ke']
                if ratio < 1:
                    parameters += ['-si', str(ratio), '-se', str(error)]
                    if permissive:
                        parameters.append('-sp')
                command = [gltfpack, '-i', str(source), '-o', str(staged), *parameters, '-r', str(report)]
                subprocess.run(command, check=True)
                statistics = json.loads(report.read_text())
                output_bounds, triangles, primitives = measure(staged)
                delta = float(abs(source_bounds - output_bounds).max())
                attempt = {'mode': 'simplified' if ratio < 1 else 'compression_only', 'target_triangle_ratio': ratio,
                           'relative_error_limit': error if ratio < 1 else None,
                           'permissive_attribute_simplification': permissive,
                           'parameters': parameters, 'triangles': triangles, 'bytes': staged.stat().st_size,
                           'maximum_bounds_change_m': delta, 'accepted': delta < MAX_BOUNDS_CHANGE}
                history.append(attempt)
                if triangles != statistics['render']['triangleCount']:
                    raise ValueError(f'Render triangle report mismatch: {ident}')
                if staged.stat().st_size >= MAX_BYTES:
                    raise ValueError(f'LOD file exceeds 100 MB: {ident}')
                if attempt['accepted']:
                    break
                print(f'{ident}: bounds change {delta:.6f} m exceeds limit; retrying more conservatively', flush=True)
            else:
                raise ValueError(f'Even compression-only output changed the bounds of {ident}; no outputs published')
            row = {'id': item['id'], 'candidate_id': ident, 'model': f'assets/models/bund/lod-v4/{ident}.glb',
                   'sha256': sha256(staged), 'bytes': staged.stat().st_size, 'triangles': triangles,
                   'full_triangles': full_triangles, 'actual_triangle_ratio': triangles / full_triangles,
                   'draw_primitives': primitives, 'maximum_bounds_change_m': delta,
                   'source_bounds_glb': {'min': source_bounds[0].tolist(), 'max': source_bounds[1].tolist()},
                   'lod_bounds_glb': {'min': output_bounds[0].tolist(), 'max': output_bounds[1].tolist()},
                   'full_model_unchanged_sha256': original[item['editable_model']],
                   'close_up_web_unchanged_sha256': original[item['model']],
                   'native_unchanged_sha256': original[item['native_model']],
                   'switch_out_distance_m': SWITCH_OUT, 'switch_in_distance_m': SWITCH_IN,
                   'generation': attempt, 'attempts': history}
            rows.append(row)
            item.update(lod_fields(row))
            web_path = root / f'data/bund/models/{ident}-web.json'
            web = json.loads(web_path.read_text())
            if web['id'] != item['id']:
                raise ValueError(f'Web record maps to the wrong building: {ident}')
            web.update(lod_fields(row)); updates[web_path] = json_bytes(web)
            matches = [x for x in landmarks if x['id'] == item['id']]
            if len(matches) != 1:
                raise ValueError(f'Landmark mapping missing/duplicate: {item["id"]}')
            matches[0].update(lod_fields(row))
            print(f'{ident}: {triangles:,} triangles, {staged.stat().st_size:,} bytes, bounds change {delta:.6f} m', flush=True)
        if near_assets(root, buildings) != original:
            raise ValueError('A close-up/native model changed during LOD generation')
        result = {'version': 'bund-distant-lod-v4', 'complete': True, 'generator': 'tools/build_bund_lods.py',
                  'gltfpack_version': version, 'maximum_bounds_change_limit_m': MAX_BOUNDS_CHANGE,
                  'source_bounds_method': 'Referenced POSITION vertices transformed through the full node hierarchy',
                  'output_bounds_method': 'Accessor extrema with validated axis-aligned node transforms; supports quantized normalized attributes',
                  'bounds_check_limit': 'Extrema preservation is not a Hausdorff or photographic-accuracy guarantee; distant geometry is simplified.',
                  'close_up_assets_modified': False, 'native_assets_modified': False,
                  'fallback_policy': [{'target_triangle_ratio': r, 'relative_error_limit': e if r < 1 else None,
                                       'permissive_attribute_simplification': p} for r, e, p in ATTEMPTS],
                  'models': rows}
        updates[manifest_path] = json_bytes(manifest)
        updates[landmark_path] = json_bytes(landmarks)
        updates[root / 'data/bund/lod-v4.json'] = json_bytes(result)
        # Publish only after every building passed; each individual file is atomic.
        for row in rows:
            (temporary / f'{row["candidate_id"]}.glb').replace(root / row['model'])
        for path, content in updates.items():
            atomic_write(path, content)
    return verify(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--gltfpack', default='gltfpack', help='gltfpack executable; used only when building')
    parser.add_argument('--verify-only', action='store_true', help='Check all ten GLBs, hashes, bounds and metadata without rewriting files')
    args = parser.parse_args()
    root = args.project.resolve()
    if args.verify_only:
        result = verify(root)
    else:
        gltfpack = shutil.which(args.gltfpack)
        if gltfpack is None:
            parser.error('gltfpack was not found; pass --gltfpack /path/to/gltfpack')
        result = build(root, gltfpack)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
