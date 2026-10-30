"""Package the historic Pacific Hotel exterior candidate without asserting acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess


ID = 'huangpu-pacific-hotel'


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
    assert document(args.raw)['extras']['id'] == ID, 'Unexpected raw candidate identity'
    assert document(args.lod)['extras']['id'] == ID, 'Unexpected LOD candidate identity'
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
        'name': '金门饭店／华安大楼历史主楼外观候选',
        'status': 'standalone-exterior-candidate-not-geographically-registered',
        'subject': "Pacific Hotel / Hua'an Building at 104 Nanjing West Road",
        'same_historic_identity': True,
        'design_height_interpretation_m': 38.16,
        'alternate_gazetteer_height_m': 36.16,
        'height_source_claims_reconciled': False,
        'clock_tower_reported_height_m': 9,
        'height_endpoints_verified': False,
        'other_scope_height_statements': [
            {
                'reported_height_m': 40.1,
                'source_period': '2026 tender mirror',
                'scope': 'south-building project quantity',
                'bound_to_historic_height': False,
            },
            {
                'reported_height_m': 24,
                'scope': 'separate north building; excluded from this candidate',
                'bound_to_historic_height': False,
            },
        ],
        'nominal_body_width_design_estimate_m': 42,
        'nominal_body_depth_design_estimate_m': 36,
        'outer_envelope_including_projection_design_estimate_m': {
            'width': 43.64,
            'depth': 38.19,
            'height': 38.16,
        },
        'all_plan_dimensions_estimated': True,
        'historic_main_building_only': True,
        'later_north_building_modeled': False,
        'estate_project_modeled': False,
        'storey_count_accounts': {
            'original': 8,
            'before_opening': 9,
            'present_day': 10,
            'different_source_and_period_accounts': True,
            'reconciled': False,
            'jointly_verified': False,
        },
        'modeled_design_layers': {'wings': 9, 'central_body': 8},
        'geographically_registered': False,
        'map_replacement': False,
        'walk_integration': False,
        'photos_embedded': False,
        'geometry_license': 'MIT',
        'original_geometry': True,
        'complete_photo_reconstruction_accepted': False,
        'reference_photo_period': '2013-12-05',
        'reference_photo_author': 'Livelikerw',
        'reference_photo_license': 'CC BY-SA 3.0',
        'estimated': (
            'The 38.16 m overall height is a chosen design interpretation; '
            'a gazetteer gives 36.16 m and the reported 9 m clock-tower height '
            'has unverified endpoints. The 40.1 m 2026 tender-mirror south-building '
            'project quantity is not bound to the historical height, while 24 m '
            'describes the separately scoped north building. Plan dimensions, '
            'I-shaped massing, recessed centre, wings, rustication, window grid, '
            'balconies, cornices, clock-tower details, roof and rear elevations are '
            'design estimates. Accounts of eight original storeys, nine before '
            'opening and ten today are different source/period accounts that remain '
            'unreconciled; nine wing layers and eight central-body layers are modeling '
            'choices. The later north building '
            'and estate project are excluded.'
        ),
        'source_candidate_metadata': document(args.raw)['extras'],
        'assets': assets,
    }
    (args.out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
