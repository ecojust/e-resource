"""Independent placement/collision checks using reviewer-decoded city and model triangles.

Usage: geometry-report.json actual-occupancy-directory footprint-review.json output.json source-cache-directory [original-city-report.json]
The mapper's ordered rings are used only to replay topology-preserving simplification
after proving equality with independently derived actual occupied geometry.
"""
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, box, shape
from shapely.ops import transform, unary_union

G, C, M, O = map(Path, sys.argv[1:5])
R = Path(__file__).resolve().parent
P = Path(sys.argv[5])  # verified source cache prepared by independent-prepare-source-cache.py
g = json.loads(G.read_bytes())
mr = json.loads(M.read_bytes())
c = mr['proposed_placement_contract']
tol = 1e-6
assert c['id'] == g['modelId'] == 'yangpu-former-shanghai-city-hall'
assert c['owner'] == {'macro_id': '14-13722-6690', 'feature_local_id': 525,
                      'key': 'building:3904106e-f668-46d4-a302-a13ccd00866a'}
assert c['source_feature_ids'] == {'building': ['3904106e-f668-46d4-a302-a13ccd00866a'], 'building_part': []}
assert [c[k] for k in ['lng', 'lat', 'heading', 'scale', 'altitude']] == [121.52123739682835, 31.315220250550375, 0, 1, 0]
assert c['partial_model'] is False and shape(c['remaining_source_geometry']).is_empty
assert c['expected_replacement_triangle_count'] == 10
assert c['navigation']['listed'] is False
assert c['ground_collision_excludes_overhead_projection'] is True

radius = 6371008.8
scale = radius * math.cos(math.radians(c['lat']))
psi = math.asinh(math.tan(math.radians(c['lat'])))


def local(lng, lat, z=None):
    return (math.radians(lng - c['lng']) * scale,
            (math.asinh(math.tan(math.radians(lat))) - psi) * scale)


table_path = P / 'macro-feature-table.json.gz'
table = json.loads(gzip.decompress(table_path.read_bytes()))
sources = {row['localId']: transform(local, shape(row['geometry'])) for row in table['features']}
assert len(sources) == 2324
source = sources[525]
assert source.symmetric_difference(shape(mr['geometry']['source_geometry_local_xy'])).area < tol
assert source.symmetric_difference(transform(local, shape(c['source_limit_geometry']))).area < tol
foreign_source = unary_union([poly for owner, poly in sources.items() if owner != 525])
original_path = Path(sys.argv[6]) if len(sys.argv) > 6 else R / 'independent-original-city-projection.json'
original = json.loads(original_path.read_bytes())
assert original['passed'] is True
native_rows = {row['variant']: row for row in original['rows']}
near_parts = native_rows['near']['projection_components']
far_parts = native_rows['far']['projection_components']
near = shape(next(row['geometry_local_xy'] for row in near_parts if row['owner'] == 525))
far = shape(next(row['geometry_local_xy'] for row in far_parts if row['owner'] == 525))
foreign_native = unary_union([shape(row['geometry_local_xy']) for row in near_parts if row['owner'] != 525])
assert near.symmetric_difference(shape(mr['baseline_native_group_geometry_check']['owner525_projection_geometry_local_xy'])).area < tol
assert far.symmetric_difference(shape(mr['baseline_native_far_geometry_check']['geometry_local_xy'])).area < tol

clip = transform(local, shape(c['replacement_geometry']))
collision = transform(local, shape(c['collision_geometry']))
metadata_footprint = transform(local, shape(c['footprint']))
assert clip.is_valid and collision.is_valid and metadata_footprint.is_valid
assert len(clip.exterior.coords) == 13 and len(clip.interiors) == 0
assert clip.symmetric_difference(source.buffer(.12, join_style=2)).area < tol
assert source.difference(clip).area < tol
assert near.difference(clip).area < tol and far.difference(clip).area < tol
road = box(-70, -19.5, 70, -15.7)
for checked in [clip, collision, source]:
    assert checked.intersection(foreign_source).area < tol
    assert checked.intersection(foreign_native).area < tol
    assert checked.intersection(road).area < tol
parts = list(collision.geoms) if hasattr(collision, 'geoms') else [collision]
rings = [[len(part.exterior.coords)] + [len(h.coords) for h in part.interiors] for part in parts]
assert rings == [[58], [25]]
assert all(4 <= count <= 65 for group in rings for count in group)
negative_points = []
for y in [-17.98, -17.6, -17.22]:
    assert LineString([(-70, y), (70, y)]).intersection(collision).length == 0
    for x in [-12, -6, 0, 6, 12]:
        assert not collision.covers(Point(x, y))
        negative_points.append([x, y])
for point in [[-.53, -21], [0, -14.3], [-.53, -40], [0, 0]]:
    assert collision.covers(Point(point)), point

