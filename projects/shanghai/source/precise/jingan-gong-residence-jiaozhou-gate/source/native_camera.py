"""Pack the attributed nameplate atlas and save six cameras with the editable model."""

import sys
from pathlib import Path
import bpy
from mathutils import Vector

source = Path(__file__).resolve().parent
sys.path.insert(0, str(source))
from native_layout import MAIN, CAMERAS, MATERIALS, UV_NAME, uv


@bpy.app.handlers.persistent
def prepare_gong_gate(_):
    scene = bpy.context.scene
    atlas = bpy.data.images.load(str(source / "entrance-plaques.png"), check_existing=True)
    if not atlas.packed_file:
        atlas.pack()
    for mat in MATERIALS:
        tree = bpy.data.materials[mat].node_tree
        tex = tree.nodes.get("2015 plaque photograph") or tree.nodes.new("ShaderNodeTexImage")
        tex.name = "2015 plaque photograph"
        tex.image = atlas
        tex.extension = "EXTEND"
        tree.links.new(tex.outputs["Color"], tree.nodes["Principled BSDF"].inputs["Base Color"])
    for obj in scene.objects:
        if obj.type != "MESH" or not any(m.name in MATERIALS for m in obj.data.materials):
            continue
        mesh = obj.data
        layer = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
        for face in mesh.polygons:
            mat = mesh.materials[face.material_index].name
            if mat not in MATERIALS:
                continue
            for k in face.loop_indices:
                layer.data[k].uv = uv(mat, mesh.loops[k].vertex_index)
        mesh.uv_layers.active = layer
        layer.active_render = True
    group = bpy.data.collections["Preview lighting and camera"]
    for name, (eye, target, width) in CAMERAS.items():
        camera = scene.camera if name == MAIN else bpy.data.objects.get(name)
        if camera is None:
            camera = bpy.data.objects.new(name, bpy.data.cameras.new(name))
            group.objects.link(camera)
        camera.name = camera.data.name = name
        camera.location = eye
        camera.rotation_euler = (
            (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = width
        camera.data.clip_end = 250
        camera.data.clip_start = 0.05
        camera["aim_local_m"] = target
    scene.render.resolution_x = 710
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    sun = next(x for x in scene.objects if x.type == "LIGHT" and x.data.type == "SUN")
    sun.location = (-23, -31, 34)
    sun.rotation_euler = (-sun.location).to_track_quat("-Z", "Y").to_euler()
    scene["photograph_credit"] = (
        "Livelikerw, 522 Jiaozhou Rd. Shanghai, 2015-01-22. Three cropped plaques and a traced slow sign. CC BY-SA 4.0."
    )
    bpy.context.view_layer.update()


bpy.app.handlers.save_pre.append(prepare_gong_gate)
