"""Frame the through-arch, red shutters and both tiers of rising eaves."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from stone_finish import texture_uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_longmen_gate(_):
    material=bpy.data.materials.get('dressed gate granite')
    if material and not material.node_tree.nodes.get('Gate granite grain'):
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name='Gate granite grain'
        texture.image=bpy.data.images.load(str(Path(__file__).with_name('stone-grain.png')))
        texture.image.pack()
        shader=material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or material.name not in obj.data.materials:continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='Gate granite coordinates')
            for loop in mesh.loops:
                uv.data[loop.index].uv=texture_uv(*mesh.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # A slight streetward oblique shows the depth of the arch and both side eaves.
    direction=Vector((.18,-2.25,-.37)).normalized()
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
    camera.name='龙门邨 · 尚文路总弄'
    camera.data.name='尚文路正交相机'
    scene.cycles.samples=12
    scene.render.resolution_x=760
    scene.render.resolution_y=900
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.11*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the arched gate and two-tier eaves. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_longmen_gate)
