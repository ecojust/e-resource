"""Store the original aggregate texture and frame both visible street fronts in the editable file."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from finish import texture_uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_somekh_streets(_):
    material=bpy.data.materials.get('warm grey washed aggregate')
    if material and not material.node_tree.nodes.get('Somekh washed aggregate'):
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name='Somekh washed aggregate'
        texture.image=bpy.data.images.load(str(Path(__file__).with_name('washed-aggregate.png')))
        texture.image.pack()
        shader=material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or material.name not in obj.data.materials:continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='original washed-stone aggregate')
            for loop in mesh.loops:
                uv.data[loop.index].uv=texture_uv(*mesh.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # View from southeast to see both the street entrance and the corner porch.
    direction=Vector((1.23,-2.62,.64)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Light across the pier faces also reaches beneath the eaves.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((24,-35,47))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='沙美大楼 · 北京东路与四川中路'
    camera.data.name='北京东路及东南转角'
    scene.cycles.samples=12
    scene.render.resolution_x=920
    scene.render.resolution_y=744
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.11*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the stair tower and reopened bank porch. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_somekh_streets)
