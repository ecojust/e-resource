"""Independently check Sincere author solids, exported surfaces and four assets. MIT.

Raw/LOD: --assets /workspace/sincere-build --out .../geometry.json
Packaged: --assets .../huangpu-sincere-company --out .../packaged.json
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
    assert meta['id'] == ID == 'huangpu-sincere-company'
    assert meta['status'] == 'standalone-exterior-candidate-not-geographically-registered'
    assert meta['all_plan_dimensions_estimated']
    assert not meta['photos_embedded'] and not meta['map_replacement']
    assert meta['design_plan_m'] == [100, 68]
    assert meta['main_roof_design_m'] == 30.6 and meta['tower_top_design_m'] == 51.3
    assert not meta['height_endpoints_verified'] and not meta['tower_total_height_verified']
    assert meta['tower_name'] == 'Moxing Tower / 摩星塔' and meta['tower_is_not_yongan_qiyunge']
    assert meta['scope_conflict_unresolved'] and meta['rear_elevations_and_roof_junctions_estimated']
    assert not meta['commercial_advertising_and_neighboring_buildings_included']
    assert 'more than 30 metres' in meta['documented_main_building_height']


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
        if part['label'] in ('northeast-lower-roof-terrace', 'moxing-low-curved-cap',
                              'moxing-thin-pole-design-top-51-3',
                              'walk-through-arcade-floor', 'arcade-soffit'):
            semantic_bounds[part['label']] = mesh.bounds.tolist()
        exported = np.asarray(part['vertices'])[:, [0, 2, 1]] * np.array([1, 1, -1])
        by_material.setdefault(part['material'], []).append(
            np.asarray(exported, dtype='<f4')[part['triangles']])
    points = np.asarray(points)
    # Author east/north/up becomes glTF east/up/south; this preserves handedness.
    transformed = points[:, [0, 2, 1]] * np.array([1, 1, -1])
    bounds = np.array([transformed.min(0), transformed.max(0)])
    assert features['author_parts'] == len(builder.parts)
    parameters = features['parameters']
    assert parameters['northeast_low_wing_authored_xy'] == [20., -8., 50., 34.]
    assert parameters['northeast_low_wing_roof_design_m'] == 21.8
    assert parameters['tower_total_height_has_no_verified_source_measurement']
    assert parameters['tower_stage_forms'] == [
        'stepped clock base', 'large square arched pavilion',
        'small chamfered square arched pavilion', 'open circular columned pavilion']
    assert features['ground_arcade_opening_count'] == len(features['ground_arcade_openings']) == 52
    assert len(features['tower_square_stage_through_arches']) == 8
    assert features['tower_square_stage_column_counts_design'] == [8, 8]
    assert features['tower_round_stage_column_count_design'] == 8
    assert features['tower_open_stage_count'] == 3
    assert labels.count('moxing-open-round-pavilion-column') == 8
    assert abs(semantic_bounds['northeast-lower-roof-terrace'][1][2] - 21.8) < 1e-8
    assert abs(semantic_bounds['moxing-low-curved-cap'][1][2] - 47.3) < 1e-8
    assert abs(semantic_bounds['moxing-thin-pole-design-top-51-3'][1][2] - 51.3) < 1e-8
    digests = material_triangle_digests(by_material)
    reference = None
    if export_reference:
        # Packed LOD must be compared with an actual independent uncompressed
        # export. Rebuild locally so the CLI needs no private intermediate file.
        with tempfile.TemporaryDirectory(prefix='sincere-lod-reference-') as temporary:
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


def surface_probes(meshes):
    """Probe complete serialized geometry, with material/solid controls.

    glTF coordinates are east/up/south. The main front lies at z=34 and east
    front at x=50. Inner shop walls are 3.2 m behind the outer arcade; actual
    glass front faces add 0.32 m (raw) or 0.31 m (LOD). Tower square stages use
    axes rotated 45 degrees, while the round pavilion columns use global axes.
    All heights here are author-design checks, not measured historical heights.
    """
    tags = np.concatenate([np.full(len(mesh.faces), mesh.visual.material.name)
                           for mesh in meshes])
    mesh = trimesh.util.concatenate(meshes)
    probes = []

    def add(group, origin, direction, **check):
        probes.append({'group': group, 'origin_glb': list(origin),
                       'direction_glb': list(direction), **check})

    # Full opening plus recessed shop glass, avoiding the independently spaced
    # shop mullions. The upper probes also pass through the curved arch heads.
    for height in (1.5, 3.6):
        for east in (-3.9, 0., 4.):
            add('south_arcade_glazing', [east, height, 45.], [0, 0, -1],
                material='recessed glass', depth_axis=2, outer_plane=34.)
        for north in (2.2, 6.35, 10.5):
            add('east_arcade_glazing', [60., height, -north], [-1, 0, 0],
                material='recessed glass', depth_axis=0, outer_plane=50.)
    add('outer_arcade_pier_control', [1.00476190476, 1.5, 45.], [0, 0, -1],
        material='base stone', plane_axis=2, plane=34.)
    add('outer_arcade_pier_control', [60., 1.5, 0.], [-1, 0, 0],
        material='base stone', plane_axis=0, plane=50.)
    # The corridor must remain open longitudinally, not just normal to a facade.
    add('south_arcade_longitudinal_clear', [-35., 1.5, 32.2], [1, 0, 0], clear_m=70.)
    add('south_arcade_longitudinal_clear', [35., 1.5, 32.2], [-1, 0, 0], clear_m=70.)
    add('east_arcade_longitudinal_clear', [48.4, 1.5, 20.], [0, 0, -1], clear_m=45.)
    add('east_arcade_longitudinal_clear', [48.4, 1.5, -25.], [0, 0, 1], clear_m=45.)
    for point in ([-10., 1.5, 32.2], [48.4, 1.5, -10.]):
        add('arcade_floor_control', point, [0, -1, 0], material='roof', plane_axis=1, plane=.18)
        add('arcade_soffit_control', point, [0, 1, 0], material='roof', plane_axis=1, plane=4.31)
    # Each square pavilion is open through both opposing arch pairs. Two levels
    # in each include an arch crown; offset rays must still find a stone pier.
    s = 1 / np.sqrt(2)
    for height in (36., 37.3, 40., 41.2):
        add('square_pavilion_through_arch', [43+8*s, height, 27+8*s], [-s, 0, -s], open=True)
        add('square_pavilion_through_arch', [43-8*s, height, 27+8*s], [s, 0, -s], open=True)
    for height, offset, expected in (
            (36., 2., [46.6769552381, 36., 27.8485281134]),
            (40., 1.12, [45.4713388085, 40., 27.8874196186])):
        add('square_pavilion_pier_control',
            [43+(8+offset)*s, height, 27+(8-offset)*s], [-s, 0, -s],
            material='cream stone', point=expected)
    for east in (42.5, 43.5):
        for height in (43.4, 44.6):
            add('round_pavilion_open', [east, height, 35.], [0, 0, -1], open=True)
    for east, expected in ((43., 28.69239285), (44.52, 27.1723923)):
        add('round_pavilion_column_control', [east, 44., 35.], [0, 0, -1],
            material='carved pale stone', plane_axis=2, plane=expected, tolerance=.03)
    # Terrace faces, adjacent high roof, and low east cornice are distinct levels.
    for east, north in ((25., 0.), (35., 10.), (45., 25.)):
        add('northeast_terrace_roof', [east, 40., -north], [0, -1, 0],
            material='roof', plane_axis=1, plane=21.8)
        add('northeast_terrace_sky_clear', [east, 22.2, -north], [0, 1, 0], open=True)
    for east, north in ((-20., 0.), (0., 0.), (15., 15.)):
        add('main_roof_control', [east, 40., -north], [0, -1, 0],
            material='roof', plane_axis=1, plane=30.585)
    for north in (4., 33.1):
        add('northeast_east_cornice_top', [50.1, 40., -north], [0, -1, 0],
            material='carved pale stone', plane_axis=1, plane=21.865)
    # Catch erroneously full-height east piers above the low wing. The high
    # transition at x=20 may be hit later, beyond the checked x=60..45 segment.
    for north in (0., 4., 8., 16., 24., 30., 33.1):
        for height in (22.5, 25., 29.5):
            add('northeast_east_upper_air_clear', [60., height, -north], [-1, 0, 0], clear_m=15.)

    origins = np.array([probe['origin_glb'] for probe in probes])
    directions = np.array([probe['direction_glb'] for probe in probes])
    hits, ray_ids, face_ids = mesh.ray.intersects_location(origins, directions, multiple_hits=True)
    glass_depths = []
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
                'Clear corridor/terrace air obstructed', probe, first)
        else:
            assert first is not None and first['material'] == probe['material'], (
                'Intended material absent or blocked', probe, first)
            tolerance = probe.get('tolerance', 2e-5)
            if 'plane_axis' in probe:
                assert abs(first['point_glb'][probe['plane_axis']] - probe['plane']) < tolerance, (
                    'Unexpected surface plane', probe, first)
            if 'point' in probe:
                assert np.allclose(first['point_glb'], probe['point'], atol=tolerance, rtol=0), (probe, first)
            if 'depth_axis' in probe:
                depth = probe['outer_plane'] - first['point_glb'][probe['depth_axis']]
                assert 3.50 < depth < 3.55, ('Rear shop glass not behind arcade', probe, first)
                glass_depths.append(depth)
        probe['first_hit'] = first
    return {'coordinates': 'glTF east/up/south, metres; all heights are author design estimates',
            'counts': counts, 'total_rays': len(probes),
            'arcade_glass_depth_range_m': [min(glass_depths), max(glass_depths)],
            'south_arcade_clear_segment_m': 70., 'east_arcade_clear_segment_m': 45.,
            'northeast_terrace_roof_m': 21.8, 'main_roof_interior_surface_m': 30.585,
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
    with tempfile.TemporaryDirectory(prefix='sincere-verify-') as temporary:
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
            assert abs(scene.bounds[1, 1] - 51.3) < 1e-5  # Author estimate, not official tower height
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
                            'height_basis': '30.6 m main design roof, 21.8 m NE terrace, 47.3 m '
                                            'tower cap and 51.3 m pole top are author estimates; '
                                            'no verified total tower-height measurement.',
                            'feature_counts': expected['feature_counts'],
                            'surface_probes': surface_probes(meshes),
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
