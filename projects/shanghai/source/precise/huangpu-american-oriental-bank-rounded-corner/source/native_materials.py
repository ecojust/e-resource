"""Recreate editable brick UVs and pack the authored texture in the .blend."""
import bpy
import json
import sys
from mathutils import Vector
from pathlib import Path
source=Path(__file__).resolve().parent
sys.path.insert(0,str(source))
from brick_uv import brick_uv

@bpy.app.handlers.persistent
def before_save(_):
    data=json.loads((source/'dimensions.json').read_text())
    registration=json.loads((source/'frontage-registration.json').read_text())
    name='Meifeng ochre brick strips'
    mat=bpy.data.materials[name]
    image=bpy.data.images.load(str(source/'ochre-brick-fin.png'),check_existing=True)
    image.pack()
    texture=mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image=image
    texture.extension='EXTEND'
    mat.node_tree.links.new(texture.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    for ob in bpy.context.scene.objects:
        if not ob.name.startswith('Facing brick/Strip '):continue
        i=int(ob.name.split()[-1])-1
        left=data['centers'][i]+data['opening_widths'][1][i]/2+.12
        right=data['centers'][i+1]-data['opening_widths'][1][i+1]/2-.12
        pad=min(.20,(right-left)*.15)
        limits=[left+pad,right-pad,data['levels']['brick_foot'],data['levels']['band']-.080]
        uv=ob.data.uv_layers.new(name='Whole fin')
        for loop in ob.data.loops:
            uv.data[loop.index].uv=brick_uv(ob.data.vertices[loop.vertex_index].co,limits,registration)
    scene=bpy.context.scene
    cam=scene.camera
    cam.name='Ningbo and Henan road corner'
    target=Vector((21.2,4.9,7.4))
    cam.location=target+Vector((23,-32,3.2))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=22.6
    scene.render.resolution_x=840
    scene.render.resolution_y=780
    scene.cycles.samples=20
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(before_save)
