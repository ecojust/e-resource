"""Independently check Daxin historic main block author solids, exported surfaces and four assets. MIT.

Raw/LOD: --assets /workspace/daxin-build --out .../geometry.json
Packaged: --assets .../huangpu-daxin-company --out .../packaged.json
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
    assert meta['id'] == ID == 'huangpu-daxin-company'
    assert meta['status'] == 'exterior-candidate-with-estimated-geographic-placement'
    assert meta['current_address'] == '南京东路830号'
    assert meta['documented_storeys'] == 10 and meta['documented_height_m'] == 42.3
    assert meta['model_selected_architectural_top_m'] == 42.3
    assert not meta['height_endpoints_verified'] and meta['all_plan_dimensions_estimated']
    assert meta['all_floor_layer_datums_estimated'] and meta['floor_layer_allocation_is_author_interpretation']
    assert not meta['north_and_east_elevations_photo_verified'] and meta['unseen_roof_is_author_closure']
    assert not meta['courtyard_configuration_verified']
    assert not meta['modern_north_B_building_modeled'] and not meta['modern_east_C_building_modeled']
    assert not meta['photos_embedded'] and not meta['map_replacement'] and not meta['interiors_modeled']
    assert not meta['commercial_signs_modeled'] and not meta['original_1936_state_claimed']
    assert meta['local_origin_wgs84'] == [121.47027547958102,31.237025440662855]


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
        assert mesh.bounds[1,1] <= 28.34483246364317+1e-6, ('North neighbor boundary exceeded',part['label'],mesh.bounds.tolist())
        triangles += len(mesh.faces)
        volumes.append(float(mesh.volume))
        points.extend(mesh.bounds)
        labels.append(part['label'])
        if any(token in part['label'] for token in ('roof', 'gallery', 'crown', 'rounded-drop', 'round-shelf', 'spindle', 'ground-floor')):
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
        with tempfile.TemporaryDirectory(prefix='daxin-lod-reference-') as temporary:
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
            'semantic_part_bounds_model_enu': semantic_bounds,
            'feature_counts': {key: value for key, value in features.items()
                               if isinstance(value, (int, float, bool))}}


def subject_features(builder, meta, features, semantic_bounds):
    assert features['window_openings'] == 538
    assert features['gallery_openings'] == 7 and features['crown_openings'] == 54
    assert features['north_east_and_inner_roof_estimated'] and not features['photos_embedded']
    assert [x['openings'] for x in features['gallery_specs']] == [3,4]
    labels=[part['label'] for part in builder.parts]
    for token in ['projecting-continuous-canopy','gallery-rear-wall','true-pierced-frieze',
                  'southwest-stacked-projecting-round-shelf','southwest-central-rounded-drop',
                  'slender-vertical-pier','crown-stepped-upright']:
        assert any(token in label for label in labels), token
    assert not any('advertisement' in label or 'modern-B' in label or 'modern-C' in label for label in labels)


def surface_probes(meshes, lod=False):
    # Fixed sample coordinates selected before packaging. Rays interrogate the
    # complete serialized mesh, including potential occluders from other parts.
    probes=[]
    def enu(p):return [p[0],p[2],-p[1]]
    def face(group,point,normal,depth,material='recessed glass'):
        origin=np.array(point)+np.array(normal)*8.
        probes.append({'group':group,'origin_glb':enu(origin),'direction_glb':enu(-np.array(normal)),
                       'material':material,'expected_distance_m':8.+depth,'tolerance':4e-5})
    west=[-.999948988700964,-.010100494835363325,0.]
    south=[.019397205775276642,-.9998118565050684,0.]
    curved=[-.8616529590104163,-.5074979588418005,0.]
    for z in [9.27,25.27]:
        face('west_window',[-26.546598206540626,2.643222447522132,z],west,.34)
        face('south_window',[5.63746989704081,-28.152896447075957,z],south,.34)
        face('rounded_corner_window',[-24.976222201585312,-23.984505098441666,z],curved,.34)
    face('deep_shop_entry',[-24.991447140350566,-23.958655509671352,2.2],curved,1.05)
    face('south_gallery_rear_wall',[9.115899183556557,-28.08541194165996,34.3],south,2.,'recessed gallery')
    face('south_gallery_rear_glass',[7.1349698970408095,-28.123843665335585,34.3],south,2.30)
    face('west_gallery_rear_wall',[-26.627347041879244,10.637357146045337,34.3],west,2.,'recessed gallery')
    face('west_gallery_rear_glass',[-26.64864907234149,12.746258161807845,34.3],west,2.30)
    face('high_corner_window',[-26.377070779207894,-14.139992858418134,38.0],west,.34)
    face('south_arch_window',[-5.160035747264038,-28.362377298377734,34.1],south,.34)
    face('west_arch_window',[-26.442222320122692,-7.689990307853183,34.1],west,.34)
    probes.append({'group':'circular_ornament_top','origin_glb':enu([-24.030921120280592,-25.508875599854733,50.]),'direction_glb':[0.,-1.,0.],
                   'material':'pale ceramic trim','plane_axis':1,'plane':42.30,'tolerance':3e-5})
    point=np.array([-26.371696969696966,-14.672,41.16]);normal=np.array(west)
    probes.append({'group':'crown_true_opening','origin_glb':enu(point+normal),'direction_glb':enu(-normal),'clear_m':2.25})
    # The nearby intact parapet skin is a positive control for the small hole.
    face('crown_solid_between_small_holes',[-26.41080808080808,-10.8,41.16],west,0.,'pale ceramic trim')
    probes.append({'group':'high_corner_roof','origin_glb':enu([-15.,-16.,50.]),'direction_glb':[0.,-1.,0.],
                   'material':'roof closure estimate','plane_axis':1,'plane':40.55,'tolerance':3e-5})
    probes.append({'group':'estimated_inner_roof','origin_glb':enu([0.,0.,50.]),'direction_glb':[0.,-1.,0.],
                   'material':'roof closure estimate','plane_axis':1,'plane':36.6,'tolerance':3e-5})
    probes.append({'group':'modern_north_block_excluded','origin_glb':enu([0.,29.,50.]),'direction_glb':[0.,-1.,0.],'open':True})
    probes.append({'group':'modern_east_block_excluded','origin_glb':enu([31.,0.,50.]),'direction_glb':[0.,-1.,0.],'open':True})
    return evaluate_probes(meshes,probes)


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
        assert not manifest['photos_embedded'] and not manifest['source_candidate_metadata']['map_replacement']
        integration = manifest['city_integration']
        assert integration['id'] == ID and integration['placement'] == 'estimated'
        assert integration['catalog'] == 'data/candidate-city-integrations.json'
        assert integration['view'] == 'index.html#landmark=' + ID + '&mode=overview'
        assert integration['map_source_correction'] == 'bounded runtime contract'
    with tempfile.TemporaryDirectory(prefix='daxin-verify-') as temporary:
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
            # Unexpected material-batch edge ambiguities require diagnosis;
            # do not silently treat an overlapping material aggregate as one solid.
            assert not adjacency_exceptions, (
                'Unexpected shared-edge winding ambiguity in Daxin historic main block material batch',
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
                            'semantic_part_bounds_model_enu': expected['semantic_part_bounds_model_enu'],
                            'height_basis': '42.3m model maximum, 36.6m gallery roof, 33m main roof and all layer datums are author interpretations. The documented 42.3m does not state its measurement endpoint; none of these authored datums is a survey.',
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
