"""Review-only plan and standing-height occupancy from independently decoded triangles.

Usage: geometry-report.json projection-directory output-cache-directory
No author construction code or mapper occupancy is read.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union


def digest(data):
    return hashlib.sha256(data).hexdigest()


def clip_height(vertices, height, keep_above):
    result = []
    for start, end in zip(vertices, vertices[1:] + vertices[:1]):
        inside_start = start[2] >= height if keep_above else start[2] <= height
        inside_end = end[2] >= height if keep_above else end[2] <= height
        if inside_start:
            result.append(start)
        if inside_start != inside_end:
            fraction = (height - start[2]) / (end[2] - start[2])
            crossing = start + (end - start) * fraction
            crossing[2] = height
            result.append(crossing)
    return result


report_path, projection_path, output_path = map(Path, sys.argv[1:4])
report_bytes = report_path.read_bytes()
report = json.loads(report_bytes)
script_sha = digest(Path(__file__).read_bytes())
output_path.mkdir(parents=True, exist_ok=True)
for role, asset in report['assets'].items():
    if role == 'native':
        continue
    path = output_path / (asset['sha256'] + '.json')
    if path.exists():
        previous = json.loads(path.read_bytes())
        if previous['derivation_script_sha256'] == script_sha:
            assert previous['asset_sha256'] == asset['sha256']
            assert previous['triangle_payload_sha256'] == asset['actualTrianglesENU']['sha256']
            print('CACHED', role, asset['sha256'], flush=True)
            continue
    triangle_bytes = (projection_path / asset['actualTrianglesENU']['file']).read_bytes()
    assert digest(triangle_bytes) == asset['actualTrianglesENU']['sha256']
    triangles = np.frombuffer(triangle_bytes, dtype='<f8').reshape(-1, 3, 3)
    assert len(triangles) == asset['triangles']
    candidates = triangles[(triangles[:, :, 2].min(axis=1) <= 2) &
                           (triangles[:, :, 2].max(axis=1) >= 0)]
    polygons = []
    for triangle in candidates:
        cut = clip_height(list(triangle), 0, True)
        if cut:
            cut = clip_height(cut, 2, False)
        if len(cut) < 3:
            continue
        polygon = Polygon([vertex[:2] for vertex in cut])
        if polygon.area > 1e-10:
            assert polygon.is_valid
            polygons.append(polygon)
    low = unary_union(polygons)
    assert low.is_valid
    print('SLAB', role, low.area, flush=True)
    plan_bytes = (projection_path / (role + '-plan-triangles.json')).read_bytes()
    assert digest(plan_bytes) == asset['actualPlanProjection']['trianglePayloadSHA256']
    full = unary_union([Polygon(triangle) for triangle in json.loads(plan_bytes)])
    assert full.is_valid
    output = {
        'schema': 'yangpu-city-hall-independent-actual-occupancy-v1',
        'private_only': False,
        'asset_sha256': asset['sha256'],
        'role': role,
        'triangles': len(triangles),
        'triangle_payload_sha256': digest(triangle_bytes),
        'plan_payload_sha256': digest(plan_bytes),
        'derivation_script_sha256': script_sha,
        'input_geometry_report': {'file': str(report_path), 'sha256': digest(report_bytes)},
        'method': 'Each actual indexed triangle is clipped successively to z>=0 and z<=2 with interpolated plane crossings. Surviving XY polygons are unioned. Full plan is a separate union of actual triangle projections.',
        'standing_slab': {
            'z_min_m': 0, 'z_max_m': 2,
            'triangles_touching_slab': len(candidates),
            'nonzero_projected_clipped_polygons': len(polygons),
            'area_m2': low.area,
            'geometry_local_xy': mapping(low),
        },
        'full_projection': {'area_m2': full.area, 'geometry_local_xy': mapping(full)},
    }
    path.write_text(json.dumps(output, indent=2) + '\n')
    print('SAVED', role, full.area, path, flush=True)
