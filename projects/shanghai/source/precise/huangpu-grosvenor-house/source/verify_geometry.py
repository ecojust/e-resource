"""Independently check Grosvenor House historic main block author solids, exported surfaces and four assets. MIT.

Raw/LOD: --assets /workspace/grosvenor-build --out .../geometry.json
Packaged: --assets .../huangpu-grosvenor-house --out .../packaged.json
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
    assert meta['id']==ID=='huangpu-grosvenor-house'
    assert meta['status']=='exterior-candidate-with-estimated-geographic-placement'
    assert meta['current_address']=='茂名南路65－125号（名录范围）'
    assert meta['official_narrative_address']=='茂名南路59号' and not meta['address_correspondence_verified']
    assert meta['documented_storeys_including_basement']==18 and meta['documented_basements']==1
    assert meta['secondary_storey_account']=={'above_ground':18,'below_ground':3,'conflict_resolved':False}
    assert meta['model_selected_architectural_top_m']==78.0 and meta['documented_height_m']==78.0
    assert meta['model_above_ground_floor_layers']==17 and meta['model_below_ground_layers']==0
    assert not meta['height_endpoints_verified'] and meta['all_plan_dimensions_estimated']
    assert meta['all_floor_layer_datums_estimated'] and meta['floor_layer_allocation_is_author_interpretation']
    assert meta['garden_elevation_photo_guided'] and not meta['rear_elevation_photo_verified']
    assert meta['unseen_roof_is_author_closure']
    assert not meta['source_south_step_height_attribution_verified'] and not meta['shelter_equals_specific_map_step_claimed']
    for key in ['western_low_apartments_modeled','neighboring_new_jinjiang_tower_modeled',
                'photos_embedded','map_replacement','interiors_modeled','commercial_signs_modeled',
                'underground_modeled','original_1934_state_claimed']:assert not meta[key]
    assert meta['local_origin_wgs84']==[121.45728030428835,31.221260424588685]


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
        assert mesh.bounds[0,2]>=-1e-8 and mesh.bounds[1,2]<=78.0+1e-8,('Above-ground scope exceeded',part['label'],mesh.bounds.tolist())
        triangles += len(mesh.faces)
        volumes.append(float(mesh.volume))
        points.extend(mesh.bounds)
        labels.append(part['label'])
        if any(token in part['label'] for token in ('terrace-', 'crown', 'central-continuous', 'shelter', 'main-ground')):
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
        with tempfile.TemporaryDirectory(prefix='grosvenor-lod-reference-') as temporary:
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


def subject_features(builder,meta,features,semantic_bounds):
    assert features['window_openings']==761
    assert features['crown_recesses']==8 and features['shelter_glass_cells']==18
    assert len(features['terrace_levels'])==5 and features['main_above_ground_floor_layers']==17
    assert not features['underground_modeled'] and not features['photos_embedded']
    assert not features['western_low_apartments_modeled'] and not features['neighboring_new_jinjiang_tower_modeled']
    labels=[p['label'] for p in builder.parts]
    for token in ['central-continuous-pale-fin','crown-deep-groove','exposed-roof',
                  'open-plan-parapet','shelter-glass-panel','low-entrance-roof-pierced-frame-matrix']:
        assert any(token in label for label in labels),token
    assert not any('low-entrance-roof-frame-slab' in label for label in labels)


# Fixed pre-package sample locations; expected surfaces do not depend on the
# exported mesh under test. Model behavior only, not historical/survey proof.
RECESS_PROBES = [{'group': 'garden-wide-tier-0-floor-4', 'point': [-17.560074024301162, -4.2413543075312194, 17.37], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-0-floor-10', 'point': [-17.560074024301162, -4.2413543075312194, 41.97], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'central-tower-tier-0-floor-4', 'point': [-10.55124230355509, -4.142374778457526, 17.37], 'normal': [0.1210261561239089, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'central-tower-tier-0-floor-10', 'point': [-10.55124230355509, -4.142374778457526, 41.97], 'normal': [0.1210261561239089, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-0-floor-4', 'point': [5.650910937106371, -1.4114160429766978, 17.37], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-0-floor-10', 'point': [5.650910937106371, -1.4114160429766978, 41.97], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-0-floor-4', 'point': [14.24099925705929, -1.572867029643227, 17.37], 'normal': [-0.3093097683092465, -0.9509613384509804, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-0-floor-10', 'point': [14.24099925705929, -1.572867029643227, 41.97], 'normal': [-0.3093097683092465, -0.9509613384509804, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'outer-accent-tier-0-floor-4', 'point': [27.28941410570068, -7.238518896839297, 17.37], 'normal': [-0.7413591741856177, -0.6711084672769514, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'outer-accent-tier-0-floor-10', 'point': [27.28941410570068, -7.238518896839297, 41.97], 'normal': [-0.7413591741856177, -0.6711084672769514, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'outer-accent-tier-0-floor-4', 'point': [37.57038466196608, -14.744834178467826, 17.37], 'normal': [0.6994469973577866, -0.7146844743571644, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'outer-accent-tier-0-floor-10', 'point': [37.57038466196608, -14.744834178467826, 41.97], 'normal': [0.6994469973577866, -0.7146844743571644, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'outer-accent-tier-0-floor-4', 'point': [-43.1659403464058, -7.806783820678761, 17.37], 'normal': [-0.7009678964869904, -0.7131928267268284, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'outer-accent-tier-0-floor-10', 'point': [-43.1659403464058, -7.806783820678761, 41.97], 'normal': [-0.7009678964869904, -0.7131928267268284, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-0-floor-4', 'point': [-32.51412525693093, -14.082248397846286, 17.37], 'normal': [0.7075185558290197, -0.7066947666125866, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-0-floor-10', 'point': [-32.51412525693093, -14.082248397846286, 41.97], 'normal': [0.7075185558290197, -0.7066947666125866, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'outer-accent-tier-1-floor-13', 'point': [26.381046772091466, -6.235064926076309, 54.269999999999996], 'normal': [-0.7413591741856176, -0.6711084672769515, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-1-floor-13', 'point': [-32.51412525693093, -14.082248397846286, 54.269999999999996], 'normal': [0.7075185558290197, -0.7066947666125866, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-1-floor-13', 'point': [-17.560074024301162, -4.2413543075312194, 54.269999999999996], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'central-tower-tier-1-floor-13', 'point': [-10.55124230355509, -4.142374778457526, 54.269999999999996], 'normal': [0.1210261561239089, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-1-floor-13', 'point': [5.650910937106371, -1.4114160429766978, 54.269999999999996], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-1-floor-13', 'point': [14.24099925705929, -1.572867029643227, 54.269999999999996], 'normal': [-0.3093097683092465, -0.9509613384509804, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-2-floor-14', 'point': [14.603190402863714, -1.690673353478549, 58.36999999999999], 'normal': [-0.30930976830924656, -0.9509613384509805, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-2-floor-14', 'point': [-28.53067685046846, -10.094156513044233, 58.36999999999999], 'normal': [0.7075185558290198, -0.7066947666125867, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-2-floor-14', 'point': [-17.560074024301162, -4.2413543075312194, 58.36999999999999], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'central-tower-tier-2-floor-14', 'point': [-10.55124230355509, -4.142374778457526, 58.36999999999999], 'normal': [0.1210261561239089, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-2-floor-14', 'point': [5.650910937106371, -1.4114160429766978, 58.36999999999999], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-3-floor-15', 'point': [-17.560074024301162, -4.2413543075312194, 62.46999999999999], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'central-tower-tier-3-floor-15', 'point': [-10.55124230355509, -4.142374778457526, 62.46999999999999], 'normal': [0.1210261561239089, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'garden-wide-tier-3-floor-15', 'point': [5.650910937106371, -1.4114160429766978, 62.46999999999999], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'central-tower-tier-4-floor-16', 'point': [-10.55124230355509, -4.142374778457526, 66.57], 'normal': [0.1210261561239089, -0.9926493185077353, 0.0], 'depth': 0.32, 'material': 'recessed glass'}, {'group': 'crown-real-deep-groove', 'point': [-6.5421678523106745, -2.8476548340760135, 73.2], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.58, 'material': 'crown recessed brick'}, {'group': 'crown-real-deep-groove', 'point': [-1.9263485212497042, -2.284883208099837, 73.2], 'normal': [0.12102615612390892, -0.9926493185077353, 0.0], 'depth': 0.58, 'material': 'crown recessed brick'}]
GLASS_CELL_XY = [-5.3407895111902395, -5.884580101758232]
FRAME_CELL_XY = [-3.851815533428637, -5.703040867572369]
TOWER_FRONT_XY = [-4.058025316400443, -3.3507063834042006]
CROWN_FRONT_XY = [-4.234258186780189, -2.5662690210879253]
GARDEN_NORMAL = [0.12102615612390889, -0.9926493185077353, 0.0]


def surface_probes(meshes,lod=False):
    probes=[]
    def enu(p):return [p[0],p[2],-p[1]]
    for item in RECESS_PROBES:
        point=np.array(item['point']);normal=np.array(item['normal'])
        probes.append({'group':item['group'],'origin_glb':enu(point+normal*8.),
                       'direction_glb':enu(-normal),'material':item['material'],
                       'expected_distance_m':8.+item['depth'],'tolerance':5e-5})
    for name,x,y in [('open-garden-forecourt',-4.,-17.),('western-low-block-excluded',-52.,0.),('new-jinjiang-tower-excluded',0.,30.)]:
        probes.append({'group':name,'origin_glb':enu([x,y,90.]),'direction_glb':[0.,-1.,0.],'open':True})
    for index,(x,y,z) in enumerate([(38.,-3.,53.265),(26.,0.,57.365),(18.,3.,61.465),(10.,4.,65.565),(-4.,8.,69.665),(-4.,1.,77.07)]):
        probes.append({'group':'distinct-terrace-roof-'+str(index),'origin_glb':enu([x,y,90.]),
                       'direction_glb':[0.,-1.,0.],'material':'roof closure estimate','plane_axis':1,'plane':z,'tolerance':5e-5})
    for name,xy,material,upper,lower in [('glass-panel',GLASS_CELL_XY,'shelter roof glass',4.085,4.005),
                                       ('pierced-metal-frame',FRAME_CELL_XY,'dark shelter metal',4.08,3.93)]:
        for side,origin,direction,plane in [('above',10.,[0.,-1.,0.],upper),('below',1.,[0.,1.,0.],lower)]:
            probes.append({'group':'canopy-'+name+'-from-'+side,'origin_glb':enu([*xy,origin]),
                           'direction_glb':direction,'material':material,'plane_axis':1,'plane':plane,'tolerance':5e-5})
    for name,xy,z,depth in [('central-pale-fin-control',TOWER_FRONT_XY,30.,-.175),('crown-solid-rib-control',CROWN_FRONT_XY,73.2,0.)]:
        point=np.array([*xy,z]);normal=np.array(GARDEN_NORMAL)
        probes.append({'group':name,'origin_glb':enu(point+normal*8.),'direction_glb':enu(-normal),
                       'material':'pale vertical stone','expected_distance_m':8.+depth,'tolerance':5e-5})
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
    with tempfile.TemporaryDirectory(prefix='grosvenor-verify-') as temporary:
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
                'Unexpected shared-edge winding ambiguity in Grosvenor House historic main block material batch',
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
                            'height_basis': 'Official18 includes1 basement; secondary18-above/3-below conflicts. The author chooses17 above-ground layers and78m architectural maximum; all terrace and floor datums are estimates. No basement is modeled and the78m endpoints are unverified.',
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
