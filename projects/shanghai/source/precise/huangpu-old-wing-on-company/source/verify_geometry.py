"""Independently check Old Wing On author solids, exported surfaces and four assets. MIT.

Raw/LOD: --assets /workspace/wing-build --out .../geometry.json
Packaged: --assets .../huangpu-old-wing-on-company --out .../packaged.json
          --gltfpack /path/to/gltfpack --blender /path/to/blender
Checks geometric implementation, not historical accuracy or geographic acceptance.
"""
import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import trimesh

from build_model import ID, build

# Subject-specific probes below were selected from final author labels and coordinates.
VERIFY_READY = True


def oriented_triangle_digest(triangles):
    """Hash an exact FLOAT32 oriented multiset, preserving duplicate face counts.

    Only cyclic corner rotation is allowed; reversed triangles hash differently.
    Sorted byte rows remove face order dependence. No coordinate rounding or
    tolerance is used beyond the exporter's specified FLOAT32 representation.
    """
    values = np.array(triangles, dtype='<f4')
    values[values == 0] = 0  # Signed zero denotes the same geometric coordinate.
    starts = np.lexsort((values[:, :, 2], values[:, :, 1], values[:, :, 0]), axis=-1)[:, 0]
    values = values[np.arange(len(values))[:, None], (starts[:, None] + np.arange(3)) % 3]
    rows = np.ascontiguousarray(values.reshape(-1, 9)).view(np.dtype((np.void, 36))).ravel()
    return hashlib.sha256(np.sort(rows).tobytes()).hexdigest()


def material_triangle_digests(groups):
    return {name: oriented_triangle_digest(np.concatenate(arrays))
            for name, arrays in groups.items()}


def adjacency_exception(mesh):
    """Describe shared-edge ambiguity without calling an overlapping batch a solid."""
    groups = trimesh.grouping.group_rows(mesh.edges_sorted, require_count=2)
    pairs = mesh.edges[groups]
    bad = groups[~np.all(pairs[:, 0, :] == pairs[:, 1, ::-1], axis=1)]
    positions = mesh.vertices[mesh.edges[bad[:, 0]]]
    unique_edges = {tuple(sorted(tuple(point) for point in edge)) for edge in positions}
    return {'material': mesh.visual.material.name, 'triangles': len(mesh.faces),
            'signed_volume_m3': float(mesh.volume), 'two_face_edges_same_direction': len(bad),
            'unique_geometric_edges': len(unique_edges),
            'edge_positions_glb': positions.tolist(),
            'explanation': 'Shared-edge topology of an aggregate material batch differs from '
                           'a single closed manifold. Individual author solids are checked '
                           'separately. Exact oriented triangle equivalence verifies unchanged '
                           'surfaces; the recorded edge locations require case-specific diagnosis.'}


def document(data):
    magic, version, total = struct.unpack_from('<4sII', data)
    assert magic == b'glTF' and version == 2 and total == len(data)
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4E4F534A
    return json.loads(data[20:20 + size])


def identity(meta):
    assert meta['id'] == ID == 'huangpu-old-wing-on-company'
    assert meta['status'] == 'standalone-exterior-candidate-not-geographically-registered'
    assert meta['all_plan_dimensions_estimated'] and not meta['height_endpoints_verified']
    assert meta['documented_floor_count'] == 'six storeys, locally seven; two-storey roof pavilion'
    assert meta['design_plan_m'] == [66., 94.]
    assert meta['main_roof_design_m'] == 30. and meta['seventh_storey_roof_design_m'] == 34.4
    assert meta['tower_architectural_top_design_m'] == 45.8 and meta['tower_top_design_m'] == 54.
    assert meta['tower_modern_mast_top_design_m'] == 54. and not meta['tower_total_height_verified']
    assert meta['tower_official_name'] == '倚云阁' and meta['tower_common_variant'] == '绮云阁'
    assert meta['tower_solid_base_not_counted_as_open_storey'] and meta['tower_open_storeys'] == 2
    assert meta['tower_is_separate_from_northeast_curved_entrance']
    assert meta['tower_location_photo_guided_xy_unmeasured'] == [-12.5, 42.5]
    assert meta['tower_modern_photo_mast_not_claimed_historically_original']
    assert meta['local_seventh_storey_boundary_rear_and_roof_estimated']
    assert meta['rear_elevations_and_roof_junctions_estimated']
    assert not meta['photos_embedded'] and not meta['reference_photographs_embedded']
    assert not meta['map_replacement'] and not meta['continuous_ground_arcade_claimed']
    assert meta['new_wing_on_building_and_bridges_excluded']
    assert not meta['commercial_signage_and_neighboring_buildings_included']


