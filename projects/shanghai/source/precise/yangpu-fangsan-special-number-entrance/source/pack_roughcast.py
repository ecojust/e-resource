"""Preserve the entrance's original wall finish when saving its editable model."""
from pathlib import Path
import bpy

@bpy.app.handlers.persistent
def pack_roughcast(_):
    mat=bpy.data.materials['grey pebble render']
    wall=bpy.data.objects['Pebbled wall with two apertures'].data
    uv=wall.uv_layers.get('Facade') or wall.uv_layers.new(name='Facade')
    for loop in wall.loops:
        position=wall.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=((position.x+1.586)/3.172,position.z/5.78)
    png=Path(__file__).with_name('pebble-finish.png')
    image=bpy.data.images.load(str(png),check_existing=True)
    image.pack()
    nodes=mat.node_tree.nodes
    image_node=nodes.get('Roughcast chips') or nodes.new('ShaderNodeTexImage')
    image_node.name='Roughcast chips'
    image_node.image=image
    mat.node_tree.links.new(image_node.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])

bpy.app.handlers.save_pre.append(pack_roughcast)
