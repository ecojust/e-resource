"""Frame the six lower treads, the curved handrails and both newel stones."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_windows(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:
        return
    eye=Vector((5.,-14.,7.4)).normalized()
    rotation=(-eye).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (o.matrix_world @ Vector(p)) for o in scene.objects if o.type=='MESH' for p in o.bound_box]
    if not corners:
        return
    lo=Vector([min(v[i] for v in corners) for i in range(3)])
    hi=Vector([max(v[i] for v in corners) for i in range(3)])
    camera.rotation_euler=rotation.to_euler()
    camera.location=rotation @ ((lo+hi)/2)+eye*30
    camera.name='Lunghwa terminal stair foot'
    camera.data.type='ORTHO'
    scene.render.resolution_x=800
    scene.render.resolution_y=640
    camera.data.ortho_scale=max((hi.x-lo.x)*1.13,(hi.y-lo.y)*800/640*1.13)
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(frame_windows)

# The first mesh export uses glTF top-origin UVs. Blender's packed image uses the opposite V axis.
from pathlib import Path
_STONE_IMAGE=Path(__file__).with_name('pale-stone.png')
@bpy.app.handlers.persistent
def pack_stair_stone(_):
    material=bpy.data.materials.get('Warm veined stone')
    if material is None:return
    image=bpy.data.images.load(str(_STONE_IMAGE),check_existing=True)
    image.pack()
    node=material.node_tree.nodes.get('Original cream stone')
    if node is None:
        node=material.node_tree.nodes.new('ShaderNodeTexImage')
        node.name='Original cream stone'
        node.image=image
        shader=material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH':continue
        mesh=obj.data
        if not any(m==material for m in mesh.materials):continue
        uv=mesh.uv_layers.get('Stone slab coordinates') or mesh.uv_layers.new(name='Stone slab coordinates')
        for face in mesh.polygons:
            if mesh.materials[face.material_index]!=material:continue
            for idx in face.loop_indices:
                x,y,z=mesh.vertices[mesh.loops[idx].vertex_index].co
                uv.data[idx].uv=((x+2.8)/5.6,1-(.28+y*.47+z*.23)/1.9)
bpy.app.handlers.save_pre.append(pack_stair_stone)
