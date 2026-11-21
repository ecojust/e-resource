"""Frame the three balcony bays and the paired columns at the street entrance."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_street_front(_):
    material=bpy.data.materials.get('restored red facing brick')
    if material and not material.node_tree.nodes.get('Ta-Ching brickwork'):
        image_node=material.node_tree.nodes.new('ShaderNodeTexImage')
        image_node.name='Ta-Ching brickwork'
        image_node.image=bpy.data.images.load(str(Path(__file__).with_name('bond.png')))
        image_node.image.pack()
        shader=material.node_tree.nodes['Principled BSDF']
        material.node_tree.links.new(image_node.outputs['Color'],shader.inputs['Base Color'])
        from brick import wall_uv
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or material.name not in obj.data.materials:continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='Southwest brick courses')
            for loop in mesh.loops:
                u,v=wall_uv(*mesh.vertices[loop.vertex_index].co)
                uv.data[loop.index].uv=(u,1-v)
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # The slight oblique view exposes the projecting low crown and cornices along the two short street returns.
    direction=Vector((1.05,-5.4,.48)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Raking light separates the upper brick piers and the recessed corner sashes.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((-22,-45,39))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Ta-Ching Bank southwest corner'
    scene.render.resolution_x=940
    scene.render.resolution_y=800
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.09*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the three street facets and the low copper cupola',scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_street_front)
