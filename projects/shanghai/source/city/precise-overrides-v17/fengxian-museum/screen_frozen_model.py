#!/usr/bin/env python3
"""Decode frozen raw GLB and screen finite spawn/boom/camera poses.

Conservative projected convex hulls contain every decoded triangle. A positive
distance proves clearance for these finite planar probes, without pretending the
hull is an exact walkable surface or proving all motion and visibility.
"""
import argparse
import gzip
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ID = 'fengxian-museum'
R = 6378137.0


def read(path):
    path = Path(path)
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def desc(path):
    path = Path(path).resolve()
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def decode_raw(path):
    blob = Path(path).read_bytes()
    magic, version, length = struct.unpack_from('<4sII', blob)
    assert magic == b'glTF' and version == 2 and length == len(blob)
    offset = 12
    chunks = {}
    while offset < len(blob):
        n, kind = struct.unpack_from('<II', blob, offset)
        offset += 8
        assert kind not in chunks and offset + n <= len(blob)
        chunks[kind] = memoryview(blob)[offset:offset+n]
        offset += n
    doc = json.loads(bytes(chunks[0x4E4F534A]))
    binary = chunks[0x004E4942]
    assert len(doc['buffers']) == 1 and 'uri' not in doc['buffers'][0]
    assert not doc.get('skins') and not doc.get('animations')
    assert not any('uri' in image for image in doc.get('images', [])), 'External raw image dependencies forbidden; exact embedded image/UV acceptance is separate'
    dtype = {5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
    size = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

    def accessor(i):
        acc = doc['accessors'][i]
        assert not acc.get('sparse') and not acc.get('normalized')
        view = doc['bufferViews'][acc['bufferView']]
        assert view['buffer'] == 0 and not view.get('extensions')
        dt = np.dtype(dtype[acc['componentType']])
        width = size[acc['type']]
        stride = view.get('byteStride', width * dt.itemsize)
        start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
        assert start + (acc['count']-1)*stride + width*dt.itemsize <= len(binary)
        return np.ndarray((acc['count'], width), dtype=dt, buffer=binary,
                          offset=start, strides=(stride, dt.itemsize))

    def matrix(node):
        if 'matrix' in node:
            return np.array(node['matrix'], dtype=float).reshape(4, 4).T
        x, y, z, w = node.get('rotation', [0, 0, 0, 1])
        rotation = np.array([
            [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
        ])
        result = np.eye(4)
        result[:3, :3] = rotation @ np.diag(node.get('scale', [1, 1, 1]))
        result[:3, 3] = node.get('translation', [0, 0, 0])
        return result

    positions, triangle_count, visited = [], 0, set()

    def visit(i, parent):
        nonlocal triangle_count
        assert i not in visited, 'Unexpected repeated raw scene node'
        visited.add(i)
        node = doc['nodes'][i]
        world = parent @ matrix(node)
        if 'mesh' in node:
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                assert primitive.get('mode', 4) == 4 and not primitive.get('targets')
                verts = accessor(primitive['attributes']['POSITION'])
                assert verts.shape[1] == 3 and np.all(np.isfinite(verts))
                if 'indices' in primitive:
                    indices = accessor(primitive['indices']).ravel()
                    assert len(indices) % 3 == 0 and int(indices.max()) < len(verts)
                    triangle_count += len(indices) // 3
                    verts = verts[np.unique(indices)]
                else:
                    assert len(verts) % 3 == 0
                    triangle_count += len(verts) // 3
                transformed = np.asarray(verts, dtype=float) @ world[:3, :3].T + world[:3, 3]
                # Author contract: glTF east/up/south -> actual ENU metres.
                positions.append(transformed[:, [0, 2, 1]] * [1, -1, 1])
        for child in node.get('children', []):
            visit(child, world)

    for root in doc['scenes'][doc.get('scene', 0)]['nodes']:
        visit(root, np.eye(4))
    return np.concatenate(positions), triangle_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--navigation', type=Path, required=True)
    parser.add_argument('--camera-views', type=Path)
    parser.add_argument('--draft', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    assert args.output.is_relative_to(HERE) and args.output != HERE and not args.output.exists()
    metadata = read(args.metadata)
    assert metadata['id'] == ID and metadata.get('rotation_y', 0) == 0 and metadata['ground_base_m'] == 0
    raw = metadata.get('assets', {}).get('raw') or metadata['raw']
    raw_path = Path(raw.get('path') or raw.get('source') or raw['file'])
    if not raw_path.is_absolute():
        raw_path = args.metadata.parent / raw_path
    raw_desc = desc(raw_path)
    assert all(raw_desc[k] == raw[k] for k in ('bytes', 'sha256'))
    points, triangles = decode_raw(raw_path)
    assert triangles == raw['triangles'] and np.isfinite(points).all()
    geometry_path = HERE / 'freeze-v1' / ID / 'geometry-input.json'
    source = read(geometry_path)
    assert metadata['anchor'] == source['anchor']
    if metadata.get('source_geometry_sha256'):
        assert metadata['source_geometry_sha256'] == desc(geometry_path)['sha256']
    lon0, lat0 = source['anchor']
    cos0 = math.cos(math.radians(lat0))
    mercator0 = math.asinh(math.tan(math.radians(lat0)))

    def local(lon, lat, z=None):
        return (R * math.radians(lon-lon0) * cos0,
                R * (math.asinh(math.tan(math.radians(lat))) - mercator0) * cos0)

    context_path = HERE / 'source-neighborhood-v1.json'
    context = read(context_path)
    assert context['anchor'] == source['anchor'] and len(context['features']) == 5
    # Rebind every saved footprint to exact immutable source records and recompute ENU.
    actual_features = {}
    for record in context['source_files']:
        assert all(desc(record['path'])[k] == record[k] for k in ('bytes', 'sha256'))
        macro = Path(record['path']).parent.name
        for feature in read(record['path'])['features']:
            actual_features[(macro, feature['localId'])] = feature
    neighbors = []
    for record in context['features']:
        feature = actual_features[(record['macro'], record['local_id'])]
        assert feature['key'] == record['key'] and feature['geometry'] == record['geometry_geographic']
        geom = transform(local, shape(feature['geometry']))
        assert geom.hausdorff_distance(shape(record['geometry_local_east_north_m'])) < 1e-7
        neighbors.append({**record, 'geometry': geom})
    keep = {95}
    assert all(r['retain'] is True for r in neighbors)
    assert keep <= {r['local_id'] for r in neighbors if r['macro'] == '14-13721-6710'}
    assert set(source['current_city_detail']['near_feature_local_ids']) == keep | {143}
    prior = read(args.navigation)
    nav = prior['navigation']
    assert nav['listed'] is True and nav['overviewZoom'] == 18
    ground_descriptor = prior['source_ground_screen']
    ground_path = Path(ground_descriptor['path'])
    assert all(desc(ground_path)[key] == ground_descriptor[key] for key in ('bytes', 'sha256'))
    ground = read(ground_path)
    assert ground['passed_source_screen_only'] and ground['candidate_navigation'] == {key: nav[key] for key in ('walkStart', 'bearing')}
    assert ground['all_probe_buffers_inside_requested_bbox'] and not ground['incomplete_way_node_refs'] and not ground['invalid_way_geometries'] and not ground['water_relations_pending']
    # Bind exact complete water reconstruction plus every input used in the
    # independent ground screen. Water never automatically rejects airborne views.
    dependencies = [ground['osm_input'], ground['tool'], ground['candidate_binding'], ground['complete_water_evidence'], ground['effective_neighborhood']]
    dependencies += ground['runtime_source_inputs'] + ground['water_source_dependencies']
    for descriptor in dependencies:
        assert all(desc(descriptor['path'])[key] == descriptor[key] for key in ('bytes', 'sha256'))
    water_proof = read(ground['complete_water_evidence']['path'])
    assert water_proof['source_extraction_passed'] and water_proof['all_relation_way_nodes_present']
    water_doc = read(water_proof['water_geometry']['path'])
    water = shape(water_doc['features'][0]['geometry'])
    assert water.is_valid and len(water.interiors) == 5
    start = np.array(local(*nav['walkStart']))
    rad = math.radians(nav['bearing'])
    forward = np.array([math.sin(rad), math.cos(rad)])
    target = start + forward * 2.8
    camera = target - forward * (14 * math.sin(math.radians(82)))
    probes = {
        'avatar_disc': (Point(start), .38),
        'first_5m_forward_swept_body': (LineString([start, start+forward*5]), .38),
        'settled_camera_disc': (Point(camera), .12),
        'settled_camera_boom_projection': (LineString([target, camera]), .12),
    }
    hull = Polygon(points[ConvexHull(points[:, :2]).vertices, :2])
    clearance = {}
    for name, (probe, radius) in probes.items():
        rows = sorted([{'key': row['key'], 'macro': row['macro'], 'local_id': row['local_id'],
                        'radius_clearance_m': row['geometry'].distance(probe)-radius}
                       for row in neighbors], key=lambda r: r['radius_clearance_m'])
        clearance[name] = {
            'radius_m': radius,
            'conservative_distance_to_projected_hull_m': hull.distance(probe),
            'radius_clearance_lower_bound_m': hull.distance(probe)-radius,
            'source_neighbor_intersections': [r for r in rows if r['radius_clearance_m'] <= 0],
            'nearest_source_neighbors': rows[:5],
        }
    assert all(r['radius_clearance_lower_bound_m'] > 0 and not r['source_neighbor_intersections'] for r in clearance.values())
    mesh_neighbors = sorted([
        {'key': row['key'], 'macro': row['macro'], 'local_id': row['local_id'], 'retain': row['retain'],
         'projected_hull_clearance_m': row['geometry'].distance(hull),
         'projected_hull_overlap_area_m2': row['geometry'].intersection(hull).area}
        for row in neighbors], key=lambda r: r['projected_hull_clearance_m'])
    assert all(r['projected_hull_clearance_m'] > 0 and r['projected_hull_overlap_area_m2'] == 0 for r in mesh_neighbors)
    water_screen = {}
    for name, (probe, radius) in probes.items():
        required = name in ('avatar_disc', 'first_5m_forward_swept_body')
        distance = water.distance(probe) - radius
        water_screen[name] = {'radius_clearance_m': distance, 'ground_requirement': required,
                              'accepted_by_this_water_check': distance > 0 if required else None,
                              'scope': 'Ground clearance required.' if required else 'Elevated camera water proximity is informational; geometry/obstacle checks are separate.'}
        assert not required or distance > 0
    low, high = points.min(axis=0), points.max(axis=0)
    views = read(args.camera_views) if args.camera_views else {}
    assert args.draft or set(views) == {'front', 'rear'}, 'Final screen requires explicit front/rear camera poses'
    view_checks = {}
    for name, pose in views.items():
        eye = np.array([pose['east'], pose['north'], pose['alt']], dtype=float)
        aim = np.array([pose.get('to_east', 0), pose.get('to_north', 0), pose['to_alt']], dtype=float)
        front = aim-eye
        front /= np.linalg.norm(front)
        right = np.cross(front, [0, 0, 1])
        right /= np.linalg.norm(right)
        up = np.cross(right, front)
        transformed = (points-eye) @ np.vstack([right, up, front]).T
        depth = transformed[:, 2]
        assert depth.min() > .1 and 10 <= pose['fov'] <= 100
        ndc = transformed[:, :2] / (depth[:, None] * math.tan(math.radians(pose['fov']/2)) * [1040/760, 1])
        point = Point(eye[:2])
        sightline = LineString([eye[:2], aim[:2]])
        rows = sorted([
            {'key': row['key'], 'macro': row['macro'], 'local_id': row['local_id'],
             'camera_radius_clearance_m': row['geometry'].distance(point)-.12,
             'sightline_radius_clearance_m': row['geometry'].distance(sightline)-.12}
            for row in neighbors], key=lambda r: min(r['camera_radius_clearance_m'], r['sightline_radius_clearance_m']))
        view_checks[name] = {
            'eye_enu_m': eye.tolist(), 'target_enu_m': aim.tolist(),
            'actual_vertex_count': len(points), 'ndc_min': ndc.min(axis=0).tolist(),
            'ndc_max': ndc.max(axis=0).tolist(),
            'positive_depth_range_m': [float(depth.min()), float(depth.max())],
            'inside_frame_with_10_percent_edge_margin': bool(np.abs(ndc).max() <= .80),
            'camera_projected_hull_radius_clearance_m': hull.distance(point)-.12,
            'bounded_source_neighbor_screen': {
                'features_within_250m_of_source_owner': len(neighbors), 'nearest': rows[:6],
                'intersections': [r for r in rows if min(r['camera_radius_clearance_m'], r['sightline_radius_clearance_m']) <= 0],
                'scope': 'Conservative 2D camera point and camera-to-target segment against actual frozen source footprints; no height-based waiver.',
            },
            'projection_scope': 'Every referenced raw GLB vertex after scene transforms; perspective FOV as requested, 1040x760; no rendered visibility claim.',
        }
        assert view_checks[name]['inside_frame_with_10_percent_edge_margin'] and view_checks[name]['camera_projected_hull_radius_clearance_m'] > 0 and not view_checks[name]['bounded_source_neighbor_screen']['intersections']
    report = {
        'schema': 'fengxian-v17-frozen-raw-model-planar-and-perspective-screen',
        'building_id': ID, 'draft_only': args.draft,
        'spatial_mesh_screen_passed': True, 'geometry_screen_passed': not args.draft,
        'browser_passed': False, 'root_visual_accepted': False,
        'raw_asset': raw_desc, 'metadata': desc(args.metadata), 'geometry_input': desc(geometry_path),
        'source_neighborhood': desc(context_path), 'source_files': context['source_files'],
        'navigation_input': desc(args.navigation), 'source_ground_screen': ground_descriptor, 'screen_script': desc(__file__),
        'navigation': nav, 'camera_requests': views,
        'camera_views_input': desc(args.camera_views) if args.camera_views else None,
        'triangles': triangles, 'referenced_vertex_count': len(points),
        'actual_bounds_enu_m': [low.tolist(), high.tolist()],
        'actual_projected_convex_hull_enu_m': list(map(list, hull.exterior.coords)),
        'spawn_probe_clearance': clearance, 'views': view_checks,
        'complete_mapped_water_screen': water_screen,
        'model_convex_hull_to_mapped_water': {
            'distance_m': hull.distance(water),
            'intersection_area_m2': hull.intersection(water).area,
            'scope': 'Conservative projected convex hull, not exact mesh/ground footprint. Roof overhang or empty hull concavity is not automatically a water collision or geometry failure.'},
        'model_to_source_neighbor_screen': mesh_neighbors,
        'limitations': [
            'Draft geometry is not a final model or navigation acceptance. Final model byte hashes must receive a separate non-draft screen.',
            'Positive convex-hull distances conservatively contain every actual projected triangle; hull is not a walking surface or reconstructed opening.',
            'Only stated spawn, first 5m movement, current settled controller camera and supplied finite screenshot poses are screened.',
            'Complete mapped lake data is separately bound for the external avatar and first 5m path. Elevated camera water proximity is informational. Vegetation, furniture, hidden current obstacles and arbitrary motion are not accepted.',
            'Embedded image bytes, UV, material semantics and compressed web/LOD equivalence require independent asset validation.',
            'Actual web/LOD rendering, ownership, input and appearance require the pinned browser run and root screenshot review.',
        ],
    }
    args.output.mkdir(parents=True)
    write(args.output / 'model-clearance.json', report)
    if not args.draft:
        write(args.output / 'camera-views.json', views)
        result = dict(prior)
        result['actual_model_screen'] = {'report': desc(args.output / 'model-clearance.json'),
                                        'camera_views': desc(args.output / 'camera-views.json'),
                                        'raw_asset_sha256': raw_desc['sha256'],
                                        'geometry_screen_passed': True,
                                        'browser_passed': False, 'root_visual_accepted': False}
        write(args.output / 'navigation-proposal.json', result)
    print(json.dumps({'report': desc(args.output / 'model-clearance.json'),
                      'draft_only': args.draft, 'triangles': triangles,
                      'mesh_min_neighbor_clearance_m': mesh_neighbors[0]['projected_hull_clearance_m'],
                      'probe_min_hull_clearance_m': min(r['radius_clearance_lower_bound_m'] for r in clearance.values()),
                      'camera_views': views}, indent=2))


if __name__ == '__main__':
    main()

