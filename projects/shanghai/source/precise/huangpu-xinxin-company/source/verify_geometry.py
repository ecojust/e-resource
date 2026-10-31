"""Independently check Xinxin south commercial scope author solids, exported surfaces and four assets. MIT.

Raw/LOD: --assets /workspace/xinxin-build --out .../geometry.json
Packaged: --assets .../huangpu-xinxin-company --out .../packaged.json
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
    assert meta['id'] == ID == 'huangpu-xinxin-company'
    assert meta['status'] == 'partial-exterior-candidate-with-estimated-geographic-placement'
    assert meta['current_address'] == '南京东路720号'
    assert meta['documented_front_storeys'] == 7
    assert meta['model_selected_architectural_top_m'] == 37.5
    assert meta['documented_height_description'] == 'more than thirty metres; measurement endpoint unspecified'
    assert not meta['height_endpoints_verified'] and meta['all_plan_dimensions_estimated']
    assert meta['floor_layer_allocation_is_author_interpretation']
    assert meta['scope_cut_y_m'] == 15.219429812778612 and meta['author_frame_scope_cut_y_m'] == -8.
    assert not meta['scope_cut_is_surveyed_dividing_wall']
    assert meta['rear_cut_face_is_neutral_closure_not_real_elevation']
    assert not meta['northern_hotel_modeled'] and not meta['courtyard_modeled']
    assert not meta['true_front_hotel_dividing_line_verified']
    assert not meta['tower_original_1925_identity_claimed']
    assert meta['observed_current_south_tower_modeled'] and meta['documentary_1949_removal_vs_current_tower_unresolved']
    assert meta['southern_front_and_short_side_returns_only']
    assert not meta['photos_embedded'] and not meta['map_replacement']
    assert not meta['interiors_modeled'] and not meta['neighbor_buildings_modeled']
    assert meta['coordinate_rebase']['model_origin_wgs84'] == [121.47222314008322,31.237338603109322]


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
        assert mesh.bounds[1,1] <= meta['scope_cut_y_m']+1e-6, ('North scope overhang',part['label'],mesh.bounds.tolist())
        triangles += len(mesh.faces)
        volumes.append(float(mesh.volume))
        points.extend(mesh.bounds)
        labels.append(part['label'])
        if any(token in part['label'] for token in ('roof', 'pavilion', 'central-open', 'gallery', 'scope-ground', 'closed-opened-wall')):
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
        with tempfile.TemporaryDirectory(prefix='xinxin-lod-reference-') as temporary:
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
    assert features['window_openings'] == 174
    assert features['south_main_upper_windows'] == 65
    assert features['gallery_railing_panels'] == 29
    assert features['central_tower_is_open'] and features['corner_pavilions'] == 2
    assert features['north_hotel_unmodeled'] and features['scope_cut_face_has_no_windows']
    labels=[part['label'] for part in builder.parts]
    for token in ['central-open-lower','central-open-upper','entry-paired-column',
                  'southwest-corner','southeast-corner','gallery-square-column']:
        assert any(token in label for label in labels), token
    assert not any('antenna' in label or 'north-hotel' in label for label in labels)
    cut=[part for part in builder.parts if part['material']=='neutral scope cut']
    assert len(cut)==1 and not any('window' in part['label'] for part in cut)
    assert features['coordinate_rebase'] == meta['coordinate_rebase']


def surface_probes(meshes, lod=False):
    # Fixed final-model-frame sample locations. These geometry checks do not
    # promote authored dimensions or an estimated rear scope plane to surveys.
    probes=[]
    def enu(p):return [p[0],p[2],-p[1]]
    def face(group,point,normal,depth,material='recessed glass'):
        origin=np.array(point)+np.array(normal)*8.
        probes.append({'group':group,'origin_glb':enu(origin),'direction_glb':enu(-np.array(normal)),
                       'material':material,'expected_distance_m':8.+depth,'tolerance':4e-5})
    south=[-.0042914195430514964,-.9999907918167574,0]
    for height in [5.51,18.71]:
        face('south_recessed_windows',[.3331429351395268,-14.879963646431053,height],south,.32000068438182255)
    face('west_recessed_window',[-25.207512252020408,1.9430785433420152,18.71],[-1.,0.,0.],.32000068438182255)
    face('east_recessed_window',[25.15331149429076,2.5106900648514183,5.51],
         [.9999931144445879,.00371093834674288,0.],.32000068438182255)
    face('deep_main_shop_entry',[.353142793749332,-14.880049475005473,2.],south,1.4500031011051333)
    # Paired solid control on a long cream pier, beside the recessed windows.
    face('south_solid_pier',[1.790182421254,-14.886216395525,12.],south,-.1300002780301154,'pale raised trim')
    face('plain_north_scope_closure',[0.,15.219429812778612,10.],[0.,1.,0.],0.,'neutral scope cut')
    # Openings in both opposite walls must be clear across the full tower depth.
    for group,x,y,z,depth in [
        ('lower_tower_through_opening',-3.2137486342253716,-12.88063028450018,31.6,8.000017109545563),
        ('upper_tower_through_opening',-2.3804135186477082,-11.930628252741641,35.575,6.100013046028491)]:
        probes.append({'group':group,'origin_glb':enu([x,y-1.,z]),'direction_glb':enu([0.,1.,0.]),'clear_m':depth+1.})
    # Nearby columns remain solid: the tower is a frame, not an empty bbox.
    face('lower_tower_column',[-1.647078617613,-12.88063028450018,31.6],[0.,-1.,0.],0.,'warm cream plaster')
    face('upper_tower_column',[-1.230411059825,-11.930628252741641,35.575],[0.,-1.,0.],0.,'warm cream plaster')
    face('recessed_gallery_hall',[-2.2,-14.869092767232804,27.6],south,2.470005282572193,'recessed glass')
    probes.append({'group':'gallery_roof','origin_glb':enu([10.,0.,45.]),'direction_glb':[0.,-1.,0.],
                   'material':'roof stone','plane_axis':1,'plane':29.2,'tolerance':3e-5})
    probes.append({'group':'central_tower_roof','origin_glb':enu([0.,-9.,45.]),'direction_glb':[0.,-1.,0.],
                   'material':'roof stone','plane_axis':1,'plane':37.5,'tolerance':3e-5})
    probes.append({'group':'unmodeled_north_is_clear','origin_glb':enu([0.,15.72,45.]),
                   'direction_glb':[0.,-1.,0.],'open':True})
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
    with tempfile.TemporaryDirectory(prefix='xinxin-verify-') as temporary:
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
                'Unexpected shared-edge winding ambiguity in Xinxin south commercial scope material batch',
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
                            'height_basis': '37.5m tower top, 29.2m main roof and all layer datums are author interpretations of photographs and a documentary height described only as more than thirty metres; endpoint is not surveyed.',
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
