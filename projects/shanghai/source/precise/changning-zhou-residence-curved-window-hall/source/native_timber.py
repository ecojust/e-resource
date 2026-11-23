"""Pack the two shafts' authored timber texture in the editable Blender model."""
from pathlib import Path
import sys

import bpy

source_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(source_dir))
from hall import WOOD
from native_timber_source import timber_source


@bpy.app.handlers.persistent
def add_timber_before_save(_):
    material = bpy.data.materials.get(WOOD)
    if material is None:
        return

    image = bpy.data.images.load(str(source_dir / 'stained-timber.png'), check_existing=True)
    image.pack()
    image.filepath = '//stained-timber.png'
    nodes = material.node_tree.nodes
    texture = nodes.get('Packed stained timber') or nodes.new('ShaderNodeTexImage')
    texture.name = 'Packed stained timber'
    texture.image = image
    shader = nodes.get('Principled BSDF')
    material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])

    group_file = Path(sys.argv[sys.argv.index('--') + 1])
    raw = group_file.parent / 'changning-zhou-residence-curved-window-hall-raw.glb'
    faces, _, _ = timber_source(raw)
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or material.name not in obj.data.materials:
            continue
        mesh = obj.data
        uv = mesh.uv_layers.get('Timber grain') or mesh.uv_layers.new(name='Timber grain')
        for face in mesh.polygons:
            if mesh.materials[face.material_index] != material:
                continue
            coordinates = []
            for loop in face.loop_indices:
                x, y, z = mesh.vertices[mesh.loops[loop].vertex_index].co
                coordinates.append((x, z, -y))
            original = faces.pop(tuple(sorted(coordinates)))
            for loop, position in zip(face.loop_indices, coordinates):
                u, v = original[position]
                uv.data[loop].uv = (u, 1. - v)
    assert not faces


bpy.app.handlers.save_pre.append(add_timber_before_save)