def authored(lod, export_reference=False):
    builder, meta, features = build(lod)
    identity(meta)
    triangles = 0
    volumes = []
    points = []
    labels = []
    semantic_bounds = {}
    by_material = {}
    for part in builder.parts:
        mesh = trimesh.Trimesh(part['vertices'], part['triangles'], process=True)
        assert np.isfinite(mesh.vertices).all(), part['label']
        assert (mesh.area_faces > 1e-12).all(), part['label']
        assert mesh.is_watertight and mesh.is_winding_consistent, part['label']
        assert mesh.volume > 0, part['label']
        triangles += len(mesh.faces)
        volumes.append(float(mesh.volume))
        points.extend(mesh.bounds)
        labels.append(part['label'])
        if any(token in part['label'] for token in ('roof', 'dome', 'lantern', 'pole', 'mast-estimated', 'arcade-floor', 'arcade-soffit')):
            semantic_bounds.setdefault(part['label'], []).append(mesh.bounds.tolist())
        exported = np.asarray(part['vertices'])[:, [0, 2, 1]] * np.array([1, 1, -1])
        by_material.setdefault(part['material'], []).append(
            np.asarray(exported, dtype='<f4')[part['triangles']])
    points = np.asarray(points)
    # Author east/north/up becomes glTF east/up/south; this preserves handedness.
    transformed = points[:, [0, 2, 1]] * np.array([1, 1, -1])
    bounds = np.array([transformed.min(0), transformed.max(0)])
    assert features['author_parts'] == len(builder.parts)
    subject_features(builder, meta, features, semantic_bounds)
    digests = material_triangle_digests(by_material)
    reference = None
    if export_reference:
        # Packed LOD must be compared with an actual independent uncompressed
        # export. Rebuild locally so the CLI needs no private intermediate file.
        with tempfile.TemporaryDirectory(prefix='old-wing-on-lod-reference-') as temporary:
            path = Path(temporary) / (ID + '-lod.glb')
            record = builder.save(path, meta)
            reference_meshes = list(trimesh.load(path, force='scene', process=False).dump())
            reference_groups = {}
            for mesh in reference_meshes:
                assert np.isfinite(mesh.vertices).all() and (mesh.area_faces > 1e-12).all()
                reference_groups.setdefault(mesh.visual.material.name, []).append(mesh.triangles)
            reference_digests = material_triangle_digests(reference_groups)
            assert reference_digests == digests
            reference = {'kind': 'Temporary uncompressed GLB from current frozen build(lod=True)',
                         'file': path.name, 'bytes': record['bytes'],
                         'sha256': record['sha256'], 'triangles': record['triangles'],
                         'build_model_sha256': hashlib.sha256(
                             Path(__file__).with_name('build_model.py').read_bytes()).hexdigest(),
                         'oriented_triangle_multiset_sha256': reference_digests}
    return {'parts': len(builder.parts), 'triangles': triangles,
            'bounds_glb': bounds.tolist(), 'all_closed_positive_winding': True,
            'minimum_part_volume_m3': min(volumes), 'metadata': meta,
            'oriented_triangle_multiset_sha256': digests,
            'uncompressed_export_reference': reference,
            'semantic_part_bounds_author_enu': semantic_bounds,
            'feature_counts': {key: value for key, value in features.items()
                               if isinstance(value, (int, float, bool))}}


