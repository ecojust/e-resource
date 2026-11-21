"""Independently check the Foncim apartment blocks D and E opening, glazing, camera rig and wall texture."""
from pathlib import Path
import hashlib
import json
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

source = Path(__file__).resolve().parent
sys.path.insert(0, str(source))
from raw_wall_uv import NAME as PLASTER, raw_wall_loops, mapped_polygon

blend, raw, output = map(Path, sys.argv[sys.argv.index("--") + 1:])
report = json.loads(output.read_bytes())
assert report["match_raw"] and Path(bpy.data.filepath).resolve() == blend.resolve()
scene = bpy.context.scene
views = json.loads((source / "cameras.json").read_bytes())
assert len(views) == 7 and scene.camera.name == views[0]["label"]
for view in views:
    cam = bpy.data.objects[view["label"]]
    assert cam.type == 'CAMERA' and cam.data.type == 'PERSP'
    assert (cam.location-Vector(view["eye"])).length < .0001
    delta = Vector(view["target"])-cam.location
    xy = world_to_camera_view(scene, cam, Vector(view["target"]))
    assert abs(xy.x-.5) < .001 and abs(xy.y-.5) < .001 and xy.z > 0
    assert abs(cam.data.sensor_width*delta.length/cam.data.lens-view["width_m"]) < .001
material = bpy.data.materials[PLASTER]
node = material.node_tree.nodes["Foncim striped wall finish"]
image = node.image
texture_sha = hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
assert texture_sha == scene["plaster_texture_sha256"] == hashlib.sha256((source/"chestnut-ochre-courses.png").read_bytes()).hexdigest()
assert node.extension == 'REPEAT' and node.inputs['Vector'].is_linked
layer_name = node.inputs['Vector'].links[0].from_node.uv_map
assert layer_name == 'Foncim signed wall coordinates'
shader = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
assert shader.inputs['Base Color'].links[0].from_node == node
groups = [o for o in scene.objects if o.type=='MESH']
assert all(any(o.name.startswith(k) for o in groups) for k in ['D','E'])
raw_index, raw_faces, raw_sha = raw_wall_loops(raw,texture_sha)
assert scene['wall_source_raw_sha256']==raw_sha
loops, max_error = 0, 0.
by_block={'D':0,'E':0}
for obj in groups:
    if PLASTER not in obj.data.materials:
        continue
    mesh = obj.data
    layer = mesh.uv_layers[layer_name]
    assert layer.active_render and len(layer.data) == len(mesh.loops)
    for poly in mesh.polygons:
        if mesh.materials[poly.material_index].name!=PLASTER:
            continue
        block=obj.name[0]
        assert block in by_block
        for i,want in mapped_polygon(obj,poly,raw_index):
            got=layer.data[i].uv
            max_error=max(max_error,abs(want[0]-got[0]),abs(want[1]-got[1]))
            loops+=1
            by_block[block]+=1
assert loops == scene["plaster_uv_loops"] == raw_faces*3 and max_error < .00001
assert all(by_block[key]==scene['wall_uv_'+key+'_loops'] and by_block[key]>0 for key in by_block)
report["foncim_apartments"] = dict(cameras=views, groups=len(groups), texture_sha256=texture_sha,
    wall_block_uv_loops=by_block, raw_sha256=raw_sha, packed_image_bytes=image.packed_file.size,uv_loops=loops,max_uv_error=max_error)
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
