"""Read-only independent Blender reopen and native/raw FLOAT32 triangle check.

Run: blender -b FINAL.blend -t 1 --python-exit-code 1 --python check-native.py
     -- FINAL-raw.glb output.json
This script never saves or edits the native asset.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np

raw_path, output_path = map(Path, sys.argv[sys.argv.index('--') + 1:])
native_path = Path(bpy.data.filepath)
native_before = native_path.read_bytes()
raw_bytes = raw_path.read_bytes()
raw_sha = hashlib.sha256(raw_bytes).hexdigest()
assert struct.unpack_from('<4sII', raw_bytes) == (b'glTF', 2, len(raw_bytes))
json_size, json_kind = struct.unpack_from('<II', raw_bytes, 12)
assert json_kind == 0x4E4F534A
document = json.loads(raw_bytes[20:20 + json_size])
binary_size, binary_kind = struct.unpack_from('<II', raw_bytes, 20 + json_size)
assert binary_kind == 0x004E4942
binary = raw_bytes[28 + json_size:]
assert len(binary) == binary_size
assert not document.get('images') and not document.get('textures')


def accessor(index):
    record = document['accessors'][index]
    view = document['bufferViews'][record['bufferView']]
    assert not view.get('extensions') and not record.get('normalized') and not record.get('sparse')
    dtype = {5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[record['componentType']]
    components = {'SCALAR': 1, 'VEC3': 3}[record['type']]
    size = np.dtype(dtype).itemsize
    start = view.get('byteOffset', 0) + record.get('byteOffset', 0)
    values = np.ndarray((record['count'], components), dtype=dtype, buffer=binary,
                        offset=start, strides=(view.get('byteStride', components * size), size)).copy()
    return values[:, 0] if components == 1 else values


def signatures(triangles):
    triangles = np.asarray(triangles, dtype='<f4').copy()
    assert np.isfinite(triangles).all()
    triangles[triangles == 0] = 0  # Normalize signed zero only.
    rows = []
    for triangle in triangles:
        rotations = [np.roll(triangle, shift, axis=0).tobytes() for shift in range(3)]
        rows.append(min(rotations))
    return hashlib.sha256(b''.join(sorted(rows))).hexdigest()


def node_matrix(node):
    if 'matrix' in node:
        assert all(key not in node for key in ['translation', 'rotation', 'scale'])
        return np.asarray(node['matrix'], dtype=float).reshape(4, 4).T
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    assert abs(x*x+y*y+z*z+w*w-1) < 1e-5
    matrix = np.eye(4)
    matrix[:3, :3] = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                      [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                      [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    matrix[:3, :3] *= np.asarray(node.get('scale', [1, 1, 1]))
    matrix[:3, 3] = node.get('translation', [0, 0, 0])
    return matrix


raw_groups = {}
raw_nodes = []


def visit_node(index, parent, ancestors):
    assert index not in ancestors
    node = document['nodes'][index]
    world = parent @ node_matrix(node)
    assert np.isfinite(world).all()
    raw_nodes.append({'node': index, 'world_matrix': world.tolist()})
    if 'mesh' in node:
        for primitive in document['meshes'][node['mesh']]['primitives']:
            assert primitive.get('mode', 4) == 4
            vertices = accessor(primitive['attributes']['POSITION']).astype(float)
            vertices = vertices @ world[:3, :3].T + world[:3, 3]
            faces = accessor(primitive['indices']).reshape(-1, 3)
            material = document['materials'][primitive['material']]['name']
            raw_groups.setdefault(material, []).append(vertices[faces])
    for child in node.get('children', []):
        visit_node(child, world, ancestors | {index})


for root in document['scenes'][document.get('scene', 0)]['nodes']:
    visit_node(root, np.eye(4), set())
raw_groups = {material: np.concatenate(values) for material, values in raw_groups.items()}

scene = bpy.context.scene
assert scene['candidate_id'] == 'yangpu-jiangwan-gymnasium'
assert json.loads(scene['candidate_metadata_json']) == document['extras']
assert not bpy.data.libraries
assert not [image for image in bpy.data.images if image.type not in {'RENDER_RESULT', 'COMPOSITING'}]
assert not [(material.name, node.name) for material in bpy.data.materials if material.use_nodes
            for node in material.node_tree.nodes if node.type == 'TEX_IMAGE']
names = list(scene['model_mesh_names'])
assert len(names) == len(set(names))
native_groups = {}
matrices = {}
for name in names:
    obj = bpy.data.objects[name]
    assert obj.type == 'MESH' and len(obj.modifiers) == 0
    assert obj['source_raw_sha256'] == raw_sha
    matrix = np.asarray(obj.matrix_world, dtype=np.float64)
    matrices[name] = matrix.tolist()
    points = np.asarray([tuple(vertex.co) for vertex in obj.data.vertices], dtype=np.float64)
    world = points @ matrix[:3, :3].T + matrix[:3, 3]
    glb = world[:, [0, 2, 1]] * np.array([1, 1, -1])
    for face in obj.data.polygons:
        assert len(face.vertices) == 3
        material = obj.data.materials[face.material_index].name
        native_groups.setdefault(material, []).append(glb[list(face.vertices)])
assert set(native_groups) == set(raw_groups)
checks = []
for material, triangles in raw_groups.items():
    actual = np.asarray(native_groups[material], dtype='<f4')
    assert len(actual) == len(triangles)
    expected_digest = signatures(triangles)
    actual_digest = signatures(actual)
    assert actual_digest == expected_digest, material
    checks.append({'material': material, 'triangles': len(actual),
                   'exact_oriented_float32_digest': actual_digest})
assert hashlib.sha256(native_path.read_bytes()).hexdigest() == hashlib.sha256(native_before).hexdigest()
report = {
    'schema': 'jiangwan-gymnasium-independent-native-reopen-v1',
    'passed': True, 'private_only': False,
    'method': 'Reviewer independently reads raw GLB accessors and reopened Blender model mesh polygons, converts native world coordinates back to GLB axes, and compares oriented FLOAT32 triangle multisets by material without coordinate rounding. Preview ground/camera/lights excluded by explicit model mesh names.',
    'native': {'file': str(native_path), 'bytes': len(native_before),
               'sha256': hashlib.sha256(native_before).hexdigest()},
    'raw': {'file': str(raw_path), 'bytes': len(raw_bytes), 'sha256': raw_sha},
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'blender': bpy.app.version_string,
    'model_mesh_names': names, 'model_world_matrices': matrices,
    'triangles': sum(row['triangles'] for row in checks),
    'material_checks': checks,
    'native_asset_modified': False,
    'linked_libraries_or_texture_images': False,
    'model_metadata_matches_raw': True, 'raw_scene_nodes': raw_nodes,
}
output_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': True, 'triangles': report['triangles'], 'native': report['native']}))
