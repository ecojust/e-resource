"""Pack the original stepped diaper brick image and frame the Ningbo Road frontage."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
source=Path(__file__).resolve().parent
sys.path.insert(0,str(source))
from brick_mapping import BRICK,brick_uv

@bpy.app.handlers.persistent
def apply_appearance(_):
    mat=bpy.data.materials[BRICK]
    image=bpy.data.images.load(str(source/'strand-diaper-brick.png'),check_existing=True)
    image.pack()
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.name='Strand diaper brick field';tex.image=image;tex.extension='EXTEND'
    mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH' or obj.active_material!=mat:continue
        uv=obj.data.uv_layers.new(name='Strand pattern coordinates')
        for loop in obj.data.loops:
            uv.data[loop.index].uv=brick_uv(obj.name,obj.data.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    direction=Vector((.43,-1.,.12)).normalized()
    camera=scene.camera
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted()@(obj.matrix_world@Vector(pt))for obj in scene.objects if obj.type=='MESH'for pt in obj.bound_box]
    lo=Vector([min(v[i]for v in corners)for i in range(3)])
    hi=Vector([max(v[i]for v in corners)for i in range(3)])
    camera.location=(rotation@((lo+hi)/2))+direction*137
    camera.rotation_euler=rotation.to_euler();camera.name='Strand Theatre Ningbo Road'
    camera.data.name='新光大戏院宁波路立面';scene.render.resolution_x=900;scene.render.resolution_y=780
    camera.data.ortho_scale=1
    bounds=camera.data.view_frame(scene=scene)
    dx=max(v.x for v in bounds)-min(v.x for v in bounds);dy=max(v.y for v in bounds)-min(v.y for v in bounds)
    camera.data.ortho_scale=1.10*max((hi.x-lo.x)/dx,(hi.y-lo.y)/dy)
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(apply_appearance)