def subject_features(builder, meta, features, semantic_bounds):
    p = features['parameters']
    assert p['design_width_east_west_m'] == 66. and p['design_depth_north_south_m'] == 94.
    assert p['northeast_corner_radius_design_m'] == 12.4
    assert p['northeast_corner_circle_center_xy'] == [20.6, 34.6]
    assert p['northeast_curve_facets'] == 5
    assert p['design_layer_datums_m'] == [0., 5., 10., 15., 20., 25.5, 30.]
    assert p['seventh_storey_estimated_xy'] == [8., -44., 33., -22.]
    assert p['seventh_storey_roof_design_m'] == 34.4
    assert p['tower_open_pavilion_datums_design_m'] == [34., 39., 43.4]
    assert p['tower_solid_base_datums_design_m'] == [30., 34.]
    assert not p['continuous_ground_arcade_included'] and not p['invented_courtyard_included']
    assert features['window_openings'] == 520 and features['round_oculus_openings'] == 40
    assert features['continuous_ground_arcade_opening_count'] == 0
    assert features['tower_open_stage_count'] == 2
    assert len(features['tower_pavilion_through_openings']) == 8
    assert features['two_continuous_street_iron_gallery_floors_m'] == [5., 25.5]
    assert features['northeast_curved_balcony_floors_m'] == [10., 15., 20.]
    assert features['northeast_crown_and_north_tower_are_separate']
    assert features['primary_pier_min_window_clearance_design_m'] > .10
    labels = [part['label'] for part in builder.parts]
    assert labels.count('tower-stage-1-external-column') == 8
    assert labels.count('tower-stage-2-external-column') == 8
    assert abs(semantic_bounds['estimated-seventh-storey-roof'][0][1][2] - 34.4) < 1e-8
    assert abs(semantic_bounds['modern-photo-mast-estimated-top-54'][0][1][2] - 54.) < 1e-8
    assert all('round-oculus-sill' not in label for label in labels)
    assert 'tower-architectural-top-design-45-8' in labels


