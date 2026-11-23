"""Import the Xinlefang Wavefront model in Blender with the MTL's numeric Ke emission.

From a Blender Python console, execute this script from the extracted OBJ package.
To save a .blend from the command line: blender -b --python-exit-code 1
--python import_wavefront.py -- path/to/the-model.obj path/to/converted.blend
"""
from pathlib import Path
import sys


def restore_mtl_emission(path, materials):
    """Blender 4.3 stores numeric Ke as a color but leaves its strength at zero."""
    by_name = {m.name: m for m in materials}
    material = None
    restored = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        words = line.strip().split()
        if not words:
            continue
        if words[0] == 'newmtl':
            material = by_name.get(' '.join(words[1:]))
        elif words[0] == 'Ke' and material is not None:
            colour = tuple(map(float, words[1:4]))
            if not any(colour):
                continue
            shader = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            shader.inputs['Emission Color'].default_value = (*colour, 1.0)
            shader.inputs['Emission Strength'].default_value = 1.0
            restored[material.name] = colour
    return restored


def import_mesh(path):
    import bpy
    path = Path(path).absolute()
    bpy.ops.wm.obj_import(filepath=str(path), forward_axis='Y', up_axis='Z')
    materials = {slot.material for obj in bpy.context.selected_objects if obj.type == 'MESH'
                 for slot in obj.material_slots if slot.material}
    return restore_mtl_emission(path.with_suffix('.mtl'), materials)


if __name__ == '__main__':
    import bpy
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    location = Path(__file__).absolute().parent
    obj = Path(args[0]) if args else next(location.glob('*.obj'))
    import_mesh(obj)
    if len(args) > 1:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[1]).absolute()))
