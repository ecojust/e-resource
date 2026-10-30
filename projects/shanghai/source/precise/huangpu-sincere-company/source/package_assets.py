"""Package the Sincere Company and Moxing Tower exterior candidate without asserting acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess


ID = 'huangpu-sincere-company'


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
        'name': '先施公司历史主楼与摩星塔外观候选',
        'status': 'standalone-exterior-candidate-not-geographically-registered',
        'subject': 'Sincere Company historic main building and southeast Moxing Tower',
        'tower_identity': 'Moxing Tower (摩星塔), Sincere Company (先施公司)',
        'tower_location': 'southeast corner',
        'nominal_body_width_design_estimate_m': 100,
        'nominal_body_depth_design_estimate_m': 68,
        'outer_envelope_including_projection_design_estimate_m': {
            'width': 102.1,
            'depth': 70.05,
            'height': 51.3,
        },
        'body_height_design_estimate_m': 30.6,
        'tower_cap_height_design_estimate_m': 47.3,
        'finial_top_height_design_estimate_m': 51.3,
        'height_endpoints_verified': False,
        'all_plan_dimensions_estimated': True,
        'all_tower_dimensions_estimated': True,
        'modeled_body_design_layers': {'principal_body': 7, 'east_north_wing': 5},
        'east_north_wing_roof_height_design_estimate_m': 21.8,
        'east_north_wing_transition_boundary_estimated': True,
        'modeled_layers_are_surveyed_floor_levels': False,
        'official_body_description': 'Seven storeys and over 30 m high',
        'official_street_frontage_references_m': {'Nanjing Road': 66, 'Zhejiang Road': 61},
        'map_footprint_reference_m': {'width': 106, 'depth': 75},
        'frontage_full_extent_and_map_footprint_reconciled': False,
        'map_footprint_used_as_measured_plan': False,
        'tower_design': 'Three open pavilions: square, smaller square, round; lower clock stage',
        'historic_main_building_only': True,
        'modern_advertisements_modeled': False,
        'interiors_modeled': False,
        'neighboring_buildings_modeled': False,
        'unverified_courtyard_modeled': False,
        'rear_and_roof_estimated': True,
        'geographically_registered': False,
        'map_replacement': False,
        'walk_integration': False,
        'photos_embedded': False,
        'geometry_license': 'MIT',
        'original_geometry': True,
        'complete_photo_reconstruction_accepted': False,
        'reference_photographs': [
            {'period': '2010-05-07', 'author': 'Pyzhou', 'license': 'GFDL 1.2 or later', 'pixels_embedded': False},
            {'period': '2013-12-19', 'author': 'Livelikerw', 'license': 'CC BY-SA 3.0', 'pixels_embedded': False},
            {'period': '2024-04-24', 'author': 'Chainwit.', 'license': 'CC BY 4.0', 'pixels_embedded': False},
        ],
        'estimated': (
            'The 100 x 68 m body, 30.6 m body height, 47.3 m tower cap and '
            '51.3 m finial top are chosen design estimates. Official descriptions '
            'of seven storeys and over 30 m height, 66 m / 61 m street-frontage '
            'lengths, the complete historical extent and the 106 x 75 m map '
            'footprint remain unreconciled. The principal body has seven design '
            'layers and the east-north wing has five with an estimated 21.8 m '
            'roof and estimated transition boundary. Tower dimensions, pavilion '
            'forms, clocks, openings, '
            'facade details, rear elevations and roof are estimated. Modern '
            'advertisements, interiors, neighboring buildings and an unverified '
            'courtyard are excluded.'
        ),
        'source_candidate_metadata': document(args.raw)['extras'],
        'assets': assets,
    }
    (args.out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