def surface_probes(meshes, lod=False):
    """Independent fixed author-coordinate expectations, selected after source review.

    All checks are against the full exported model, including ornaments. They
    distinguish shop glass from a fictitious open arcade, check actual holes in
    the circular oculus band and two pavilion stages, and distinguish the sixth
    storey roof from the estimated local seventh-storey mass. They do not test
    the real historical building or its unmeasured construction dimensions.
    """
    probes = []
    # The LOD deliberately omits mullions and moves its glass front by .01m.
    glass_depth = .31 if lod else .32
    def add(group, origin, direction, **checks):
        probes.append({'group': group, 'origin_glb': list(origin),
                       'direction_glb': list(direction), **checks})
    def enu(point):
        return [point[0], point[2], -point[1]]
    def facade_ray(group, xy, normal, height, material, depth=0, outward=10):
        start = np.array([xy[0]+normal[0]*outward, xy[1]+normal[1]*outward, height])
        add(group, enu(start), enu([-normal[0], -normal[1], 0]),
            material=material, expected_distance_m=outward-depth)

    # Ordinary street shop windows: avoid raw-model mullions and paired doors.
    for height in (1.5, 3.2):
        for east in (18., 7.4, .35, -6.7, -24.35):
            facade_ray('north_recessed_shop_glass', [east, 47.], [0, 1], height,
                       'recessed glass', -glass_depth)
        for north in (-30.3, -15.56, -4.5, 24.99):
            facade_ray('east_recessed_shop_glass', [33., north], [1, 0], height,
                       'recessed glass', -glass_depth)
    facade_ray('ground_solid_pier_control', [-4.7, 47.], [0, 1], 1.5, 'base stone')
    facade_ray('ground_solid_pier_control', [33., -2.857142857142856], [1, 0], 1.5, 'base stone')

    # Circular openings are real cutouts with inset glass, not dark decals.
    for east in (18.095714285714283, 7.51, -24.247142857142855):
        facade_ray('north_round_oculus_glass', [east, 47.], [0, 1], 24.14,
                   'recessed glass', -glass_depth)
    for north in (-30.36, -4.56, 24.92571428571429):
        facade_ray('east_round_oculus_glass', [33., north], [1, 0], 24.14,
                   'recessed glass', -glass_depth)
    facade_ray('oculus_surrounding_wall_control', [17.135714285714283, 47.], [0, 1], 24.04,
               'cream stone')
    facade_ray('oculus_surrounding_wall_control', [33., -3.6], [1, 0], 24.04, 'cream stone')

    # Five shallow planar facets describe the author-estimated curved NE front.
    centre = np.array([20.6, 34.6])
    radius_to_chord = 12.4 * np.cos(np.pi/20)
    for index, degrees in enumerate((9., 27., 45., 63., 81.)):
        angle = np.deg2rad(degrees)
        normal = np.array([np.cos(angle), np.sin(angle)])
        tangent = np.array([-normal[1], normal[0]])
        midpoint = centre + normal*radius_to_chord
        offset = (.2, -.6, .2, .6, .2)[index]
        for height in (1.5, 3.2):
            facade_ray('northeast_curved_shop_glass', midpoint+tangent*offset, normal,
                       height, 'recessed glass', -glass_depth)
        facade_ray('northeast_round_oculus_glass', midpoint+tangent*.15, normal, 24.14,
                   'recessed glass', -glass_depth)
        if index in (1, 3):
            # These two rays intentionally meet the paired entrance columns
            # that occlude oblique sight-lines towards the shop windows.
            xy = midpoint + tangent*(.8 if index == 1 else -.8) + normal*10
            add('northeast_entrance_column_control', enu([*xy, 1.5]),
                enu([-normal[0], -normal[1], 0]), material='carved pale stone',
                expected_distance_m=7.60, tolerance=.02)
        if index in (0, 2, 4):
            facade_ray('northeast_curved_pier_control', midpoint+tangent*1.80, normal,
                       1.5, 'base stone')
        if index == 2:
            for floor in (10., 15., 20.):
                xy = midpoint + normal*.75
                add('northeast_curved_balcony_slab', enu([*xy, floor+.45]), [0, -1, 0],
                    material='carved pale stone', plane_axis=1, plane=floor)

    # Two open pavilions, tested in both directions on both axes. Crown probes
    # remain below the cut arch maximum and above the stone balustrades.
    for height in (36.6, 38.2, 41.6, 42.2):
        for origin, direction in (([-12.5, height, -53.], [0, 0, 1]),
                                   ([-12.5, height, -32.], [0, 0, -1]),
                                   ([-23., height, -42.5], [1, 0, 0]),
                                   ([-2., height, -42.5], [-1, 0, 0])):
            add('two_pavilion_through_openings', origin, direction, open=True)
    # Adjacent pavilion stone and freestanding columns must remain present.
    for east, height, plane in ((-16.7, 36.6, -46.1), (-15.8, 41.6, -45.35)):
        add('pavilion_wall_pier_control', [east, height, -53.], [0, 0, 1],
            material='cream stone', plane_axis=2, plane=plane)
    for east, height in ((-15.86, 36.6), (-9.14, 36.6), (-15.11, 41.6), (-9.89, 41.6)):
        add('pavilion_external_column_control', [east, height, -53.], [0, 0, 1],
            material='carved pale stone')

    # Main roof and SE seventh storey are actually different planes. Air rays
    # straddle its x=8/y=-22 boundaries and avoid parapets and moulding ends.
    for east, north in ((-20., -20.), (0., 0.), (20., 10.), (-10., -35.)):
        add('main_roof_control', enu([east, north, 40.]), [0, -1, 0],
            material='roof', plane_axis=1, plane=29.985)
    for east, north in ((12., -28.), (20., -33.), (28., -40.)):
        add('seventh_storey_roof_control', enu([east, north, 40.]), [0, -1, 0],
            material='roof', plane_axis=1, plane=34.4)
        add('seventh_storey_sky_clear', enu([east, north, 34.7]), [0, 1, 0], open=True)
    for east, north in ((6., -30.), (6., -40.), (20., -20.), (28., -20.)):
        add('outside_seventh_storey_air_clear', enu([east, north, 31.2]), [0, 1, 0], open=True)
    for east, north in ((8.2, -30.), (20., -22.2), (20., -43.8), (32.8, -30.)):
        add('seventh_storey_boundary_top_control', enu([east, north, 38.]), [0, -1, 0],
            material='cream stone', plane_axis=1, plane=34.4)
    result = evaluate_probes(meshes, probes)
    result.update({'ground_shopfront_glass_depth_design_m': glass_depth,
                   'continuous_ground_arcade_claimed': False,
                   'sixth_storey_roof_interior_surface_m': 29.985,
                   'seventh_storey_roof_design_m': 34.4,
                   'curved_front_radius_and_facets_design_only': [12.4, 5]})
    return result


