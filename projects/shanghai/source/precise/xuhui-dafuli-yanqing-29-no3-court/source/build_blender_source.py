"""Install and reopen the Dafu Li physical brick surfaces, including their tangent-space normals."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = next(p for p in SOURCE.parents if (p / 'tools/verify_editable_model.py').is_file())
sys.path.insert(0, str(SOURCE))
from court_finishes import FILENAMES, NORMAL_FILENAMES

verified = PROJECT / 'source/precise/xuhui-huashan-823-827-stair-loggia/source/build_blender_source.py'
spec = importlib.util.spec_from_file_location('shanghai_native_surface_io', verified)
native = importlib.util.module_from_spec(spec)
paths = sys.path.copy()
try:
    spec.loader.exec_module(native)
finally:
    sys.path[:] = paths
native.SOURCE = SOURCE
helpers = native.helpers
helpers.SOURCE = SOURCE
helpers.MODEL_ID = SOURCE.parent.name
helpers.UV = 'Dafu Li architectural UV'
native.NODE = 'Dafu Li brick colour'
NORMAL_NAME = 'Dafu Li brick normal texture'
TANGENT_NAME = 'Dafu Li pointing relief'
used_textures, digest = native.used_textures, native.digest


def attribution(raw):
    meta = helpers.raw_document(raw)['extras']
    if (meta.get('id') != helpers.MODEL_ID or meta.get('photos_embedded') is not False
            or not meta.get('geometry_license') or not meta.get('texture_license')
            or meta.get('plate_outline_license',meta.get('photo_reference_license')) != 'CC BY-SA 4.0'):
        raise ValueError('Dafu Li asset lacks its identifier or authorship declarations')
    if not (meta.get('source') and (meta.get('photo_reference') or meta.get('photo_source'))
            and (meta.get('photographer') or meta.get('photo_author')) and meta.get('photo_reference_license')
            and meta.get('camera_views')):
        raise ValueError('Missing photographic provenance or architectural cameras')
    return {k: v for k, v in meta.items() if isinstance(v, (bool, str, int, float))}


native.attribution = attribution


def brick_bindings(raw):
    data = raw.read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + size])
    used = {p['material'] for mesh in doc['meshes'] for p in mesh['primitives']}
    result = {}
    for index in sorted(used):
        mat = doc['materials'][index]
        name = mat['name']
        if name not in FILENAMES:
            continue
        info = {}
        for key, binding, filename in [('colour', mat['pbrMetallicRoughness']['baseColorTexture'], FILENAMES[name]),
                                       ('normal', mat['normalTexture'], NORMAL_FILENAMES[name])]:
            tex = doc['textures'][binding['index']]
            sampler = doc.get('samplers', [{}])[tex.get('sampler', 0)]
            image = doc['images'][tex['source']]
            view = doc['bufferViews'][image['bufferView']]
            start = 28 + size + view.get('byteOffset', 0)
            image_bytes = data[start:start + view['byteLength']]
            if (image_bytes != (SOURCE / filename).read_bytes() or image['mimeType'] != 'image/png'
                    or sampler.get('wrapS', 10497) != 10497 or sampler.get('wrapT', 10497) != 10497):
                raise ValueError(f'Unexpected {key} image or wrapping in {name}')
            info[key] = dict(filename=filename, sha256=hashlib.sha256(image_bytes).hexdigest(),
                             texcoord=binding.get('texCoord', 0), scale=binding.get('scale', 1.))
        if info['colour']['texcoord'] != info['normal']['texcoord'] or not (info['normal']['scale'] > 0):
            raise ValueError(f'Brick relief must follow the same UV set at its authored strength: {name}')
        result[name] = info
    if set(result) != {doc['materials'][i]['name'] for i in used}.intersection(FILENAMES):
        raise ValueError('The 42 Dafu Li asset must contain the three observed brick finishes')
    return result


def prepare(scene):
    import bpy
    native.prepare(scene)
    raw = Path(os.environ['ARCHITECTURAL_NATIVE_RAW'])
    for name, binding in brick_bindings(raw).items():
        nodes = bpy.data.materials[name].node_tree.nodes
        links = bpy.data.materials[name].node_tree.links
        colour = nodes[native.NODE]
        tangent = nodes.new('ShaderNodeNormalMap')
        tangent.name = TANGENT_NAME
        tangent.space = 'TANGENT'
        tangent.uv_map = helpers.UV
        tangent.inputs['Strength'].default_value = binding['normal']['scale']
        tex = nodes.new('ShaderNodeTexImage')
        tex.name = NORMAL_NAME
        image = bpy.data.images.load(str(SOURCE / binding['normal']['filename']), check_existing=True)
        image.colorspace_settings.name = 'Non-Color'
        image.pack()
        image.filepath = '//' + binding['normal']['filename']
        tex.image, tex.extension = image, 'REPEAT'
        shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
        links.new(colour.inputs['Vector'].links[0].from_socket, tex.inputs['Vector'])
        links.new(tex.outputs['Color'], tangent.inputs['Color'])
        links.new(tangent.outputs['Normal'], shader.inputs['Normal'])


def verify(blend, raw, out):
    import bpy
    native.verify(blend, raw, out)
    report = native.read_file(out)
    checked = {}
    for name, binding in brick_bindings(raw).items():
        nodes = bpy.data.materials[name].node_tree.nodes
        tex, tangent, colour = nodes[NORMAL_NAME], nodes[TANGENT_NAME], nodes[native.NODE]
        shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
        assert tex.image.colorspace_settings.name == 'Non-Color' and colour.image.colorspace_settings.name == 'sRGB'
        assert tex.extension == colour.extension == 'REPEAT'
        assert tex.inputs['Vector'].links[0].from_node == colour.inputs['Vector'].links[0].from_node
        assert tangent.space == 'TANGENT' and tangent.uv_map == helpers.UV
        assert tangent.inputs['Strength'].default_value == binding['normal']['scale']
        assert tangent.inputs['Color'].links[0].from_node == tex and shader.inputs['Normal'].links[0].from_node == tangent
        actual = hashlib.sha256(bytes(tex.image.packed_file.data)).hexdigest()
        assert actual == binding['normal']['sha256']
        checked[name] = dict(packed_normal_sha256=actual, packed_colour_sha256=binding['colour']['sha256'],
                             colour_space=colour.image.colorspace_settings.name, normal_colour_space=tex.image.colorspace_settings.name,
                             same_uv=helpers.UV, tangent_space=tangent.space, strength=tangent.inputs['Strength'].default_value,
                             extension=tex.extension, connected_to_principled_normal=True)
    report['architectural_source']['brick_normals'] = checked
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    phase = os.environ['ARCHITECTURAL_NATIVE_STAGE']
    if phase == 'make':
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(prepare))
    elif phase == 'reopen':
        verify(*map(Path, sys.argv[sys.argv.index('--') + 1:]))
    else:
        raise ValueError(phase)
