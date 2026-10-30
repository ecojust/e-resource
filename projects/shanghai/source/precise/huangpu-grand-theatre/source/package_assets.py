"""Package the bounded Grand Theatre candidate without asserting acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess


ID = 'huangpu-grand-theatre'


def document(path):
    data = path.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20 + length])


def preserve_candidate_metadata(path, source):
    # gltfpack omits top-level extras even with -ke. Restore the candidate scope
    # and limits without changing the packed binary mesh data.
    data = path.read_bytes()
    old_length = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + old_length])
    doc['extras'] = document(source)['extras']
    payload = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    payload += b' ' * ((-len(payload)) % 4)
    tail = data[20 + old_length:]
    path.write_bytes(
        struct.pack('<4sII', b'glTF', 2, 20 + len(payload) + len(tail))
        + struct.pack('<II', len(payload), 0x4E4F534A) + payload + tail
    )
    assert document(path)['extras'] == document(source)['extras']


def record(path):
    data = path.read_bytes()
    assert 0 < len(data) < 100_000_000
    result = {'file': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if path.suffix == '.glb':
        doc = document(path)
        assert not doc.get('images'), 'Reference images must not be embedded'

        def count_node(index):
            node = doc['nodes'][index]
            own = sum(
                doc['accessors'][primitive['indices']]['count'] // 3
                for primitive in doc['meshes'][node['mesh']]['primitives']
            ) if 'mesh' in node else 0
            return own + sum(count_node(child) for child in node.get('children', []))

        result['triangles'] = sum(count_node(index) for index in doc['scenes'][doc.get('scene', 0)]['nodes'])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--lod', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--gltfpack', required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    assets = {}
    for role, source, suffix in [('raw', args.raw, '-raw.glb'), ('native', args.native, '.blend')]:
        dest = args.out / (ID + suffix)
        if source.resolve() != dest.resolve():
            shutil.copyfile(source, dest)
        assets[role] = record(dest)
    for role, source, suffix in [('full', args.raw, '-web.glb'), ('lod', args.lod, '-lod.glb')]:
        dest = args.out / (ID + suffix)
        subprocess.run([
            args.gltfpack, '-i', str(source), '-o', str(dest),
            '-cc', '-noq', '-vnf', '-km', '-kn', '-ke',
        ], check=True)
        preserve_candidate_metadata(dest, source)
        assets[role] = record(dest)
        assert assets[role]['triangles'] == record(source)['triangles']
    manifest = {
        'id': ID,
        'name': '上海大光明电影院街面入口灯塔与相邻弧形转角外观候选',
        'status': 'standalone-partial-exterior-candidate-not-geographically-registered',
        'subject': 'Grand Theatre cinema at 216 Nanjing West Road',
        'design_height_m': 30.5,
        'alternate_height_reference_m': 16,
        'height_interpretation_unresolved': True,
        'height_endpoints_verified': False,
        'width_design_estimate_m': 23.85,
        'depth_including_canopy_design_estimate_m': 9.32,
        'all_plan_dimensions_estimated': True,
        'street_entrance_light_tower_and_adjacent_curved_return_only': True,
        'rear_auditorium_modeled': False,
        'full_roof_modeled': False,
        'whole_shop_strip_modeled': False,
        'geographically_registered': False,
        'map_replacement': False,
        'walk_integration': False,
        'photos_embedded': False,
        'geometry_license': 'MIT',
        'original_geometry': True,
        'complete_photo_reconstruction_accepted': False,
        'reference_photo_period': '2010 photograph plus undated historic and repaired night views; mixed periods',
        'single_period_reconstruction': False,
        'estimated': (
            'The 30.5 m modeled height is a chosen interpretation; the alternate 16 m '
            'source statement remains unresolved and endpoints are unverified. '
            'All plan dimensions, canopy depth, curved-return extent, openings, '
            'lettering, light-tower details, upper fins and recessed screen wall, '
            'hidden surfaces and rear closure are '
            'design estimates. The rear auditorium and whole shop strip are excluded.'
        ),
        'assets': assets,
    }
    (args.out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