def evaluate_probes(meshes, probes):
    """Evaluate preselected rays against complete serialized model surfaces.

    These checks establish model behavior only. They never turn author-picked
    dimensions into observations of the real building. Material controls pair
    open-space rays with adjacent solid portions of the same authored feature.
    """
    tags = np.concatenate([np.full(len(mesh.faces), mesh.visual.material.name)
                           for mesh in meshes])
    mesh = trimesh.util.concatenate(meshes)
    origins = np.array([probe['origin_glb'] for probe in probes])
    directions = np.array([probe['direction_glb'] for probe in probes])
    assert np.allclose(np.linalg.norm(directions, axis=1), 1, atol=1e-12, rtol=0)
    hits, ray_ids, face_ids = mesh.ray.intersects_location(origins, directions, multiple_hits=True)
    counts = {}
    for index, probe in enumerate(probes):
        counts[probe['group']] = counts.get(probe['group'], 0) + 1
        candidates = np.flatnonzero(ray_ids == index)
        first = None
        if len(candidates):
            chosen = candidates[np.argmin(np.linalg.norm(hits[candidates] - origins[index], axis=1))]
            first = {'point_glb': hits[chosen].tolist(), 'material': str(tags[face_ids[chosen]]),
                     'distance_m': float(np.linalg.norm(hits[chosen] - origins[index]))}
        if probe.get('open'):
            assert first is None, ('Expected open space', probe, first)
        elif 'clear_m' in probe:
            assert first is None or first['distance_m'] > probe['clear_m'], (
                'Intended clear segment obstructed', probe, first)
        else:
            assert first is not None and first['material'] == probe['material'], (
                'Intended material absent or blocked', probe, first)
            tolerance = probe.get('tolerance', 2e-5)
            if 'plane_axis' in probe:
                assert abs(first['point_glb'][probe['plane_axis']] - probe['plane']) < tolerance, (
                    'Unexpected surface plane', probe, first)
            if 'point' in probe:
                assert np.allclose(first['point_glb'], probe['point'], atol=tolerance, rtol=0), (probe, first)
            if 'expected_distance_m' in probe:
                assert abs(first['distance_m'] - probe['expected_distance_m']) < tolerance, (
                    'Unexpected surface depth', probe, first)
        probe['first_hit'] = first
    return {'coordinates': 'glTF east/up/south, metres; all dimensions are authored model checks',
            'historical_or_survey_validation': False, 'counts': counts, 'total_rays': len(probes),
            'all_probe_conditions_passed': True, 'probes': probes}


