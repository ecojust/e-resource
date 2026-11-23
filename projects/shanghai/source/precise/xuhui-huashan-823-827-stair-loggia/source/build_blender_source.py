"""Install and verify the actual Huashan Road finishes, oriented corner UVs and frozen cameras in Blender."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = next(p for p in [*SOURCE.parents, Path(os.getenv('E_RESOURCE_SHANGHAI', '.'))]
               if (p / 'tools/verify_editable_model.py').is_file())
sys.path.insert(0, str(SOURCE))
# Reuse the verified per-corner reader, Blender UV writer and frozen-camera verifier.
# Resolve the earlier adapter by filename so that its module-level path setup stays local.
verified = PROJECT / 'source/precise/xuhui-yanqing-159-garden-residence/source/build_blender_source.py'
spec = importlib.util.spec_from_file_location('shanghai_verified_textured_native', verified)
native = importlib.util.module_from_spec(spec)
import_paths = sys.path.copy()
try:
    spec.loader.exec_module(native)
finally:
    sys.path[:] = import_paths
helpers = native.helpers
helpers.SOURCE = SOURCE
helpers.MODEL_ID = SOURCE.parent.name
helpers.UV = 'Huashan Road architectural surface UV'
NODE = 'Huashan Road original procedural finish'
cameras = native.cameras


def read_file(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def used_textures(raw):
    doc = helpers.raw_document(raw)
    if doc['extras'].get('id') != helpers.MODEL_ID:
        raise ValueError('Unexpected Huashan Road model ID')
    used = {p['material'] for mesh in doc['meshes'] for p in mesh['primitives']}
    textures = {}
    for index in sorted(used):
        material = doc['materials'][index]
        binding = material.get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if binding is None:
            continue
        texture = doc['textures'][binding['index']]
        image = doc['images'][texture['source']]
        filename = image['name']
        if Path(filename).name != filename or image.get('mimeType') != 'image/png':
            raise ValueError(f'Expected an embedded, named procedural PNG: {filename}')
        image_path = SOURCE / filename
        if not image_path.is_file() or 'bufferView' not in image:
            raise ValueError(f'Missing authored texture: {filename}')
        textures[material['name']] = image_path
    if not textures:
        raise ValueError('No textured exterior is present in the authored mesh')
    helpers.TEXTURES = textures
    return textures


def attribution(raw):
    meta = helpers.raw_document(raw)['extras']
    if meta.get('id') != helpers.MODEL_ID or meta.get('photos_embedded') is not False:
        raise ValueError('Wrong model ID or photo-embedding metadata')
    if (meta.get('geometry_license'), meta.get('texture_license')) != ('MIT', 'MIT'):
        raise ValueError('The original geometry and generated finishes must retain their MIT licences')
    if not all(meta.get(k) for k in ('source', 'photo_source', 'photo_author', 'photo_reference_license')):
        raise ValueError('Missing register or photographic reference URL')
    if not meta.get('camera_views'):
        raise ValueError('No camera views are embedded in the authored GLB')
    return {k: v for k, v in meta.items() if isinstance(v, (bool, str, int, float))}


def prepare(_scene):
    import bpy
    scene = bpy.context.scene
    raw = Path(os.environ['ARCHITECTURAL_NATIVE_RAW'])
    doc = helpers.raw_document(raw)
    for name, path in used_textures(raw).items():
        mat = bpy.data.materials[name]
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
        uv = nodes.new('ShaderNodeUVMap')
        uv.uv_map = helpers.UV
        node = nodes.new('ShaderNodeTexImage')
        node.name = NODE
        node.image = bpy.data.images.load(str(path), check_existing=True)
        node.image.pack()
        node.image.filepath = '//' + path.name
        node.extension = helpers.texture_extension(doc, name)
        links.new(uv.outputs['UV'], node.inputs['Vector'])
        links.new(node.outputs['Color'], shader.inputs['Base Color'])
        helpers.native_uv(scene, helpers.texture_faces(raw, name), True, name)

    for key, value in attribution(raw).items():
        scene[key] = value
    scene['source_glb_sha256'] = digest(raw)
    aliases = read_file(Path(os.environ['ARCHITECTURAL_NATIVE_GROUPS']))['original_names']
    for name, original in aliases.items():
        scene.objects[name]['authored_group_name'] = original
    names = [obj.name for obj in scene.objects if obj.type == 'MESH']
    scene['editable_group_sha256'] = helpers.editable_groups(names)['names_sha256']
    views = cameras(scene, True, raw)
    scene.render.resolution_x = views[0]['width']
    scene.render.resolution_y = views[0]['height']
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()


def verify(blend, raw, output):
    import bpy
    scene = bpy.context.scene
    report = read_file(output)
    assert Path(bpy.data.filepath).samefile(blend) and report['match_raw']
    assert scene['source_glb_sha256'] == digest(raw)

    materials = {}
    for name, path in used_textures(raw).items():
        nodes = bpy.data.materials[name].node_tree.nodes
        node = nodes[NODE]
        shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
        assert node.extension == 'REPEAT' and shader.inputs['Base Color'].links[0].from_node == node
        assert node.inputs['Vector'].links[0].from_node.uv_map == helpers.UV
        assert hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest() == digest(path)
        faces = helpers.texture_faces(raw, name)
        materials[name] = dict(packed_png_sha256=digest(path), textured_corners=len(faces) * 3,
                               extension=node.extension, max_uv_error=helpers.native_uv(scene, faces, False, name))

    colours = {}
    for source_mat in helpers.raw_document(raw)['materials']:
        name = source_mat['name']
        shader = next(n for n in bpy.data.materials[name].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        pbr = source_mat['pbrMetallicRoughness']
        rgba = list(shader.inputs['Base Color'].default_value)
        metallic = float(shader.inputs['Metallic'].default_value)
        roughness = float(shader.inputs['Roughness'].default_value)
        differences = [abs(a - b) for a, b in zip(rgba, pbr['baseColorFactor'])]
        differences.extend([abs(metallic - pbr['metallicFactor']), abs(roughness - pbr['roughnessFactor'])])
        if max(differences) > 1e-6:
            raise ValueError(f'Changed native shader values: {name}')
        colours[name] = dict(linear_rgba=rgba, metallic=metallic, roughness=roughness)

    names = [obj.name for obj in scene.objects if obj.type == 'MESH']
    groups = helpers.editable_groups(names)
    assert groups['names_sha256'] == scene['editable_group_sha256'] and groups['count'] == report['mesh_count']
    aliases = read_file(Path(os.environ['ARCHITECTURAL_NATIVE_GROUPS']))['original_names']
    assert all(scene.objects[name]['authored_group_name'] == original for name, original in aliases.items())
    data = attribution(raw)
    assert all(scene[k] == v for k, v in data.items())
    report['architectural_source'] = dict(metadata=data, raw_sha256=digest(raw), editable_groups=groups,
                                material_factors=colours, textured_materials=materials, cameras=cameras(scene, False, raw))
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    phase = os.environ['ARCHITECTURAL_NATIVE_STAGE']
    if phase == 'make':
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(prepare))
    elif phase == 'reopen':
        verify(*map(Path, sys.argv[sys.argv.index('--') + 1:]))
    else:
        raise ValueError(phase)