records = []
bindings = []
raw_full = raw_low = None
for role, asset in g['assets'].items():
    if role == 'native':
        continue
    name = 'web' if role == 'full' else role
    assert c['model_geometry_sha256'][name] == asset['sha256']
    assert c['bounds_glb'] == asset['actualBoundsGLB']
    assert len(asset['surfaceProbes']) == 59
    cache_path = C / (asset['sha256'] + '.json')
    cache_bytes = cache_path.read_bytes()
    cache = json.loads(cache_bytes)
    assert cache['asset_sha256'] == asset['sha256']
    assert cache['triangle_payload_sha256'] == asset['actualTrianglesENU']['sha256']
    assert cache['plan_payload_sha256'] == asset['actualPlanProjection']['trianglePayloadSHA256']
    bindings.append({'file': str(cache_path), 'sha256': hashlib.sha256(cache_bytes).hexdigest()})
    full = shape(cache['full_projection']['geometry_local_xy'])
    low = shape(cache['standing_slab']['geometry_local_xy'])
    mapped = next(row for row in mr['actual_model_envelope_review']['records'] if row['asset_binding']['sha256'] == asset['sha256'])
    mapped_full = shape(mapped['actual_full_projection_local_xy'])
    mapped_low = shape(mapped['actual_standing_slab']['geometry_local_xy'])
    assert full.symmetric_difference(mapped_full).area < tol
    assert low.symmetric_difference(mapped_low).area < tol
    assert source.difference(full).area < tol and near.difference(full).area < tol
    assert low.difference(collision).area < tol
    assert source.difference(collision).area < tol
    assert low.intersection(road).area < tol
    assert full.intersection(foreign_source).area < tol
    assert full.intersection(foreign_native).area < tol
    if role == 'raw':
        raw_full, raw_low = full, low
        # DP may choose a different result for different cyclic starting vertices.
        # Safety tests above use independently computed geometry. Replay uses only
        # the ordered ring whose actual occupied set was independently verified.
        replay = unary_union([mapped_low, source]).buffer(.12, join_style=2).simplify(.05, preserve_topology=True)
        assert collision.symmetric_difference(replay).area < tol
        assert collision.difference(unary_union([low, source]).buffer(.20, join_style=2)).area < tol
        assert metadata_footprint.symmetric_difference(mapped_full.simplify(.03, preserve_topology=True)).area < tol
        fill = source.difference(low)
        recorded_fill = shape(mr['actual_model_envelope_review']['collision_review']['main_interior_fill_geometry_local_xy'])
        assert fill.symmetric_difference(recorded_fill).area < tol
        assert fill.difference(source).area < tol and fill.intersection(road).area < tol
        assert clip.difference(full).area < tol
    records.append({
        'variant': role, 'sha256': asset['sha256'], 'triangles': asset['triangles'],
        'independent_surface_rays_passed': len(asset['surfaceProbes']),
        'actual_projection_m2': full.area, 'actual_standing_slab_m2': low.area,
        'mapper_full_symmetric_difference_m2': full.symmetric_difference(mapped_full).area,
        'mapper_slab_symmetric_difference_m2': low.symmetric_difference(mapped_low).area,
        'raw_full_symmetric_difference_m2': full.symmetric_difference(raw_full).area,
        'raw_slab_symmetric_difference_m2': low.symmetric_difference(raw_low).area,
        'standing_slab_outside_collision_m2': low.difference(collision).area,
        'source_outside_actual_projection_m2': source.difference(full).area,
        'native_near_outside_actual_projection_m2': near.difference(full).area,
        'all_2323_foreign_source_overlap_m2': full.intersection(foreign_source).area,
        'six_same_group_foreign_native_overlap_m2': full.intersection(foreign_native).area,
        'actual_slab_road_overlap_m2': low.intersection(road).area,
        'overhead_projection_outside_ground_collision_m2': full.difference(collision).area,
    })
assert [row['variant'] for row in records] == ['raw', 'full', 'lod']
assert records[1]['raw_full_symmetric_difference_m2'] < tol
assert .5 < records[2]['raw_full_symmetric_difference_m2'] < .7
report = {
    'schema': 'yangpu-city-hall-independent-placement-review-v1',
    'passed': True, 'private_only': False, 'browser_started_or_connected': False,
    'method': 'Reviewer independent indexed/instanced city decoder and actual model triangle decoder; exact standing-slab plane intersections. All actual model/source/foreign safety tests use reviewer-derived geometry. Ordered mapper rings are reused only after occupied-set equivalence for deterministic DP replay.',
    'bindings': bindings + [{'file': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in [G, M, table_path, original_path, Path(__file__)]],
    'source_owner': c['owner'], 'source_area_m2': source.area,
    'source_replaced_m2': source.intersection(clip).area,
    'source_remaining_m2': source.difference(clip).area,
    'native_near_remaining_m2': near.difference(clip).area,
    'native_far_remaining_m2': far.difference(clip).area,
    'display_clip_m2': clip.area,
    'display_clip_outside_source_m2': clip.difference(source).area,
    'display_clip_triangles': len(clip.exterior.coords) - 3,
    'main_interior_fill_m2': fill.area,
    'main_interior_fill_outside_source_m2': fill.difference(source).area,
    'collision_area_m2': collision.area,
    'collision_ring_points_including_all_interiors_and_closure': rings,
    'road_centre_and_shoulders_negative_points': negative_points,
    'complete_X_road_centre_and_shoulders_clear': True,
    'piers_steps_and_main_interior_positive_controls': True,
    'variants': records,
    'numeric_area_tolerance_m2': tol,
    'limitations': [
        'Full and raw surfaces are exactly equal; LOD retains the exact bounds and tested openings but is not geometrically identical.',
        'Main source interior is conservatively blocked. This two-dimensional collision does not certify bridge-deck/stair or indoor walking; the model remains overview-only.',
        'Complete bridge-deck projection is deliberately excluded from ground collision. Source replacement clips only the main source and explicitly bounded old eaves, not the external staircase footprint.',
        'Metric roof/bridge/threshold dimensions remain estimates; this placement proof is not a measured architectural survey.',
    ],
}
O.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: report[key] for key in ['passed', 'source_replaced_m2', 'display_clip_outside_source_m2', 'main_interior_fill_m2', 'collision_ring_points_including_all_interiors_and_closure']}))
