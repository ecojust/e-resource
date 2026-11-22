"""Frame the actual editable asset from the measured garden-side approach."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

settings = json.loads(Path(__file__).with_name("preview-camera.json").read_bytes())

@bpy.app.handlers.persistent
def frame_component(_):
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        return
    direction = Vector(settings["direction"]).normalized()
    orientation = (-direction).to_track_quat("-Z", "Y")
    projected = [orientation.inverted() @ (obj.matrix_world @ Vector(corner))
                 for obj in scene.objects if obj.type == "MESH" for corner in obj.bound_box]
    if not projected:
        return
    low = Vector([min(point[i] for point in projected) for i in range(3)])
    high = Vector([max(point[i] for point in projected) for i in range(3)])
    center = orientation @ ((low + high) / 2)
    camera.location = center + direction * 40
    camera.rotation_euler = orientation.to_euler()
    camera.name = settings["name"]
    scene.render.resolution_x,scene.render.resolution_y = settings["pixels"]
    for obj in scene.objects:
        if obj.type == "LIGHT" and obj.data.type == "SUN":
            obj.location = Vector((29,-31,49))
            obj.rotation_euler = (-obj.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1
    frustum = camera.data.view_frame(scene=scene)
    width = max(v.x for v in frustum)-min(v.x for v in frustum)
    height = max(v.y for v in frustum)-min(v.y for v in frustum)
    camera.data.ortho_scale = 1.15*max((high.x-low.x)/width,(high.y-low.y)/height)
    bpy.context.view_layer.update()
    print("Framed",camera.name,scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_component)

@bpy.app.handlers.persistent
def assign_plank_finish(_):
    texture=bpy.data.images.load(str(Path(__file__).with_name('weathered-planks.png')),check_existing=True)
    texture.pack()
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH' or ' vertical board ' not in obj.name:
            continue
        layer=obj.data.uv_layers.get('Wood plane') or obj.data.uv_layers.new(name='Wood plane')
        for loop in obj.data.loops:
            v=obj.data.vertices[loop.vertex_index].co
            u=min(1.,max(0.,(v.x/.00345+252)/500))
            t=min(1.,max(0.,(751-v.z/.00345)/752))
            layer.data[loop.index].uv=(u,1.-t)
    for name in ('dark oak','weathered board','inner strip'):
        mat=bpy.data.materials[name]
        nodes=mat.node_tree.nodes
        tex=nodes.get('Original plank finish') or nodes.new('ShaderNodeTexImage')
        tex.name='Original plank finish'
        tex.image=texture
        product=nodes.get('Plank colour') or nodes.new('ShaderNodeMixRGB')
        product.name='Plank colour'
        product.blend_type='MULTIPLY'
        product.inputs[0].default_value=1.
        product.inputs[2].default_value=mat.diffuse_color
        mat.node_tree.links.new(tex.outputs['Color'],product.inputs[1])
        mat.node_tree.links.new(product.outputs[0],nodes['Principled BSDF'].inputs['Base Color'])

bpy.app.handlers.save_pre.append(assign_plank_finish)
