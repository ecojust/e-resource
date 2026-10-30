"""Package the Old Wing On Company and Qiyun Pavilion exterior candidate without asserting acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess


ID = 'huangpu-old-wing-on-company'


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


def authored_bounds_enu(path):
    # Builder exports ENU geometry to glTF [east, up, -north] without node
    # transforms. Read actual accessor bounds; do not reuse nominal dimensions.
    doc = document(path)
    assert all(not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale'))
               for node in doc['nodes']), 'Unexpected transformed authored source'
    positions = [doc['accessors'][p['attributes']['POSITION']]
                 for mesh in doc['meshes'] for p in mesh['primitives']]
    lo = [min(p['min'][axis] for p in positions) for axis in range(3)]
    hi = [max(p['max'][axis] for p in positions) for axis in range(3)]
    return {'min': [lo[0], -hi[2], lo[1]], 'max': [hi[0], -lo[2], hi[1]]}


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
    metadata = document(args.raw)['extras']
    bounds = authored_bounds_enu(args.raw)
    spans = [bounds['max'][axis] - bounds['min'][axis] for axis in range(3)]
    manifest = {
        'id': ID,
        'name': '老永安公司主楼与屋顶塔楼外观候选',
        'status': 'standalone-exterior-candidate-not-geographically-registered',
        'subject': 'Old Wing On Company historic main building, 635 East Nanjing Road, and Qiyun Pavilion',
        'tower_identity': 'Qiyun Pavilion (绮云阁) in modern official sources; Yiyun Pavilion (倚云阁) in the gazetteer; no formal renaming established',
        'nominal_body_width_design_estimate_m': metadata['design_plan_m'][0],
        'nominal_body_depth_design_estimate_m': metadata['design_plan_m'][1],
        'outer_envelope_including_projection_design_estimate_m': dict(zip(('width', 'depth', 'height'), spans)),
        'authored_bounds_enu_m': bounds,
        'body_height_design_estimate_m': metadata['main_roof_design_m'],
        'tower_architectural_top_height_design_estimate_m': metadata['tower_architectural_top_design_m'],
        'modern_mast_top_height_design_estimate_m': metadata['tower_modern_mast_top_design_m'],
        'modern_mast_claimed_historically_original': False,
        'local_seventh_storey_roof_height_design_estimate_m': metadata['seventh_storey_roof_design_m'],
        'modeled_body_design_layers': {'principal_body': 6, 'local_southeast_body': 7},
        'tower_location': 'north facade, middle-west portion; separate from the northeast rounded entry corner',
        'height_endpoints_verified': False,
        'all_plan_dimensions_estimated': True,
        'all_tower_dimensions_estimated': True,
        'modeled_layers_are_surveyed_floor_levels': False,
        'official_body_description': 'Six storeys, locally seven; a two-storey roof pavilion',
        'map_footprint_used_as_measured_plan': False,
        'historic_main_building_only': True,
        'new_wing_on_company_at_627_included': False,
        'former_connecting_bridges_included': False,
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
        'reference_photographs': [{'id': 'old',
          'permanent_page': 'https://commons.wikimedia.org/w/index.php?title=File:Old_Wing_On_in_Shanghai.jpg&oldid=1248639600',
          'author': 'Legolas1024',
          'capture_date': '2011-05-06',
          'license': 'CC BY-SA 4.0',
          'pixels_embedded': False},
         {'id': 'general',
          'permanent_page': 'https://commons.wikimedia.org/w/index.php?title=File:Old_Wing_On_Company_Shanghai.JPG&oldid=1248639598',
          'author': 'Livelikerw',
          'capture_date': '2013-12-19',
          'license': 'CC BY-SA 3.0',
          'pixels_embedded': False},
         {'id': 'corner',
          'permanent_page': 'https://commons.wikimedia.org/w/index.php?title=File:Wing_On_Department_Store_%28Shanghai%29_20250501-2.jpg&oldid=1248639618',
          'author': 'Suicasmo',
          'capture_date': '2025-05-01',
          'license': 'CC0 1.0',
          'pixels_embedded': False},
         {'id': 'side',
          'permanent_page': 'https://commons.wikimedia.org/w/index.php?title=File:Wing_On_Department_Store_20251126_%28III%29.jpg&oldid=1248639627',
          'author': 'Supanut Arunoprayote',
          'capture_date': '2025-11-26',
          'license': 'CC BY 4.0',
          'pixels_embedded': False},
         {'id': 'modern',
          'permanent_page': 'https://commons.wikimedia.org/w/index.php?title=File:Wing_On_Department_Store_20251126.jpg&oldid=1248639632',
          'author': 'Supanut Arunoprayote',
          'capture_date': '2025-11-26',
          'license': 'CC BY 4.0',
          'pixels_embedded': False},
         {'id': 'north',
          'permanent_page': 'https://commons.wikimedia.org/w/index.php?title=File:Wing_On_Department_Store_20251126_%28II%29.jpg&oldid=1248639623',
          'author': 'Supanut Arunoprayote',
          'capture_date': '2025-11-26',
          'license': 'CC BY 4.0',
          'pixels_embedded': False}],
        'estimated': (
            'Plan dimensions, body and tower heights, layer datums, facade '
            'bay widths, curves, ornamental profiles, rear elevations and '
            'roof junctions are author estimates. The official six-storey '
            'body, local seventh storey and two-storey pavilion description '
            'does not establish surveyed datum levels or total tower height. '
            'The frozen map footprint is a coarse current coverage reference, '
            'not a surveyed historic plan. Modern advertisements, interiors, '
            'neighboring buildings, New Wing On Company at 627, the former '
            'connecting bridges and an unverified courtyard are excluded.'
        ),
        'source_candidate_metadata': metadata,
        'assets': assets,
    }
    (args.out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
