"""Independent actual raw GLB reader. No author modules or geometry generation.

Decoded delivery adapters may construct the same Asset/Part interface, but must
bind their own decoded arrays and semantic mapping to actual delivery bytes.
"""
from dataclasses import dataclass
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, struct
import numpy as np


def require(ok, message):
    if not ok:
        raise ValueError(message)


def filemeta(path):
    path = Path(path)
    data = path.read_bytes()
    return {'file': str(path.resolve()), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def oriented_position_hash(triangles):
    """Exact actual positions; cyclic vertex rotation preserves orientation.

    Sorting preserves triangle multiplicity. Signed zero is normalized because
    it denotes the same position; no nonzero coordinate is rounded or snapped.
    """
    q = np.asarray(triangles, dtype='<f8').copy()
    require(q.ndim == 3 and q.shape[1:] == (3, 3) and np.isfinite(q).all(),
            'Invalid actual triangle array')
    q[q == 0] = 0.
    first = np.zeros(len(q), dtype=int)
    rows = np.arange(len(q))
    for vertex in [1, 2]:
        a, b = q[:, vertex], q[rows, first]
        less = ((a[:, 0] < b[:, 0]) |
                ((a[:, 0] == b[:, 0]) & (a[:, 1] < b[:, 1])) |
                ((a[:, 0] == b[:, 0]) & (a[:, 1] == b[:, 1]) & (a[:, 2] < b[:, 2])))
        first[less] = vertex
    q = q[rows[:, None], (first[:, None] + np.arange(3)) % 3].reshape(-1, 9)
    q = q[np.lexsort(tuple(q[:, i] for i in range(8, -1, -1)))]
    return hashlib.sha256(q.astype('<f8', copy=False).tobytes()).hexdigest()


@dataclass
class Part:
    key: str
    label: str
    material: str
    triangles_enu: np.ndarray
    normals_enu: np.ndarray
    primitive_index: int
    first_triangle: int


@dataclass
class Asset:
    identity: dict
    parts: list
    materials: dict
    extras: dict

    def select(self, selector):
        require(isinstance(selector, dict), 'Selector must be an object')
        allowed = {'key', 'label', 'prefix', 'material', 'expected_count'}
        require(not set(selector) - allowed, 'Unknown selector fields')
        require(any(k in selector for k in ['key', 'label', 'prefix']),
                'Unbounded selectors are forbidden')
        result = [p for p in self.parts
                  if ('key' not in selector or p.key == selector['key'])
                  and ('label' not in selector or p.label == selector['label'])
                  and ('prefix' not in selector or p.label.startswith(selector['prefix']))
                  and ('material' not in selector or p.material == selector['material'])]
        require(result, 'No actual part matches ' + repr(selector))
        require('expected_count' in selector, 'Selector must declare expected_count')
        require(len(result) == selector['expected_count'],
                f'Actual count {len(result)} differs for {selector}')
        return result


def verify_source_freeze(path):
    path = Path(path).resolve()
    lock = json.loads(path.read_bytes())
    require(lock.get('files'), 'Source freeze has no files')
    for row in lock['files']:
        relative = row.get('path', row.get('file'))
        require(relative, 'Source freeze row has no path')
        p = Path(relative)
        p = p if p.is_absolute() else path.parent / p
        actual = filemeta(p)
        require(actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes'],
                'Frozen author input changed: ' + str(p))
    return filemeta(path)


def load_raw(path, geometry_path=None):
    path = Path(path).resolve()
    identity = filemeta(path)
    require(identity['bytes'] < 100_000_000, 'Raw is not below100MB')
    data = path.read_bytes()
    require(len(data) >= 28 and struct.unpack_from('<4sII', data) ==
            (b'glTF', 2, len(data)), 'Invalid GLB header')
    chunks, cursor = [], 12
    while cursor < len(data):
        length, kind = struct.unpack_from('<II', data, cursor)
        cursor += 8
        require(cursor + length <= len(data), 'Chunk exceeds actual GLB')
        chunks.append((kind, data[cursor:cursor+length]))
        cursor += length
    require([x[0] for x in chunks] == [0x4e4f534a, 0x004e4942],
            'Raw requires JSON and a single BIN')
    doc, binary = json.loads(chunks[0][1]), chunks[1][1]
    geometry_path = Path(geometry_path or path.with_suffix('.geometry.json'))
    side = json.loads(geometry_path.read_bytes())
    require(side['sha256'] == identity['sha256'] and side['bytes'] == len(data),
            'Actual raw/sidecar hash binding differs')
    require(len(doc.get('nodes', [])) == len(doc.get('meshes', [])) == 1,
            'Raw adapter expects one untransformed mesh/node')
    node = doc['nodes'][0]
    require(node.get('mesh') == 0 and not any(k in node for k in
            ['matrix', 'translation', 'rotation', 'scale', 'skin', 'extensions']),
            'Unhandled transform/skin/instance in raw')
    require(len(doc.get('buffers', [])) == 1 and 'uri' not in doc['buffers'][0],
            'External raw buffer unsupported')
    require(not doc.get('images') and not doc.get('textures'),
            'Unexpected image/texture payload; explicit scope review needed')
    require(doc.get('asset', {}).get('copyright'), 'Missing attribution')
    widths = {'SCALAR': 1, 'VEC3': 3}
    types = {5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}

    def accessor(index, expected_type):
        a = doc['accessors'][index]
        require(a['type'] == expected_type and 'sparse' not in a and
                not a.get('normalized'), 'Unexpected raw accessor format')
        require(a['componentType'] in types, 'Unsupported raw component type')
        v = doc['bufferViews'][a['bufferView']]
        require(v.get('buffer', 0) == 0 and not v.get('extensions'),
                'Compressed raw accessor requires delivery decoder')
        dt, width, count = np.dtype(types[a['componentType']]), widths[a['type']], a['count']
        offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = v.get('byteStride', dt.itemsize * width)
        needbytes = 0 if count == 0 else (count - 1) * stride + dt.itemsize * width
        require(count > 0 and stride >= dt.itemsize * width and
                a.get('byteOffset', 0) + needbytes <= v['byteLength'] and
                offset + needbytes <= len(binary), 'Accessor exceeds its buffer view')
        if expected_type == 'VEC3':
            require(a['componentType'] == 5126, 'Raw coordinates/normals must be Float32')
        return np.ndarray((count, width), dt, binary, offset, (stride, dt.itemsize))

    summary = defaultdict(list)
    for row in side['part_summary']:
        summary[row['material']].append(row)
    side_ranges = defaultdict(list)
    for row in side.get('actual_serialized_part_ranges', []):
        side_ranges[row['primitive_index']].append(row)
    parts, materials, occurrences = [], {}, Counter()
    for pi, primitive in enumerate(doc['meshes'][0]['primitives']):
        require(primitive.get('mode', 4) == 4, 'Nontriangle raw primitive')
        require(not primitive.get('extensions') and not primitive.get('targets'),
                'Compressed/morphed primitive unsupported by raw reader')
        material = doc['materials'][primitive['material']]
        name = material['name']
        require(name not in materials, 'Multiple raw primitives with same material need explicit adapter')
        materials[name] = material
        x = accessor(primitive['attributes']['POSITION'], 'VEC3')
        n = accessor(primitive['attributes']['NORMAL'], 'VEC3')
        indices = accessor(primitive['indices'], 'SCALAR').ravel()
        require(len(indices) % 3 == 0 and len(x) == len(n) and indices.max() < len(x),
                'Invalid raw indices or normals')
        require(np.isfinite(x).all() and np.isfinite(n).all(), 'Nonfinite raw attributes')
        triangles = indices.reshape(-1, 3)
        embedded = primitive.get('extras', {}).get('semanticParts', [])
        rows, cursor = [], 0
        for sr in summary[name]:
            rows.append({'label': sr['label'], 'first_triangle': cursor,
                         'triangle_count': sr['triangles']})
            cursor += sr['triangles']
        require(cursor == len(triangles), 'Part summary does not cover actual primitive')
        if embedded:
            require(len(embedded) == len(rows), 'Embedded semantic count differs')
            for actual, expected in zip(embedded, rows):
                require(actual['label'] == expected['label'] and
                        actual['firstIndex'] == expected['first_triangle'] * 3 and
                        actual['indexCount'] == expected['triangle_count'] * 3,
                        'Embedded actual semantic ranges differ from sidecar')
        if side_ranges:
            require(len(side_ranges[pi]) == len(rows), 'Serialized range count differs')
            for actual, expected in zip(side_ranges[pi], rows):
                require(actual['material'] == name and all(actual[k] == expected[k]
                        for k in ['label', 'first_triangle', 'triangle_count']),
                        'Serialized actual ranges differ from summary')
        require(embedded or side_ranges, 'Modern raw requires explicit serialized semantic ranges')
        for row in rows:
            start, count, label = row['first_triangle'], row['triangle_count'], row['label']
            require(count > 0, 'Empty declared part')
            ids = triangles[start:start+count]
            ordinal = occurrences[(label, name)]
            occurrences[(label, name)] += 1
            key = json.dumps([label, name, ordinal], ensure_ascii=False, separators=(',', ':'))
            # Proper rotation glTF[east,up,south] -> ENU[east,north,up].
            tr = x[ids].astype(np.float64)[:, :, [0, 2, 1]] * [1, -1, 1]
            no = n[ids].astype(np.float64)[:, :, [0, 2, 1]] * [1, -1, 1]
            parts.append(Part(key, label, name, tr, no, pi, start))
    require(len(parts) == side['parts'] and sum(len(p.triangles_enu) for p in parts) ==
            side['triangles'], 'Actual global counts differ')
    return Asset({'raw': identity, 'part_manifest': filemeta(geometry_path),
                  'representation': 'actual Float32 raw GLB, expanded without coordinate welding'},
                 parts, materials, doc.get('extras', {}))
