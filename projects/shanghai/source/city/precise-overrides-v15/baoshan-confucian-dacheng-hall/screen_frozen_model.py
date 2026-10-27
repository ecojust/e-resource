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
ID = 'baoshan-confucian-dacheng-hall'
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
    assert not doc.get('images'), 'Expected reviewed geometry-only raw branch'
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--metadata', type=Path, required=True)
    p.add_argument('--navigation', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output = args.output.resolve()
    assert args.output.is_relative_to(HERE) and args.output != HERE, 'Use an isolated integration child directory'
    assert not args.output.exists(), 'Use a fresh review directory'
    metadata = read(args.metadata)
    assert metadata['id'] == ID and metadata.get('rotation_y', 0) == 0
    raw = metadata.get('assets', {}).get('raw') or metadata['raw']
    raw_path = Path(raw.get('path') or raw.get('source') or raw['file'])
    raw_path = raw_path if raw_path.is_absolute() else args.metadata.parent / raw_path
    raw_desc = desc(raw_path)
    assert all(raw_desc[k] == raw[k] for k in ('bytes', 'sha256'))
    points, triangles = decode_raw(raw_path)
    assert triangles == raw['triangles'], 'Decoded raw triangle count differs'
    source = read(HERE / 'freeze-v1' / ID / 'geometry-input.json')
    assert metadata['anchor'] == source['anchor']
    lon0, lat0 = source['anchor']
    cos0 = math.cos(math.radians(lat0))
    y0 = R * math.log(math.tan(math.pi/4 + math.radians(lat0)/2))

    def local(lon, lat, z=None):
        return (R*math.radians(lon-lon0)*cos0,
                (R*math.log(math.tan(math.pi/4+math.radians(lat)/2))-y0)*cos0)

    prior = read(args.navigation)
    nav = prior['navigation']
    start = np.array(local(*nav['walkStart']))
    rad = math.radians(nav['bearing'])
    forward = np.array([math.sin(rad), math.cos(rad)])
    target = start + forward * 2.8
    camera = target - forward * (14*math.sin(math.radians(82)))
    probes = {
        'avatar_disc': (Point(start), .38),
        'first_5m_forward_swept_body': (LineString([start, start+forward*5]), .38),
        'settled_camera_disc': (Point(camera), .12),
        'settled_camera_boom_projection': (LineString([target, camera]), .12),
    }
    hull_indices = ConvexHull(points[:, :2]).vertices
    projected_hull = Polygon(points[hull_indices, :2])
    clearance = {name: {'radius_m': radius,
                        'conservative_distance_to_projected_hull_m': projected_hull.distance(probe),
                        'radius_clearance_lower_bound_m': projected_hull.distance(probe)-radius}
                 for name, (probe, radius) in probes.items()}
    assert all(row['radius_clearance_lower_bound_m'] > 0 for row in clearance.values())
    low, high = points.min(axis=0), points.max(axis=0)
    center = (low+high)*.5
    theta = math.radians(prior['source_axis_east_degrees'])
    rotation = np.array([[math.cos(theta), -math.sin(theta), 0],
                         [math.sin(theta), math.cos(theta), 0], [0, 0, 1]])
    # Fit every decoded vertex, not a nominal box. These are perspective views.
    # Positive Z in the orbit vector means camera above the actual mesh center.
    orbits = {'front': np.array([26., -36., 15.]),
              'rear': np.array([-25., 36., 12.])}
    fov, width, height, ndc_limit = 48., 1040, 760, .80
    tangent = math.tan(math.radians(fov/2))
    aspect = width/height
    views, view_checks = {}, {}
    for name, orbit in orbits.items():
        direction = rotation @ orbit
        direction /= np.linalg.norm(direction)
        forward3 = -direction
        right = np.cross(forward3, [0, 0, 1])
        right /= np.linalg.norm(right)
        up = np.cross(right, forward3)
        basis = np.vstack([right, up, forward3]).T
        centered = (points-center) @ basis

        def project(distance):
            depth = centered[:, 2] + distance
            if depth.min() <= .1:
                return None
            ndc = centered[:, :2] / (depth[:, None] * tangent * [aspect, 1])
            return ndc, depth

        lo, hi = 1., 200.
        for _ in range(36):
            middle = (lo+hi)/2
            result = project(middle)
            if result is not None and np.abs(result[0]).max() <= ndc_limit:
                hi = middle
            else:
                lo = middle
        distance = hi + .5
        eye = center + direction * distance
        ndc, depth = project(distance)
        views[name] = {'east': float(eye[0]), 'north': float(eye[1]),
                       'alt': float(eye[2]), 'to_east': float(center[0]),
                       'to_north': float(center[1]), 'to_alt': float(center[2]), 'fov': fov}
        view_checks[name] = {
            'eye_enu_m': eye.tolist(), 'target_enu_m': center.tolist(),
            'distance_m': distance, 'actual_vertex_count': len(points),
            'ndc_min': ndc.min(axis=0).tolist(), 'ndc_max': ndc.max(axis=0).tolist(),
            'positive_depth_range_m': [float(depth.min()), float(depth.max())],
            'inside_frame_with_10_percent_edge_margin': bool(np.abs(ndc).max() < ndc_limit),
            'camera_projected_hull_radius_clearance_m': projected_hull.distance(Point(eye[:2]))-.12,
            'projection_scope': 'All referenced raw GLB vertex positions after scene node transforms, perspective48deg vertical FOV,1040x760. No rendering or pixel visibility claim.',
        }
    assert all(v['inside_frame_with_10_percent_edge_margin'] and v['camera_projected_hull_radius_clearance_m'] > 0 for v in view_checks.values())
    identity = read(HERE / 'source-identity.json')
    neighbors = []
    for record in identity['bounded_uniqueness_scan']['files']:
        assert all(desc(record['path'])[k] == record[k] for k in ('bytes', 'sha256'))
        for feature in read(record['path'])['features']:
            key = feature.get('key', 'building:'+str(feature.get('id', feature.get('properties', {}).get('id'))))
            if key == 'building:3b05626b-372a-473b-b2ce-b7556e888081' or not feature.get('geometry'):
                continue
            geom = transform(local, shape(feature['geometry']))
            if geom.distance(Point(0, 0)) > 150:
                continue
            neighbors.append({'kind': record['kind'], 'file': record['path'],
                              'key': key, 'local_id': feature.get('localId'), 'geometry': geom})
    for name, pose in views.items():
        point = Point(pose['east'], pose['north'])
        sightline = LineString([point, Point(pose['to_east'], pose['to_north'])])
        rows = sorted([{
            **{k: row[k] for k in ('kind', 'file', 'key', 'local_id')},
            'camera_radius_clearance_m': row['geometry'].distance(point)-.12,
            'sightline_radius_clearance_m': row['geometry'].distance(sightline)-.12,
        } for row in neighbors], key=lambda row: row['sightline_radius_clearance_m'])
        view_checks[name]['bounded_source_neighbor_screen'] = {
            'features_within_150m': len(neighbors), 'nearest': rows[:6],
            'intersections': [row for row in rows if min(row['camera_radius_clearance_m'], row['sightline_radius_clearance_m']) <= 0],
            'scope': 'Conservative2D footprint screen for finite camera point and camera-to-model-center segment; heights not used to waive intersections.',
        }
        assert not view_checks[name]['bounded_source_neighbor_screen']['intersections']
    report = {
        'schema': 'baoshan-v15-frozen-raw-model-planar-and-perspective-screen',
        'building_id': ID, 'geometry_screen_passed': True,
        'browser_passed': False, 'root_visual_accepted': False,
        'raw_asset': raw_desc, 'metadata': desc(args.metadata),
        'navigation_input': desc(args.navigation), 'screen_script': desc(__file__),
        'navigation': nav, 'camera_requests': views,
        'triangles': triangles, 'referenced_vertex_count': len(points),
        'actual_bounds_enu_m': [low.tolist(), high.tolist()],
        'actual_projected_convex_hull_enu_m': list(map(list, projected_hull.exterior.coords)),
        'spawn_probe_clearance': clearance, 'views': view_checks,
        'limitations': [
            'Positive clearance from a convex hull containing every actual projected triangle is conservative. The hull is not a reconstruction of walkable surfaces or openings.',
            'Only the stated spawn, first5m movement and settled14m camera projection were screened; no all-motion collision certification.',
            'Camera framing uses raw mesh positions and finite source neighbor footprints, not live rendered occlusion, trees, lighting or compression appearance.',
            'Actual web/LOD rendering, ownership and input behavior still require the pinned browser run and root screenshot review.',
        ],
    }
    args.output.mkdir(parents=True)
    write(args.output/'model-clearance.json', report)
    write(args.output/'camera-views.json', views)
    proposal = dict(prior)
    proposal['actual_model_screen'] = {'report': desc(args.output/'model-clearance.json'),
                                       'camera_views': desc(args.output/'camera-views.json'),
                                       'raw_asset_sha256': raw_desc['sha256'],
                                       'geometry_screen_passed': True,
                                       'browser_passed': False, 'root_visual_accepted': False}
    write(args.output/'navigation-proposal.json', proposal)
    print(json.dumps({'report': desc(args.output/'model-clearance.json'),
                      'views': desc(args.output/'camera-views.json'),
                      'navigation': desc(args.output/'navigation-proposal.json'),
                      'spawn_probe_clearance': clearance, 'camera_views': views}, indent=2))


if __name__ == '__main__':
    main()
