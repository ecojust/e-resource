"""Pack the procedural concrete and place the six cameras before the editable file is saved."""
from pathlib import Path
import sys

import bpy
from mathutils import Vector

source = Path(__file__).resolve().parent
sys.path.insert(0, str(source))
from native_layout import CAMERAS, CONCRETE, MAIN, SHADER_NAME, TEXTURE, UV_NAME, native_uv

@bpy.app.handlers.persistent
def prepare_tower(_):
    scene = bpy.context.scene
    material = bpy.data.materials[CONCRETE]
    shader = material.node_tree.nodes['Principled BSDF']
    texture = material.node_tree.nodes.get(SHADER_NAME)
    if texture is None:
        texture = material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name = SHADER_NAME
        texture.image = bpy.data.images.load(str(source / TEXTURE))
        texture.image.pack()
        texture.extension = 'EXTEND'
        material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    for obj in scene.objects:
        if obj.type != 'MESH' or CONCRETE not in obj.data.materials:
            continue
        mesh = obj.data
        uv = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
        for loop in mesh.loops:
            uv.data[loop.index].uv = native_uv(mesh.vertices[loop.vertex_index].co)
        mesh.uv_layers.active = uv
        uv.active_render = True
    collection = bpy.data.collections['Preview lighting and camera']
    for name, (eye, focus, scale) in CAMERAS.items():
        camera = scene.camera if name == MAIN else bpy.data.objects.get(name)
        if camera is None:
            camera = bpy.data.objects.new(name, bpy.data.cameras.new(name))
            collection.objects.link(camera)
        camera.name = camera.data.name = name
        camera.location = Vector(eye)
        camera.rotation_euler = (Vector(focus) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = scale
        camera.data.clip_start = .05
        camera.data.clip_end = 300
        camera['aim_local_m'] = focus
    scene.render.resolution_x = 720
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    sun = next(o for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN')
    sun.location = Vector((-21, -32, 42))
    sun.rotation_euler = (-sun.location).to_track_quat('-Z', 'Y').to_euler()
    scene['reference_state'] = '2016–2020 courtyard tower, spiral stair, lookout and roof railing'
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(prepare_tower)
