"""Audit the saved mesh groups, packed texture, individual UV loops and nine cameras."""
from pathlib import Path
import hashlib
import json
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

source = Path(__file__).resolve().parent
sys.path.insert(0, str(source))
from villa_materials import ROUGH, pebble_uv

blend, raw, output = map(Path, sys.argv[sys.argv.index("--") + 1:])
report = json.loads(output.read_bytes())
assert report["match_raw"] and Path(bpy.data.filepath).resolve() == blend.resolve()
scene = bpy.context.scene
views = json.loads((source / "cameras.json").read_bytes())
assert len(views) == 9 and scene.camera.name == views[0]["label"]
for view in views:
    cam = bpy.data.objects[view["label"]]
    assert cam.type == 'CAMERA' and cam.data.type == 'PERSP'
    assert (cam.location-Vector(view["eye"])).length < .0001
    delta = Vector(view["target"])-cam.location
    xy = world_to_camera_view(scene, cam, Vector(view["target"]))
    assert abs(xy.x-.5) < .001 and abs(xy.y-.5) < .001 and xy.z > 0
    assert abs(cam.data.sensor_width*delta.length/cam.data.lens-view["width_m"]) < .001
material = bpy.data.materials[ROUGH]
node = material.node_tree.nodes["517 original aggregate"]
image = node.image
texture_sha = hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
assert texture_sha == scene["villa_texture_sha256"] == hashlib.sha256((source/"pebble-dash.png").read_bytes()).hexdigest()
assert node.extension == 'REPEAT' and node.inputs['Vector'].is_linked
uv_name = node.inputs['Vector'].links[0].from_node.uv_map
assert uv_name == 'Pebble dash, 0.74 metre repeat'
shader = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
assert shader.inputs['Base Color'].links[0].from_node == node
groups = [o for o in scene.objects if o.type=='MESH']
for label in ('brick arch mortar joints','red barrel vault lining','attic door ridge','open diamond stone balusters',
              'attic door threshold','main cross ridge','terrace paving','tapered flue with rolled lip'):
    assert any(label in obj.name for obj in groups), label
loops = 0
max_error = 0.
for obj in groups:
    if ROUGH not in obj.data.materials:
        continue
    mesh = obj.data
    layer = mesh.uv_layers[uv_name]
    assert layer.active_render and len(layer.data) == len(mesh.loops)
    for loop in mesh.loops:
        want = pebble_uv(*(obj.matrix_world @ mesh.vertices[loop.vertex_index].co))
        uv = layer.data[loop.index].uv
        max_error = max(max_error, abs(want[0]-uv[0]), abs(want[1]-uv[1]))
    loops += len(mesh.loops)
assert loops == scene["villa_metric_uv_loops"] and loops > 0 and max_error < .00001
report["villa_roof_and_elevations"] = dict(cameras=views, groups=len(groups), texture_sha256=texture_sha,
    packed_image_bytes=image.packed_file.size,uv_loops=loops,max_uv_error=max_error)
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
