"""Pack the original stone map and set the north stair viewpoints."""
from pathlib import Path
import hashlib
import json
import sys

import bpy
from mathutils import Vector

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
from stair_render import STONE, uv

VIEWS = json.loads((SOURCE / "cameras.json").read_bytes())
UV_NAME = "Elisabeth cement render, 0.74 m"


@bpy.app.handlers.persistent
def prepare_stair(_):
    scene = bpy.context.scene
    material = bpy.data.materials[STONE]
    material.use_nodes = True
    tree = material.node_tree
    node = tree.nodes.get("Elisabeth exterior cement render") or tree.nodes.new("ShaderNodeTexImage")
    node.name = "Elisabeth exterior cement render"
    node.interpolation = "Linear"
    node.extension = "REPEAT"
    original = SOURCE / "cement-render.png"
    image = bpy.data.images.load(str(original), check_existing=True)
    if image.packed_file is None:
        image.pack()
    assert hashlib.sha256(bytes(image.packed_file.data)).digest() == hashlib.sha256(original.read_bytes()).digest()
    node.image = image
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    tree.links.new(node.outputs["Color"], shader.inputs["Base Color"])
    uvnode = tree.nodes.get("Elisabeth cement coordinates") or tree.nodes.new("ShaderNodeUVMap")
    uvnode.name = "Elisabeth cement coordinates"
    uvnode.uv_map = UV_NAME
    tree.links.new(uvnode.outputs["UV"], node.inputs["Vector"])

    assigned = 0
    for obj in scene.objects:
        if obj.type != 'MESH' or STONE not in obj.data.materials:
            continue
        mesh = obj.data
        layer = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
        mesh.uv_layers.active = layer
        layer.active_render = True
        for poly in mesh.polygons:
            if mesh.materials[poly.material_index].name!=STONE:
                continue
            axis=max(range(3),key=lambda k:abs(poly.normal[k]))
            for i in poly.loop_indices:
                point=obj.matrix_world @ mesh.vertices[mesh.loops[i].vertex_index].co
                u,v=uv(*point,axis)
                layer.data[i].uv=(float(u),float(v))
                assigned += 1
    assert assigned > 0
    collection = bpy.data.collections["Preview lighting and camera"]
    for i, view in enumerate(VIEWS):
        name = view["label"]
        camera = scene.camera if i == 0 else bpy.data.objects.get(name)
        if camera is None:
            camera = bpy.data.objects.new(name, bpy.data.cameras.new(name))
            collection.objects.link(camera)
        camera.name = camera.data.name = name
        camera.location = view["eye"]
        delta = Vector(view["target"]) - camera.location
        camera.rotation_euler = delta.to_track_quat("-Z", "Y").to_euler()
        camera.data.type = "PERSP"
        camera.data.sensor_fit = "HORIZONTAL"
        camera.data.lens = camera.data.sensor_width * delta.length / view["width_m"]
        camera.data.clip_start, camera.data.clip_end = .025, 180
        camera["target_local_m"] = view["target"]
    scene.camera = bpy.data.objects[VIEWS[0]["label"]]
    scene.render.resolution_x, scene.render.resolution_y = VIEWS[0]["width"], VIEWS[0]["height"]
    scene.render.resolution_percentage = 100
    for light in scene.objects:
        if light.type == 'LIGHT' and light.data.type == 'SUN':
            light.location = (24, -34, 43)
            light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
    scene["stone_texture_sha256"] = hashlib.sha256(original.read_bytes()).hexdigest()
    scene["stone_uv_loops"] = assigned
    bpy.context.view_layer.update()


bpy.app.handlers.save_pre.append(prepare_stair)
