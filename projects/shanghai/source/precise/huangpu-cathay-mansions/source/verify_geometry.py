"""Independently check Cathay Mansions historic main block author solids, exported surfaces and four assets. MIT.

Raw/LOD: --assets /workspace/cathay-build --out .../geometry.json
Packaged: --assets .../huangpu-cathay-mansions --out .../packaged.json
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
AUTHOR_PARTS = {}


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
    assert meta['id'] == ID == 'huangpu-cathay-mansions'
    assert meta['status'] == 'exterior-candidate-with-estimated-geographic-placement'
    assert meta['current_address'] == '长乐路109号'
    assert meta['documented_storey_height_alternatives'] == [{'storeys':14,'height_m':57.0},{'storeys':13,'height_m':65.0}]
    assert meta['model_selected_architectural_top_m'] == 57.0
    assert meta['model_main_bar_layers']==13 and meta['model_rooftop_layers']==1
    assert not meta['height_endpoints_verified'] and meta['all_plan_dimensions_estimated']
    assert meta['all_floor_layer_datums_estimated'] and meta['floor_layer_allocation_is_author_interpretation']
    assert meta['south_and_northwest_photo_guided'] and not meta['east_elevation_photo_verified']
    assert meta['unseen_roof_is_author_closure'] and not meta['closed_courtyard_claimed']
    assert not meta['adjacent_low_hall_and_other_compound_blocks_modeled']
    assert not meta['photos_embedded'] and not meta['map_replacement'] and not meta['interiors_modeled']
    assert not meta['commercial_signs_modeled'] and not meta['original_1929_state_claimed']
    assert meta['local_origin_wgs84'] == [121.4562656354953,31.222458278353752]


def authored(lod, export_reference=False):
    builder, meta, features = build(lod)
    AUTHOR_PARTS[lod] = builder.parts
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
        assert mesh.bounds[1,0] <= 32.40+1e-6, ('East boundary exceeded',part['label'],mesh.bounds.tolist())
        triangles += len(mesh.faces)
        volumes.append(float(mesh.volume))
        points.extend(mesh.bounds)
        labels.append(part['label'])
        if any(token in part['label'] for token in ('roof', 'crown', 'south-projecting-bay', 'main-ground-slab', 'central-vertical-strip', 'north-wing-small')):
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
        with tempfile.TemporaryDirectory(prefix='cathay-lod-reference-') as temporary:
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
    assert features['window_openings']==605
    assert features['south_bay_columns']==2 and features['north_projecting_wings']==2
    assert features['north_gaps_preserved'] and not features['photos_embedded']
    assert not features['adjacent_low_hall_and_other_compound_blocks_modeled']
    labels=[part['label'] for part in builder.parts]
    for token in ['south-projecting-bay-0','south-projecting-bay-1','stepped-pale-surround',
                  'north-wing-central-vertical-strip','north-wing-small-stepped-head',
                  'crown-geometric-relief','main-roof-follows-notched-footprint']:
        assert any(token in label for label in labels), token


def diagnose_component_junctions(issues, lod):
    """Accept only frozen, individually traced two-component contact edges.

    gltfpack may weld equal position/normal vertices from independent solids.
    A material batch then has different index adjacency even when its exact
    oriented surface multiset is unchanged. The caller first proves that exact
    multiset equality; this function additionally proves each ambiguous edge
    belongs to the two expected independently closed positive author solids.
    """
    register_path=Path(__file__).with_name('component-junctions.json')
    register=json.loads(register_path.read_text())
    assert register['id']==ID
    assert register['build_model_sha256']==hashlib.sha256(Path(__file__).with_name('build_model.py').read_bytes()).hexdigest()
    def edge_key(material,edge):
        return (material,tuple(sorted(tuple(float(v) for v in point) for point in edge)))
    expected={edge_key(row['material'],row['edge']):row for row in register['junctions']}
    actual={edge_key(issue['material'],edge) for issue in issues for edge in issue['edge_positions_glb']}
    assert actual==set(expected), ('Unknown or changed packed component junctions',actual-set(expected),set(expected)-actual)
    owners={key:[] for key in actual}
    for index,part in enumerate(AUTHOR_PARTS[lod]):
        if part['material'] not in {key[0] for key in actual}:continue
        vertices=np.asarray(part['vertices'])[:,[0,2,1]]*np.array([1,1,-1])
        vertices=np.asarray(vertices,dtype='<f4')
        seen=set()
        for triangle in part['triangles']:
            for a,b in zip(triangle,[triangle[1],triangle[2],triangle[0]]):
                key=edge_key(part['material'],[vertices[a],vertices[b]])
                if key in owners and key not in seen:
                    owners[key].append({'part_index':index,'label':part['label'],'material':part['material'],
                                        'individually_closed_positive_winding_checked':True})
                    seen.add(key)
    for key,parts in owners.items():
        assert len(parts)==2,('Unexpected owner count',key,parts)
        assert sorted(p['label'] for p in parts)==sorted(p['label'] for p in expected[key]['parts']),('Unexpected component owners',key,parts)
    for issue in issues:
        keys=sorted({edge_key(issue['material'],edge) for edge in issue['edge_positions_glb']})
        issue['classification']='Explicit coincident component junctions after packing; global aggregate manifold not claimed'
        issue['fixed_junction_register_sha256']=hashlib.sha256(register_path.read_bytes()).hexdigest()
        issue['author_component_junctions']=[{'edge_positions_glb':key[1],'owners':owners[key]} for key in keys]
        issue['exact_oriented_surface_multiset_preserved']=True
        issue['explanation']='The two listed author components are individually closed, consistently wound and positive-volume. Their coincident edge receives packed shared indices. Exact FLOAT32 oriented triangle equivalence proves the complete serialized surfaces are unchanged; the aggregate is not asserted to be one Boolean-unioned manifold.'
    return issues


# Fixed feature locations selected before native review/packaging. They do not
# derive their expected surfaces from the mesh being tested.
RECESS_PROBES = [{'group': 'north-notch-side-4', 'point': [23.55, 9.18, 16.92], 'normal': [1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-notch-side-10', 'point': [23.55, 9.18, 40.919999999999995], 'normal': [1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-wing-tip-4', 'point': [20.6152, 15.56, 16.92], 'normal': [0.0, 1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-wing-tip-10', 'point': [20.6152, 15.56, 40.919999999999995], 'normal': [0.0, 1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-notch-side-4', 'point': [10.95, 13.030000000000001, 16.92], 'normal': [-1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-notch-side-10', 'point': [10.95, 13.030000000000001, 40.919999999999995], 'normal': [-1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-notch-side-4', 'point': [-11.45, 9.18, 16.92], 'normal': [1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-notch-side-10', 'point': [-11.45, 9.18, 40.919999999999995], 'normal': [1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-wing-tip-4', 'point': [-13.955799999999996, 15.56, 16.92], 'normal': [0.0, 1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-wing-tip-10', 'point': [-13.955799999999996, 15.56, 40.919999999999995], 'normal': [0.0, 1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-notch-side-4', 'point': [-22.1, 13.030000000000001, 16.92], 'normal': [-1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'north-notch-side-10', 'point': [-22.1, 13.030000000000001, 40.919999999999995], 'normal': [-1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'west-wide-7', 'point': [-32.6, 3.1430000000000007, 28.92], 'normal': [-1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'west-wide-7', 'point': [-32.6, -2.2874999999999996, 28.92], 'normal': [-1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'west-wide-7', 'point': [-32.6, -8.257, 28.92], 'normal': [-1.0, -0.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'south-flat-4', 'point': [-29.659, -10.95, 16.92], 'normal': [0.0, -1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'south-flat-10', 'point': [-29.659, -10.95, 40.919999999999995], 'normal': [0.0, -1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'south-bay-oblique', 'point': [-21.533252886265494, -11.887742444797734, 32.91], 'normal': [-0.8061322667206139, -0.5917353872736405, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'south-bay-front', 'point': [-19.6892, -12.26, 32.91], 'normal': [0.0, -1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'south-bay-oblique', 'point': [-18.323252886265493, -11.692257555202264, 32.91], 'normal': [0.8061322667206139, -0.5917353872736405, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'south-bay-oblique', 'point': [18.466747113734506, -11.887742444797734, 32.91], 'normal': [-0.8061322667206139, -0.5917353872736405, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'south-bay-front', 'point': [20.3108, -12.26, 32.91], 'normal': [0.0, -1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'south-bay-oblique', 'point': [21.676747113734507, -11.692257555202264, 32.91], 'normal': [0.8061322667206139, -0.5917353872736405, 0.0], 'depth': 0.3, 'material': 'recessed glass'}, {'group': 'central-crown-window', 'point': [0.19, -8.5, 53.33], 'normal': [0.0, -1.0, 0.0], 'depth': 0.3, 'material': 'recessed glass'}]


def surface_probes(meshes, lod=False):
    probes=[]
    def enu(p):return [p[0],p[2],-p[1]]
    for item in RECESS_PROBES:
        normal=np.array(item['normal']);point=np.array(item['point'])
        probes.append({'group':item['group'],'origin_glb':enu(point+normal*8.),
                       'direction_glb':enu(-normal),'material':item['material'],
                       'expected_distance_m':8.+item['depth'],'tolerance':4e-5})
    # Real empty north notches must stay empty at all heights, roof included.
    for name,x in [('northwest-open-notch',-27.),('north-central-open-gap',0.),('northeast-open-notch',28.)]:
        probes.append({'group':name,'origin_glb':enu([x,12.,70.]),'direction_glb':[0.,-1.,0.],'open':True})
    for name,point,plane,material in [
            ('main-roof-positive-control',[-27.,0.,70.],52.1,'roof closure estimate'),
            ('north-wing-roof-positive-control',[-20.,10.,70.],52.1,'roof closure estimate'),
            ('small-central-crown-roof',[0.,0.,70.],56.25,'roof closure estimate')]:
        probes.append({'group':name,'origin_glb':enu(point),'direction_glb':[0.,-1.,0.],
                       'plane_axis':1,'plane':plane,'material':material,'tolerance':4e-5})
    probes.append({'group':'brick-between-openings-positive-control',
                   'origin_glb':enu([-27.1,-18.95,16.92]),'direction_glb':enu([0.,1.,0.]),
                   'material':'brown brick','expected_distance_m':8.0,'tolerance':4e-5})
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
    with tempfile.TemporaryDirectory(prefix='cathay-verify-') as temporary:
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
            if adjacency_exceptions:
                assert compressed, 'Raw per-component vertices unexpectedly share packed indices'
                adjacency_exceptions=diagnose_component_junctions(adjacency_exceptions,role=='lod')
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
                            'known_component_junctions_only': True,
                            'global_boolean_union_manifold_claimed': False,
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
                            'height_basis': 'Official 14-storey/57m and 13-storey/65m alternatives have undefined endpoints. The author selects 57m maximum, 52.1m main roof and 13+1 floor allocation. Every model datum is estimated, not surveyed.',
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
