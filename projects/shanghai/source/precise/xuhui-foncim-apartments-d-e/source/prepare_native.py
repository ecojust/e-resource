"""Pack the mineral wall finish and set the seven entrance cameras."""
from pathlib import Path
import hashlib
import json
import sys

import bpy
from mathutils import Vector

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
import os
from raw_wall_uv import NAME as PLASTER, raw_wall_loops, mapped_polygon

VIEWS = json.loads((SOURCE / "cameras.json").read_bytes())
UV_NAME = "Foncim signed wall coordinates"


@bpy.app.handlers.persistent
def prepare_foncim(_):
    scene = bpy.context.scene
    material = bpy.data.materials[PLASTER]
    material.use_nodes = True
    tree = material.node_tree
    node = tree.nodes.get("Foncim striped wall finish") or tree.nodes.new("ShaderNodeTexImage")
    node.name = "Foncim striped wall finish"
    node.interpolation = "Linear"
    node.extension = "REPEAT"
    original = SOURCE / "chestnut-ochre-courses.png"
    image = bpy.data.images.load(str(original), check_existing=True)
    if image.packed_file is None:
        image.pack()
    assert hashlib.sha256(bytes(image.packed_file.data)).digest() == hashlib.sha256(original.read_bytes()).digest()
    node.image = image
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    tree.links.new(node.outputs["Color"], shader.inputs["Base Color"])
    uvnode = tree.nodes.get("Foncim registered wall UV") or tree.nodes.new("ShaderNodeUVMap")
    uvnode.name = "Foncim registered wall UV"
    uvnode.uv_map = UV_NAME
    tree.links.new(uvnode.outputs["UV"], node.inputs["Vector"])

    raw = Path(os.environ['FONCIM_RAW_GLB'])
    index, raw_face_count, raw_sha = raw_wall_loops(raw,hashlib.sha256(original.read_bytes()).hexdigest())
    assigned = 0
    by_block = {'D':0,'E':0}
    for obj in scene.objects:
        if obj.type != 'MESH' or PLASTER not in obj.data.materials:
            continue
        mesh = obj.data
        layer = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
        mesh.uv_layers.active = layer
        layer.active_render = True
        for poly in mesh.polygons:
            if mesh.materials[poly.material_index].name!=PLASTER:
                continue
            block=obj.name.split(' ',1)[0][0]
            if block not in by_block:
                raise ValueError('Unexpected group for a Foncim wall: '+obj.name)
            for i,(u,v) in mapped_polygon(obj,poly,index):
                layer.data[i].uv=(u,v)
                assigned+=1
                by_block[block]+=1
    assert assigned==3*raw_face_count and all(by_block.values())
    scene['wall_source_raw_sha256']=raw_sha
    scene['wall_uv_D_loops']=by_block['D']
    scene['wall_uv_E_loops']=by_block['E']
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
    scene["plaster_texture_sha256"] = hashlib.sha256(original.read_bytes()).hexdigest()
    scene["plaster_uv_loops"] = assigned
    bpy.context.view_layer.update()


bpy.app.handlers.save_pre.append(prepare_foncim)
