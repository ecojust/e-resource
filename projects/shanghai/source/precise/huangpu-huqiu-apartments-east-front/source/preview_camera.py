"""Frame the recessed elevation and its two projecting street wings."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from brickwork import texture_uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_street_front(_):
    material=bpy.data.materials.get('Huqiu red brick')
    if material and not material.node_tree.nodes.get('Huqiu red brickwork'):
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name='Huqiu red brickwork'
        texture.image=bpy.data.images.load(str(Path(__file__).with_name('huqiu-red-brick.png')))
        texture.image.pack()
        shader=material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or material.name not in obj.data.materials:continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='Metre-scale courses')
            for loop in mesh.loops:
                uv.data[loop.index].uv=texture_uv(*mesh.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # The Culture and Tourism Bureau shows the corner from across the junction.
    direction=Vector((-.28,-3.2,.54)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Raking light distinguishes the projecting wings, recessed windows and central portal.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((-22,-45,39))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Huqiu Road east facade'
    scene.render.resolution_x=980
    scene.render.resolution_y=790
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.09*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the stepped Huqiu Road frontage',scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_street_front)