def native_check(path, blender, raw_sha256, tmp):
    assert blender is not None, '--blender is required to inspect native images and metadata'
    output = tmp / 'native-check.json'
    expression = '''import bpy,json
from pathlib import Path
scene=bpy.context.scene
assert scene['candidate_id']==%r
meta=json.loads(scene['candidate_metadata_json'])
assert not meta['photos_embedded']
images=[im.name for im in bpy.data.images if im.type not in {'RENDER_RESULT','COMPOSITING'}]
assert not images, images
texture_nodes=[(m.name,n.name) for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE']
assert not texture_nodes, texture_nodes
assert not bpy.data.libraries
models=[bpy.data.objects[n] for n in scene['model_mesh_names']]
assert models and all(obj['source_raw_sha256']==%r for obj in models)
triangles=sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in models)
Path(%r).write_text(json.dumps({'photos_embedded':False,'image_datablocks':images,'image_texture_nodes':texture_nodes,'source_raw_sha256':%r,'model_triangles':triangles,'model_meshes':len(models),'metadata':meta,'blender':bpy.app.version_string}))
''' % (ID, raw_sha256, str(output), raw_sha256)
    result = subprocess.run([str(blender.resolve()), '--background', str(path.resolve()),
                             '--python-exit-code', '1', '--python-expr', expression],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(output.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--gltfpack', type=Path)
    parser.add_argument('--blender', type=Path)
    args = parser.parse_args()
    assert VERIFY_READY, 'Preparation only: final model metadata and surface probes pending'
    manifest_path = args.assets / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    author = {'raw': authored(False), 'lod': authored(True, export_reference=bool(manifest))}
    report = {}
    if manifest:
        assert manifest['id'] == ID and set(manifest['assets']) == {'raw', 'full', 'lod', 'native'}
        assert not manifest['photos_embedded'] and not manifest['map_replacement']
    with tempfile.TemporaryDirectory(prefix='old-wing-on-verify-') as temporary:
        tmp = Path(temporary)
        for role in (['raw', 'full', 'lod'] if manifest else ['raw', 'lod']):
            entry = manifest['assets'][role] if manifest else None
            filename = entry['file'] if entry else f'{ID}-{role}.glb'
            assert Path(filename).name == filename
            path = args.assets / filename
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            assert 0 < len(data) < 100_000_000
            if entry:
                assert entry['bytes'] == len(data) and entry['sha256'] == digest
            doc = document(data)
            identity(doc['extras'])
            expected = author['lod' if role == 'lod' else 'raw']
            assert doc['extras'] == expected['metadata'], 'Candidate metadata changed'
            assert not doc.get('images') and not doc.get('textures')
            assert all('uri' not in buffer for buffer in doc['buffers'])
            decoded = path
            compressed = 'EXT_meshopt_compression' in doc.get('extensionsRequired', [])
            if compressed:
                assert args.gltfpack, '--gltfpack is required to decode actual packed geometry'
                decoded = tmp / (role + '.glb')
                subprocess.run([str(args.gltfpack.resolve()), '-i', str(path), '-o', str(decoded),
                                '-noq', '-vnf', '-km', '-kn', '-ke'], check=True,
                               capture_output=True, text=True)
            scene = trimesh.load(decoded, force='scene', process=False)
            meshes = list(scene.dump())
            assert meshes
            minimum_normal_dot = 1.
            by_material = {}
            adjacency_exceptions = []
            for mesh in meshes:
                assert np.isfinite(mesh.vertices).all()
                assert (mesh.area_faces > 1e-12).all()
                assert mesh.volume > 0
                by_material.setdefault(mesh.visual.material.name, []).append(mesh.triangles)
                if not mesh.is_winding_consistent:
                    issue = adjacency_exception(mesh)
                    adjacency_exceptions.append(issue)
                dots = np.einsum('ijk,ik->ij', mesh.vertex_normals[mesh.faces], mesh.face_normals)
                minimum_normal_dot = min(minimum_normal_dot, float(dots.min()))
                assert dots.min() > .99, ('Exported normal opposes winding', role, dots.min())
            # This candidate must not inherit the generic verifier's allowance
            # for batch-edge ambiguities. The initial NE parapet overlap was
            # diagnosed and removed; all published material batches must now
            # have consistent adjacency winding as well as exact face digests.
            assert not adjacency_exceptions, (
                'Unexpected shared-edge winding ambiguity in Old Wing On material batch',
                role, adjacency_exceptions)
            digests = material_triangle_digests(by_material)
            assert digests == expected['oriented_triangle_multiset_sha256'], (
                'Serialized oriented triangles differ from authored FLOAT32 faces', role)
            if role == 'full':
                assert digests == report['raw']['oriented_triangle_multiset_sha256']
                orientation_reference = {'kind': 'Actual uncompressed packaged raw GLB',
                                         'file': report['raw']['file'],
                                         'sha256': report['raw']['sha256'],
                                         'triangles': report['raw']['triangles']}
            elif role == 'lod' and manifest:
                orientation_reference = expected['uncompressed_export_reference']
                assert digests == orientation_reference['oriented_triangle_multiset_sha256']
            else:
                orientation_reference = {'kind': 'Author parts transformed to serialized FLOAT32',
                                         'build_model_sha256': hashlib.sha256(
                                             Path(__file__).with_name('build_model.py').read_bytes()).hexdigest()}
            count = sum(len(mesh.faces) for mesh in meshes)
            assert count == expected['triangles']
            if entry:
                assert count == entry['triangles']
            assert np.allclose(scene.bounds, expected['bounds_glb'], atol=2e-5, rtol=0)
            assert abs(scene.bounds[1, 1] - expected['bounds_glb'][1][1]) < 1e-5
            assert abs(scene.bounds[0, 1]) < 1e-6
            report[role] = {'file': filename, 'bytes': len(data), 'sha256': digest,
                            'triangles': count, 'bounds_glb': scene.bounds.tolist(),
                            'finite_vertices': True, 'nondegenerate_faces': True,
                            'consistent_triangle_orientation': True,
                            'material_batch_adjacency_winding_consistent': not adjacency_exceptions,
                            'material_batch_adjacency_exceptions': adjacency_exceptions,
                            'oriented_triangles_exactly_match_authored_float32': True,
                            'oriented_triangle_coordinate_tolerance_m': 0,
                            'oriented_triangle_multiset_sha256': digests,
                            'oriented_triangle_counts_by_material': {
                                name: sum(len(array) for array in arrays)
                                for name, arrays in by_material.items()},
                            'oriented_triangle_reference': orientation_reference,
                            'positive_material_batch_volumes': True,
                            'minimum_face_vertex_normal_dot': minimum_normal_dot,
                            'meshopt_decoded_for_checks': compressed,
                            'author_solids_checked': expected['parts'],
                            'author_solids_closed_positive': True,
                            'author_solids_not_boolean_unioned': True,
                            'minimum_author_part_volume_m3': expected['minimum_part_volume_m3'],
                            'semantic_part_bounds_author_enu': expected['semantic_part_bounds_author_enu'],
                            'height_basis': '30 m main roof, 34.4 m local seventh roof, 45.8 m tower architectural top and 54 m modern-photo mast top are author estimates, not surveyed endpoints.',
                            'feature_counts': expected['feature_counts'],
                            'surface_probes': surface_probes(meshes, lod=role == 'lod'),
                            'candidate_metadata_preserved': True, 'photos_embedded': False}
        assert report['lod']['triangles'] < report['raw']['triangles']
        for role in report:
            assert np.allclose(report[role]['bounds_glb'], report['raw']['bounds_glb'],
                               atol=1e-5, rtol=0)
        if manifest:
            assert report['full']['triangles'] == report['raw']['triangles']
            assert manifest['source_candidate_metadata'] == author['raw']['metadata']
            entry = manifest['assets']['native']
            assert Path(entry['file']).name == entry['file']
            path = args.assets / entry['file']
            data = path.read_bytes()
            assert 0 < len(data) < 100_000_000
            assert len(data) == entry['bytes']
            assert hashlib.sha256(data).hexdigest() == entry['sha256']
            native = native_check(path, args.blender, report['raw']['sha256'], tmp)
            assert native['model_triangles'] == report['raw']['triangles']
            assert native.pop('metadata') == author['raw']['metadata']
            report['native'] = dict(entry, **native)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({role: {key: row[key] for key in ('bytes', 'sha256', 'photos_embedded')}
                      for role, row in report.items()}))


if __name__ == '__main__':
    main()
