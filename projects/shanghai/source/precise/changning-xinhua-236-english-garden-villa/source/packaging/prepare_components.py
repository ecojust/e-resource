"""Rebuild the editable parts and read every material binding from the reference GLB."""
import argparse
import base64
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from package_web import chunks


def load_source(path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("building_package_entry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(model_path, reference, output, cameras_path=None, factory='build', builder_class=None):
    module = load_source(model_path)
    if builder_class:
        builder = getattr(module, builder_class)(module.PALETTE)
        module.add_building(builder, lod=False)
    else:
        builder = getattr(module, factory)(False)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        copy = Path(temp) / 'full-source.glb'
        builder.save(copy, module.META)
        if reference.read_bytes() != copy.read_bytes():
            raise ValueError('The source did not reproduce the reference GLB')
    doc, binary = chunks(reference)
    textures, materials = {}, {}
    meta = dict(module.META)
    if cameras_path:
        meta['camera_views'] = json.loads(cameras_path.read_bytes())
    cameras = meta.get('camera_views', [])
    for view in cameras:
        if len(view['eye']) != 3 or len(view['target']) != 3 or not 0 < view['fov'] < 180:
            raise ValueError(view)
    if len({v['name'] for v in cameras}) != len(cameras):
        raise ValueError('Duplicate camera identifier')
    channels = (('texture', 'baseColorTexture'), ('normal', 'normalTexture'))
    used = {part['material'] for part in builder.parts}
    for material in doc['materials']:
        name = material['name']
        if name not in used:
            continue
        pbr = material.get('pbrMetallicRoughness', {})
        color = pbr.get('baseColorFactor', [1, 1, 1, 1])
        mat = dict(color=color[:3], alpha=color[3],
                   roughness=pbr.get('roughnessFactor', 1), metallic=pbr.get('metallicFactor', 1))
        for key, slot in channels:
            binding = pbr.get(slot) if key == 'texture' else material.get(slot)
            if not binding:
                continue
            if binding.get('texCoord', 0) != 0:
                raise ValueError('A second UV set needs explicit support')
            tex = doc['textures'][binding['index']]
            image = doc['images'][tex['source']]
            file = Path(image['name']).name
            if file != image['name'] or not file:
                raise ValueError(image)
            v = doc['bufferViews'][image['bufferView']]
            offset = v.get('byteOffset', 0)
            blob = base64.b64encode(binary[offset:offset+v['byteLength']]).decode()
            if file in textures and textures[file] != blob:
                raise ValueError('Ambiguous embedded image name: ' + file)
            textures[file] = blob
            mat[key] = file
            sampler = doc['samplers'][tex['sampler']] if 'sampler' in tex else {}
            wrap = [sampler.get(axis, 10497) for axis in ('wrapS', 'wrapT')]
            if wrap[0] != wrap[1] or wrap[0] not in (10497, 33071, 33648):
                raise ValueError(f'Unsupported independent wrap settings: {wrap}')
            mat[key+'_wrap'] = wrap[0]
            if key == 'normal':
                mat['normal_strength'] = binding.get('scale', 1.0)
        materials[name] = mat
    if used != set(materials):
        raise ValueError('Some editable materials have no corresponding GLB material')
    package = dict(metadata=meta, reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                   materials=materials, textures=textures, parts=builder.parts)
    output.write_text(json.dumps(package, ensure_ascii=False, separators=(',', ':'))+'\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('model', 'reference', 'output'):
        p.add_argument(key, type=Path)
    p.add_argument('--cameras', type=Path)
    p.add_argument('--factory', default='build')
    p.add_argument('--builder-class', help='Name of the Builder subclass when using add_building instead of a factory.')
    a = p.parse_args()
    prepare(a.model.resolve(), a.reference, a.output, a.cameras, a.factory, a.builder_class)
