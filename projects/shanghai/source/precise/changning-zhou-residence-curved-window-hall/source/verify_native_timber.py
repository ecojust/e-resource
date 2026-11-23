"""Compare the reopened texture, its shader connection, and every shaft UV with the raw GLB."""
import hashlib
import json
from pathlib import Path
import sys

import bpy

_, raw, report_file = map(Path, sys.argv[sys.argv.index('--') + 1:])
sys.path.insert(0, str(Path(__file__).resolve().parent))
from native_timber_source import timber_source

faces, corner_count, texture_sha256 = timber_source(raw)

material_name = 'Fluted stained timber'
material = bpy.data.materials[material_name]
base_color = material.node_tree.nodes['Principled BSDF'].inputs['Base Color']
image = base_color.links[0].from_node.image
assert hashlib.sha256(image.packed_file.data).hexdigest() == texture_sha256

tested = 0
mesh_count = 0
max_error = 0.
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH' or material_name not in obj.data.materials:
        continue
    mesh_count += 1
    mesh = obj.data
    uv = mesh.uv_layers.active.data
    for face in mesh.polygons:
        if mesh.materials[face.material_index] != material:
            continue
        corners = []
        for loop in face.loop_indices:
            x, y, z = mesh.vertices[mesh.loops[loop].vertex_index].co
            u, v = uv[loop].uv
            corners.append(((x, z, -y), (u, 1. - v)))
        expected = faces.pop(tuple(sorted(position for position, _ in corners)))
        differences = [(u - expected[pos][0], v - expected[pos][1]) for pos, (u, v) in corners]
        # A common whole-tile translation gives the same repeated image on this face.
        shift = round(differences[0][0])
        max_error = max(max_error, *(max(abs(du - shift), abs(dv)) for du, dv in differences))
        tested += 3
assert mesh_count == 2 and tested == corner_count and not faces and max_error < 2e-6, (mesh_count, tested, max_error)
report = json.loads(report_file.read_bytes())
report['packed_timber'] = dict(sha256=texture_sha256, shaft_meshes=mesh_count, verified_uv_corners=tested,
                               maximum_uv_error=max_error, connected_to_base_color=True)
report_file.write_text(json.dumps(report, indent=2) + '\n')
