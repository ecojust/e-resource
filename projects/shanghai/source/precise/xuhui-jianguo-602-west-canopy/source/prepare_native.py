"""Pack the mineral wall finish and set the seven entrance cameras."""
from pathlib import Path
import hashlib
import json
import sys

import bpy
from mathutils import Vector

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
from plaster import PLASTER, FINISHES, dominant_axis, uv

VIEWS = json.loads((SOURCE / "cameras.json").read_bytes())



def pack_finish(scene, name, filename, period, node_name, layer_name):
    material = bpy.data.materials[name]
    material.use_nodes = True
    tree = material.node_tree
    node = tree.nodes.get(node_name) or tree.nodes.new("ShaderNodeTexImage")
    node.name = node_name
    node.interpolation = "Linear"
    node.extension = "REPEAT"
    original = SOURCE / filename
    image = bpy.data.images.load(str(original), check_existing=True)
    if image.packed_file is None:
        image.pack()
    assert hashlib.sha256(bytes(image.packed_file.data)).digest() == hashlib.sha256(original.read_bytes()).digest()
    node.image = image
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    tree.links.new(node.outputs["Color"], shader.inputs["Base Color"])
    uvnode = tree.nodes.get(node_name + " metric UV") or tree.nodes.new("ShaderNodeUVMap")
    uvnode.name = node_name + " metric UV"
    uvnode.uv_map = layer_name
    tree.links.new(uvnode.outputs["UV"], node.inputs["Vector"])

    assigned = 0
    for obj in scene.objects:
        if obj.type != 'MESH' or name not in obj.data.materials:
            continue
        mesh = obj.data
        layer = mesh.uv_layers.get(layer_name) or mesh.uv_layers.new(name=layer_name)
        mesh.uv_layers.active = layer
        layer.active_render = True
        for poly in mesh.polygons:
            if mesh.materials[poly.material_index].name!=name:
                continue
            axis=dominant_axis(poly.normal)
            for i in poly.loop_indices:
                point=obj.matrix_world @ mesh.vertices[mesh.loops[i].vertex_index].co
                u,v=uv(*point,axis,period)
                layer.data[i].uv=(float(u),float(v))
                assigned += 1
    assert assigned > 0
    return dict(texture_sha256=hashlib.sha256(original.read_bytes()).hexdigest(), uv_loops=assigned)

@bpy.app.handlers.persistent
def prepare_canopy(_):
    scene=bpy.context.scene
    finishes={name:pack_finish(scene,name,*spec) for name,spec in FINISHES.items()}
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
    scene["plaster_texture_sha256"] = finishes[PLASTER]["texture_sha256"]
    scene["mineral_finishes_json"] = json.dumps(finishes,sort_keys=True)
    scene["plaster_uv_loops"] = finishes[PLASTER]["uv_loops"]
    bpy.context.view_layer.update()


bpy.app.handlers.save_pre.append(prepare_canopy)
