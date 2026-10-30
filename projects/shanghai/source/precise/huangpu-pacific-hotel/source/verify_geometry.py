"""Independently check Pacific author solids, exported surfaces and four assets. MIT.

Raw/LOD: --assets /workspace/pacific-build --out .../geometry.json
Packaged: --assets .../huangpu-pacific-hotel --out .../packaged.json
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
            'explanation': 'Packed vertex sharing joins coincident bottom edges of independent '
                           'closed wall/plinth solids at ground level. The composite material '
                           'batch is not one manifold solid. Exact oriented triangle multiset '
                           'equivalence verifies that no face was flipped, moved, added or lost.'}


def document(data):
    magic, version, total = struct.unpack_from('<4sII', data)
    assert magic == b'glTF' and version == 2 and total == len(data)
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4E4F534A
    return json.loads(data[20:20 + size])


def identity(meta):
    assert meta['id'] == ID
    assert meta['status'] == 'standalone-exterior-candidate-not-geographically-registered'
    assert meta['official_building_height_reference_m'] == 38.16
    assert meta['official_roof_clock_tower_reference_m'] == 9
    assert meta['all_plan_dimensions_estimated'] and not meta['height_endpoints_verified']
    assert meta['tower_base_plus_height_equation_is_interpretation']
    assert meta['height_floor_sources_unresolved']
    assert not any(meta[k] for k in ('photos_embedded', 'map_replacement',
                                    'modern_northern_hotel_building_included',
                                    'neighboring_towers_included'))


def authored(lod, export_reference=False):
    builder, meta, features = build(lod)
    identity(meta)
    triangles = 0
    volumes = []
    points = []
    labels = []
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
        exported = np.asarray(part['vertices'])[:, [0, 2, 1]] * np.array([1, 1, -1])
        by_material.setdefault(part['material'], []).append(
            np.asarray(exported, dtype='<f4')[part['triangles']])
    points = np.asarray(points)
    # Author east/north/up becomes glTF east/up/south; this preserves handedness.
    transformed = points[:, [0, 2, 1]] * np.array([1, 1, -1])
    bounds = np.array([transformed.min(0), transformed.max(0)])
    assert features['author_parts'] == len(builder.parts)
    assert features['parameters']['front_central_recess_m'] == 4
    assert features['upper_lantern_is_open'] and features['central_ninth_layer_omitted']
    assert sum(label == 'open-upper-lantern-column' for label in labels) == 8
    digests = material_triangle_digests(by_material)
    reference = None
    if export_reference:
        # Packed LOD must be compared with an actual independent uncompressed
        # export. Rebuild locally so the CLI needs no private intermediate file.
        with tempfile.TemporaryDirectory(prefix='pacific-lod-reference-') as temporary:
            path = Path(temporary) / (ID + '-lod.glb')
            record = builder.save(path, meta)
            reference_meshes = list(trimesh.load(path, force='scene', process=False).dump())
            reference_groups = {}
            for mesh in reference_meshes:
                assert mesh.is_winding_consistent
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
            'feature_counts': {key: features[key] for key in (
                'estimated_window_openings', 'connected_vertical_window_strips',
                'attic_window_openings', 'balustrade_balcony_count', 'clock_face_count')}}


def surface_probes(meshes):
    """Probe complete serialized surfaces; first hit must be the intended material.

    Coordinates were chosen after reviewing author labels and wall/window geometry.
    They avoid mullions, floor spandrels, the entrance and the three balconies.
    A hidden wall skin would intercept a glass ray; a closed upper lantern would
    intercept an open ray. Solid wall/column controls prevent an empty mesh passing.
    """
    labels = np.concatenate([np.full(len(m.faces), m.visual.material.name)
                             for m in meshes])
    mesh = trimesh.util.concatenate(meshes)
    glazing = [[x, height, 30.] for x in [-15.2, .3, 15.8]
               for height in [9.1, 12.6, 16.2, 19.8]]
    walls = [[x, 16.2, 30.] for x in [-14.03, 1.27, 16.97]]
    open_lantern = [[x, height, 30.] for x in [-.45, .45]
                    for height in [35.1, 35.6]]
    columns = [[0., 35.3, 30.], [1.34, 35.3, 30.]]
    origins = np.array(glazing + walls + open_lantern + columns)
    hits, ray_ids, face_ids = mesh.ray.intersects_location(
        origins, np.tile([0, 0, -1], (len(origins), 1)), multiple_hits=True)
    first = []
    for index, origin in enumerate(origins):
        choices = np.flatnonzero(ray_ids == index)
        if not len(choices):
            first.append(None)
            continue
        pick = choices[np.argmin(np.linalg.norm(hits[choices] - origin, axis=1))]
        first.append({'point_glb': hits[pick].tolist(),
                      'material': str(labels[face_ids[pick]])})
    glass_depths = []
    for index, result in enumerate(first[:12]):
        assert result is not None and result['material'] == 'recessed glass', (
            'Glass blocked or missing', origins[index], result)
        wall_plane = 14. if 4 <= index < 8 else 18.
        depth = wall_plane - result['point_glb'][2]
        assert .30 < depth < .35, ('Glazing not recessed', index, depth)
        glass_depths.append(depth)
    wall_hits = first[12:15]
    for plane, result in zip([18., 14., 18.], wall_hits):
        assert result is not None and result['material'] == 'pale limestone', result
        assert abs(result['point_glb'][2] - plane) < 1e-5, result
    measured_recess = [wall_hits[i]['point_glb'][2] - wall_hits[1]['point_glb'][2]
                       for i in (0, 2)]
    assert np.allclose(measured_recess, 4., atol=1e-5)
    assert all(hit is None for hit in first[15:19]), ('Lantern blocked', first[15:19])
    for result, expected in zip(first[19:], [12.49, 11.15]):
        assert result is not None and result['material'] == 'carved pale stone', result
        assert abs(result['point_glb'][2] - expected) < .03, result
    return {'direction_glb': [0, 0, -1], 'glazing_rays': 12,
            'glazing_first_hit_material': 'recessed glass',
            'glazing_recess_depth_range_m': [min(glass_depths), max(glass_depths)],
            'wall_control_rays': 3, 'front_wall_planes_glb_z_m': [18., 14., 18.],
            'central_recess_measured_from_both_wings_m': measured_recess,
            'open_upper_lantern_rays': 4, 'upper_lantern_column_control_rays': 2,
            'all_open_rays_unobstructed': True,
            'probes': [{'origin_glb': o.tolist(), 'first_hit': hit}
                       for o, hit in zip(origins, first)]}


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
    manifest_path = args.assets / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    author = {'raw': authored(False), 'lod': authored(True, export_reference=bool(manifest))}
    report = {}
    if manifest:
        assert manifest['id'] == ID and set(manifest['assets']) == {'raw', 'full', 'lod', 'native'}
        assert manifest['design_height_interpretation_m'] == 38.16
        assert manifest['historic_main_building_only'] and manifest['all_plan_dimensions_estimated']
        assert not any(manifest[k] for k in ('photos_embedded', 'map_replacement',
                                           'geographically_registered', 'height_endpoints_verified',
                                           'later_north_building_modeled', 'estate_project_modeled'))
    with tempfile.TemporaryDirectory(prefix='pacific-verify-') as temporary:
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
                    assert compressed, 'Unexpected adjacency conflict in uncompressed geometry'
                    issue = adjacency_exception(mesh)
                    assert issue['material'] == 'granite plinth'
                    assert issue['two_face_edges_same_direction'] == 24
                    assert issue['unique_geometric_edges'] == 12
                    assert np.allclose(np.asarray(issue['edge_positions_glb'])[:, :, 1], 0,
                                       atol=1e-7, rtol=0)
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
            assert abs(scene.bounds[1, 1] - 38.16) < 1e-5
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
