"""Read the saved native texture, UVs, camera frames and editable face material assignments."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

source = Path(__file__).resolve().parent
sys.path.insert(0, str(source))
from render_finish import plaster_uv
CONCRETE='warm pebble dash'
MAIN='Soong residence Garden corner'
SHADER_NAME='Soong original roughcast'
TEXTURE='garden-roughcast.png'
UV_NAME='garden roughcast UV'
CAMERAS={'Soong residence '+k:v for k,v in [('Garden corner',(-1.26,-1,.31)),('East gable',(.04,-1,.16)),('Garden bay',(-1,-.36,.20)),('Roof junction',(-1.05,-1,.95))]}

blend, raw, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
assert Path(bpy.data.filepath).resolve() == blend.resolve()
report = json.loads(output.read_bytes())
assert report['match_raw']
source_png = (source / TEXTURE).read_bytes()
scene = bpy.context.scene
mat = bpy.data.materials[CONCRETE]
node = mat.node_tree.nodes[SHADER_NAME]
links = mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links
assert len(links) == 1 and links[0].from_node == node
assert node.extension == 'EXTEND' and node.image.packed_file
assert bytes(node.image.packed_file.data) == source_png
assert tuple(node.image.size) == struct.unpack_from('>II', source_png, 16)
assert node.image.colorspace_settings.name == 'sRGB'
camera_names = {o.name for o in scene.objects if o.type == 'CAMERA'}
assert camera_names == set(CAMERAS) and scene.camera.name == MAIN
for name, eye_direction in CAMERAS.items():
    camera=scene.objects[name]
    assert camera.data.type=='ORTHO' and camera.data.ortho_scale>0
    direction = camera.matrix_world.to_quaternion() @ Vector((0,0,-1))
    assert direction.dot(-Vector(eye_direction).normalized())>.999999
assert scene.cycles.samples==14 and [scene.render.resolution_x,scene.render.resolution_y]==[960,840]
groups, corners, concrete = {}, [], []
for obj in [o for o in scene.objects if o.type == 'MESH']:
    mesh = obj.data
    groups[obj.name] = Counter(mesh.materials[p.material_index].name for p in mesh.polygons)
    corners.extend(world_to_camera_view(scene, scene.camera, obj.matrix_world @ Vector(c)) for c in obj.bound_box)
    if CONCRETE not in mesh.materials:
        continue
    layer = mesh.uv_layers.active
    assert layer.name == UV_NAME and layer.active_render
    count, maximum = 0, 0.
    for poly in mesh.polygons:
        if mesh.materials[poly.material_index] != mat:
            continue
        for i in poly.loop_indices:
            real = layer.data[i].uv
            expected = plaster_uv(*mesh.vertices[mesh.loops[i].vertex_index].co)
            maximum = max(maximum, abs(real.x - expected[0]), abs(real.y - expected[1]))
            count += 1
    assert count and maximum < .000003, (obj.name, maximum)
    concrete.append(dict(group=obj.name, loops=count, maximum_error=maximum))
assert concrete and groups and min(p.z for p in corners) > 0
frame = [min(p.x for p in corners), min(p.y for p in corners), max(p.x for p in corners), max(p.y for p in corners)]
assert min(frame[:2]) > .01 and max(frame[2:]) < .99, frame
schedule = json.dumps(groups, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
report['garden_reopened'] = dict(raw_sha256=sha256(raw.read_bytes()).hexdigest(),
    packed_png_sha256=sha256(source_png).hexdigest(), png_size=list(node.image.size),
    material=CONCRETE, uv_name=UV_NAME, texture_node=SHADER_NAME, texture_coordinates=concrete,
    uv_loops=sum(row['loops'] for row in concrete), group_material_faces_sha256=sha256(schedule).hexdigest(),
    orthographic_cameras=CAMERAS, whole_frame=frame, active_camera=MAIN)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
