"""Encode the authored Yanqing Road pair and independently compare surfaces, image bytes and brick UVs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from build_model import ID, PROJECT
from build_blender_source import attribution, digest, helpers

sys.path.insert(0, str(PROJECT / 'source/precise/hongkou-gongyi-fang-975-987-sichuan-road/source'))
sys.path.insert(0, str(PROJECT / 'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from asset_rights import retain_metadata
from glb_triangles import SerialScene


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.partial')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def asset(path, triangles):
    return dict(file=path.name, bytes=path.stat().st_size, sha256=digest(path), triangles=triangles)


def check_bricks(source, decoded):
    doc = helpers.raw_document(source)
    actual = {m['name'] for m in doc['materials']
              if 'baseColorTexture' in m.get('pbrMetallicRoughness', {})}
    if actual != set(helpers.TEXTURES):
        raise ValueError(f'Unexpected set of brick finishes in {source.name}: {sorted(actual)}')
    checks = {}
    for material, image in helpers.TEXTURES.items():
        original = helpers.texture_faces(source, material)
        if original != helpers.texture_faces(decoded, material):
            raise ValueError(f'Changed oriented UV corner for {material}')
        checks[material] = dict(corners=3 * len(original), image_sha256=digest(image),
                                wrap=helpers.texture_extension(doc, material), maximum_uv_difference=0.0)
    return checks


def package(source_dir, out, gltfpack):
    out.mkdir(parents=True, exist_ok=True)
    source_raw = source_dir / 'full-source.glb'
    source_lod = source_dir / 'lod-source.glb'
    meta = attribution(source_raw)
    if attribution(source_lod) != meta:
        raise ValueError('Near and far sources have different attribution')
    raw = out / (ID + '-raw.glb')
    shutil.copyfile(source_raw, raw)
    roles = {}
    geometry = {}
    surfaces = {}
    decoder = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    for role, suffix, source in (('full', 'web', source_raw), ('lod', 'lod', source_lod)):
        encoded = out / f'{ID}-{suffix}.glb'
        decoded = out / f'decoded-{role}.glb'
        subprocess.run([gltfpack, '-i', source, '-o', encoded, '-cc', '-noq', '-vnf', '-km', '-kn', '-ke'], check=True)
        retain_metadata(encoded, source)
        subprocess.run(['node', decoder, encoded, decoded, PROJECT / 'vendor/meshopt_decoder.module.js'], check=True)
        original = SerialScene(source)
        result = SerialScene(decoded)
        oriented = original.surface_digest()
        if result.surface_digest() != oriented:
            raise ValueError(f'Encoded {role} changed oriented triangles or materials')
        if role == 'full':
            roles['raw'] = asset(raw, len(original.tri))
        roles[role] = asset(encoded, len(result.tri))
        geometry[role] = dict(source=original.asset, decoded=result.asset, oriented_surfaces=oriented)
        surfaces[role] = dict(source_sha256=digest(source), decoded_sha256=digest(decoded),
                              materials=check_bricks(source, decoded))
    manifest = dict(model_id=ID, **meta, assets=roles)
    write_json(out / 'mesh-decode-comparisons.json', geometry)
    write_json(out / 'decoded-texture-comparisons.json', surfaces)
    write_json(out / 'manifest.json', manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_dir', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--gltfpack', default=os.environ.get('GLTFPACK', 'gltfpack'))
    args = parser.parse_args()
    package(args.source_dir, args.out, args.gltfpack)
