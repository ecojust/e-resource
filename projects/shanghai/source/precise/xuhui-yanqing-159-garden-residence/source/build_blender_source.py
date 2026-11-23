"""Install or verify the Yanqing Road garden finishes, original per-corner UVs and architectural cameras in Blender."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = next(p for p in [*SOURCE.parents, Path(os.getenv('E_RESOURCE_SHANGHAI', '.'))]
               if (p / 'tools/verify_editable_model.py').is_file())
sys.path.insert(0, str(SOURCE))
from garden_finishes import FILENAMES

shared = PROJECT / 'source/precise/xuhui-baisaizhong-apartments-fuxing-road-corner/source/build_blender_source.py'
spec = importlib.util.spec_from_file_location('shanghai_textured_native', shared)
helpers = importlib.util.module_from_spec(spec)
import_paths = sys.path.copy()
try:
    spec.loader.exec_module(helpers)
finally:
    sys.path[:] = import_paths

# The shared reader validates image bytes and indexes corner UVs by oriented Float32 geometry.
helpers.SOURCE = SOURCE
helpers.MODEL_ID = 'xuhui-yanqing-159-garden-residence'
helpers.TEXTURES = {material: SOURCE / file for material, file in FILENAMES.items()}
helpers.UV = 'Yanqing 159 architectural finish UV'
NODE = 'Yanqing 159 packed original finish'


def read_file(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def used_textures(raw):
    doc = helpers.raw_document(raw)
    if doc['extras'].get('id') != helpers.MODEL_ID:
        raise ValueError('Unexpected garden residence ID')
    used = {p['material'] for mesh in doc['meshes'] for p in mesh['primitives']}
    names = {doc['materials'][i]['name'] for i in used
             if 'baseColorTexture' in doc['materials'][i].get('pbrMetallicRoughness', {})}
    if not names or not names <= set(helpers.TEXTURES):
        raise ValueError(f'Unrecognised authored finishes in {raw.name}: {sorted(names)}')
    return {name: helpers.TEXTURES[name] for name in sorted(names)}


def attribution(raw):
    meta = helpers.raw_document(raw)['extras']
    if meta.get('id') != helpers.MODEL_ID or meta.get('photos_embedded') is not False:
        raise ValueError('Wrong model ID or photo-embedding metadata')
    if (meta.get('geometry_license'), meta.get('texture_license')) != ('MIT', 'MIT'):
        raise ValueError('The original geometry and generated finishes must retain their MIT licences')
    if not meta.get('source') or not meta.get('photo_source'):
        raise ValueError('Missing register or photographic reference URL')
    if not meta.get('camera_views'):
        raise ValueError('No camera views are embedded in the authored GLB')
    return {k: v for k, v in meta.items() if isinstance(v, (bool, str, int, float))}


def cameras(scene, create, raw):
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    views = helpers.raw_document(raw)['extras']['camera_views']
    assert views and len({v["label"] for v in views}) == len(views) and len({v["name"] for v in views}) == len(views)
    stage = bpy.data.collections["Preview lighting and camera"]
    for i, view in enumerate(views):
        title = view["label"]
        cam = scene.camera if create and i == 0 else bpy.data.objects.get(title)
        if create:
            if cam is None:
                cam = bpy.data.objects.new(title, bpy.data.cameras.new(title))
                stage.objects.link(cam)
            cam.name = cam.data.name = title
            cam.location = view["eye"]
            delta = Vector(view["target"]) - cam.location
            cam.rotation_euler = delta.to_track_quat("-Z", "Y").to_euler()
            cam.data.type = "PERSP"
            cam.data.sensor_fit = "HORIZONTAL"
            cam.data.lens = cam.data.sensor_width * delta.length / view["width_m"]
            cam.data.clip_start, cam.data.clip_end = .005, max(100., 2.*delta.length + view["width_m"])
        assert cam.type == "CAMERA" and (cam.location - Vector(view["eye"])).length < .0001
        distance = (Vector(view["target"]) - cam.location).length
        assert math.isclose(distance * cam.data.sensor_width / cam.data.lens, view["width_m"], abs_tol=.0001)
        if not create:
            xy = world_to_camera_view(scene, cam, Vector(view["target"]))
            assert abs(xy.x - .5) < .001 and abs(xy.y - .5) < .001 and xy.z > 0
    assert scene.camera.name == views[0]["label"]
    return views


def prepare(_scene):
    import bpy
    scene = bpy.context.scene
    raw = Path(os.environ['YANQING_159_RAW'])
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
    aliases = read_file(Path(os.environ['YANQING_159_GROUPS']))['original_names']
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
    aliases = read_file(Path(os.environ['YANQING_159_GROUPS']))['original_names']
    assert all(scene.objects[name]['authored_group_name'] == original for name, original in aliases.items())
    data = attribution(raw)
    assert all(scene[k] == v for k, v in data.items())
    report['yanqing_159'] = dict(metadata=data, raw_sha256=digest(raw), editable_groups=groups,
                                material_factors=colours, textured_materials=materials, cameras=cameras(scene, False, raw))
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    phase = os.environ['YANQING_159_STAGE']
    if phase == 'make':
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(prepare))
    elif phase == 'reopen':
        verify(*map(Path, sys.argv[sys.argv.index('--') + 1:]))
    else:
        raise ValueError(phase)
