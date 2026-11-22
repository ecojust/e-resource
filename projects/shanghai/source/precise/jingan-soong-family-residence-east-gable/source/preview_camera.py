"""Pack the authored roughcast and store the garden and gable views in the editable file."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from render_finish import plaster_uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_soong_residence(_):
    material=bpy.data.materials.get('warm pebble dash')
    if material and not material.node_tree.nodes.get('Soong original roughcast'):
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name='Soong original roughcast'
        texture.image=bpy.data.images.load(str(Path(__file__).with_name('garden-roughcast.png')))
        texture.extension='EXTEND'
        texture.image.pack()
        shader=material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or material.name not in obj.data.materials:continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='garden roughcast UV')
            uv.active_render=True
            mesh.uv_layers.active=uv
            for loop in mesh.loops:
                uv.data[loop.index].uv=plaster_uv(*mesh.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    signature=[('Garden corner',(-1.26,-1,.31)),('East gable',(.04,-1,.16)),('Garden bay',(-1,-.36,.20)),('Roof junction',(-1.05,-1,.95))]
    active=scene.camera
    if not active:
        return
    mesh_corners=[o.matrix_world @ Vector(c) for o in scene.objects if o.type=='MESH' for c in o.bound_box]
    for index,(title,eye) in enumerate(signature):
        name='Soong residence '+title
        camera=active if index==0 else bpy.data.objects.get(name)
        if camera is None:
            camera=bpy.data.objects.new(name,bpy.data.cameras.new(name))
            scene.collection.objects.link(camera)
        camera.name=name
        camera.data.type='ORTHO'
        scene.render.resolution_x,scene.render.resolution_y=960,840
        scene.cycles.samples=14
        direction=Vector(eye).normalized()
        rotation=(-direction).to_track_quat('-Z','Y')
        p=[rotation.inverted()@v for v in mesh_corners]
        lo=Vector([min(v[i] for v in p) for i in range(3)])
        hi=Vector([max(v[i] for v in p) for i in range(3)])
        camera.location=rotation@((lo+hi)/2)+direction*90
        camera.rotation_euler=rotation.to_euler()
        camera.data.ortho_scale=1.14*max(hi.x-lo.x,(hi.y-lo.y)*960/840)
    scene.camera=active
    bpy.context.view_layer.update()
bpy.app.handlers.save_pre.append(frame_soong_residence)
