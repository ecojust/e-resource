"""Pack the authored stone finish and store the four courtyard views in the editable file."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from render_finish import stone_uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_zhu_porch(_):
    material=bpy.data.materials.get('warm pebble render')
    if material and not material.node_tree.nodes.get('Zhu original wall finish'):
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name='Zhu original wall finish'
        texture.image=bpy.data.images.load(str(Path(__file__).with_name('garden-render.png')))
        texture.extension='EXTEND'
        texture.image.pack()
        shader=material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or material.name not in obj.data.materials:continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='side render UV')
            uv.active_render=True
            mesh.uv_layers.active=uv
            for loop in mesh.loops:
                uv.data[loop.index].uv=stone_uv(*mesh.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    signature=[('Porch and bow',(-.41,-1,.23)),('Side elevation',(.015,-1,.04)),('Portico terrace',(.63,-1,.55)),('Oriel and rosette',(-.82,-1,.40))]
    active=scene.camera
    if not active:
        return
    mesh_corners=[o.matrix_world @ Vector(c) for o in scene.objects if o.type=='MESH' for c in o.bound_box]
    for index,(title,eye) in enumerate(signature):
        name='Zhu side porch '+title
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
bpy.app.handlers.save_pre.append(frame_zhu_porch)
