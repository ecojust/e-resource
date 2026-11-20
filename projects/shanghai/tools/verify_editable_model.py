"""Run inside Blender to compare the native meshes to the serialized raw GLB."""
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np


blend, raw, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
project = Path(__file__).resolve().parents[1]
read = runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']


def surface_hash(triangles):
    # Canonicalize oriented vertex cycles and triangle ordering, keeping float32 precision.
    v = np.asarray(triangles, dtype='<f4').copy()
    v[v == 0] = 0  # identical coordinates may have two IEEE zero representations
    starts = np.lexsort((v[:, :, 2], v[:, :, 1], v[:, :, 0]), axis=1)[:, 0]
    v = v[np.arange(len(v))[:, None], (starts[:, None] + np.arange(3)) % 3]
    rows = np.ascontiguousarray(v.reshape(-1,9)).view(np.dtype((np.void, 36))).reshape(-1)
    return hashlib.sha256(np.sort(rows).tobytes()).hexdigest()


bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()))
by_material = {}
object_names = []
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    mesh = obj.data
    assert all(len(face.vertices) == 3 for face in mesh.polygons)
    indices = np.empty(len(mesh.polygons) * 3, dtype=np.int32)
    mesh.polygons.foreach_get('vertices', indices)
    positions = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', positions)
    world = np.array(obj.matrix_world)
    vertices = positions.reshape(-1, 3) @ world[:3, :3].T + world[:3, 3]
    triangles = vertices[indices.reshape(-1,3)]
    slots = np.empty(len(mesh.polygons), dtype=np.int32)
    mesh.polygons.foreach_get('material_index', slots)
    for slot in np.unique(slots):
        name = mesh.materials[slot].name
        by_material.setdefault(name, []).append(triangles[slots == slot])
    object_names.append(obj.name)
native = {name: surface_hash(np.concatenate(parts)) for name,parts in by_material.items()}
triangles, material_ids, materials, _ = read(raw)
expected = {materials[i]:surface_hash(triangles[material_ids == i]) for i in np.unique(material_ids)}
assert native == expected, 'Blend and raw GLB differ in material assignment, positions or oriented triangles'
report = {'blender':bpy.app.version_string,'mesh_count':len(object_names),'materials':len(native),
          'triangles':len(triangles),'surface_sha256_by_material':native,'match_raw':True}
output.write_text(json.dumps(report,indent=2)+'\n')
