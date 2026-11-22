"""Frame the east pediment and recessed street entrance."""
import bpy
from pathlib import Path
from mathutils import Vector

BRICK_IMAGE = Path(__file__).with_name('running-bond.png')

@bpy.app.handlers.persistent
def frame_mitsui_bussan(_):
    material=bpy.data.materials.get('warm red running-bond brick')
    if material and not material.node_tree.nodes.get('Mitsui running bond'):
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name='Mitsui running bond'
        texture.image=bpy.data.images.load(str(BRICK_IMAGE))
        texture.image.pack()
        multiply=material.node_tree.nodes.new('ShaderNodeMixRGB')
        multiply.blend_type='MULTIPLY'
        multiply.inputs[0].default_value=1
        multiply.inputs[2].default_value=(.88,.85,.82,1)
        links=material.node_tree.links
        links.new(texture.outputs['Color'],multiply.inputs[1])
        links.new(multiply.outputs[0],material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or all(mat!=material for mat in obj.data.materials):continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='Metre-scale running bond')
            for polygon in mesh.polygons:
                for loop_id in polygon.loop_indices:
                    coord=mesh.vertices[mesh.loops[loop_id].vertex_index].co
                    x,y,z=coord
                    uv.data[loop_id].uv=((x+(2*y if abs(x)>5.75-.3 else 0))/1.32,z/.64)
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    direction=Vector((-.61,-3.2,.83)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((35,-25,42))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Mitsui Bussan east entrance on Sichuan Road'
    scene.render.resolution_x=760
    scene.render.resolution_y=570
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the Mitsui Bussan east entrance on Sichuan Road',scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_mitsui_bussan)
