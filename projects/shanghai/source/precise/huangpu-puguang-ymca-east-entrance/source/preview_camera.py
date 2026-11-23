"""Store the original brick texture and frame the east street facade in the editable file."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from brick_finish import texture_uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_puguang_front(_):
    material=bpy.data.materials.get('exposed warm Shanghai brick')
    if material and not material.node_tree.nodes.get('Puguang original running bond'):
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name='Puguang original running bond'
        texture.image=bpy.data.images.load(str(Path(__file__).with_name('east-wall-bricks.png')))
        texture.image.pack()
        shader=material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or material.name not in obj.data.materials:continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='east facade brick courses')
            for loop in mesh.loops:
                uv.data[loop.index].uv=texture_uv(*mesh.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # A shallow street oblique preserves the arch, the broken pediment and both shopfronts.
    direction=Vector((-.19,-2.62,.13)).normalized()
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
    camera.name='浦光大楼 · 四川中路门头'
    camera.data.name='四川中路东立面'
    scene.cycles.samples=12
    scene.render.resolution_x=920
    scene.render.resolution_y=744
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.11*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the arched portal, two shops and broken pediment. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_puguang_front)
