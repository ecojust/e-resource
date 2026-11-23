"""Install and reopen the No. 20 entrance finishes, including their tangent-space normals."""
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
helpers.UV = 'Shaanxi 222-20 architectural UV'
native.NODE = 'No. 20 architectural surface colour'
NORMAL_NAME = 'No. 20 architectural surface normal'
TANGENT_NAME = 'No. 20 original surface relief'
used_textures, digest = native.used_textures, native.digest


def attribution(raw):
    meta = helpers.raw_document(raw)['extras']
    if meta.get('id') != helpers.MODEL_ID or meta.get('photos_embedded') is not False:
        raise ValueError('Missing architectural identity or source-image declaration')
    if not all(meta.get(k) for k in ('source', 'photo_source','photo_author','geometry_license','texture_license','camera_views')):
        raise ValueError('Missing architectural provenance, license or camera views')
    return {key:value for key,value in meta.items() if isinstance(value,(bool,str,int,float))}


native.attribution = attribution


def texture_bindings(raw):
    """Read every used PNG and binding directly from this GLB, including optional surface normals."""
    data = raw.read_bytes()
    size = struct.unpack_from('<I', data,12)[0]
    doc = json.loads(data[20:20+size])
    used = {p['material'] for mesh in doc['meshes'] for p in mesh['primitives']}
    surfaces = {}
    for index in sorted(used):
        material = doc['materials'][index]
        bindings = {}
        for channel, binding in [('colour',material.get('pbrMetallicRoughness',{}).get('baseColorTexture')),
                                 ('normal',material.get('normalTexture'))]:
            if binding is None:
                continue
            texture = doc['textures'][binding['index']]
            image = doc['images'][texture['source']]
            view = doc['bufferViews'][image['bufferView']]
            start = 28+size+view.get('byteOffset',0)
            pixels = data[start:start+view['byteLength']]
            filename = image['name']
            sampler = doc.get('samplers',[{}])[texture.get('sampler',0)]
            if (Path(filename).name!=filename or image['mimeType']!='image/png'
                    or pixels != (SOURCE/filename).read_bytes()
                    or any(sampler.get(axis,10497)!=10497 for axis in ('wrapS','wrapT'))):
                raise ValueError(f'Embedded architectural texture differs from its signed PNG: {filename}')
            bindings[channel] = dict(filename=filename,sha256=hashlib.sha256(pixels).hexdigest(),
                                     texcoord=binding.get('texCoord',0),scale=binding.get('scale',1.))
        if bindings:
            if 'colour' not in bindings or ('normal' in bindings and bindings['normal']['texcoord']!=bindings['colour']['texcoord']):
                raise ValueError('Expected a shared UV coordinate set for this architectural finish')
            surfaces[material['name']] = bindings
    return surfaces


def used_textures(raw):
    textures = {name:SOURCE / channels['colour']['filename'] for name,channels in texture_bindings(raw).items()}
    helpers.TEXTURES = textures
    return textures


native.used_textures = used_textures


def prepare(scene):
    import bpy
    native.prepare(scene)
    raw = Path(os.environ['ARCHITECTURAL_NATIVE_RAW'])
    for name, binding in texture_bindings(raw).items():
        if 'normal' not in binding:
            continue
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
    for name, binding in texture_bindings(raw).items():
        if 'normal' not in binding:
            continue
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
    report['architectural_source']['surface_normals'] = checked
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
