"""Independently union decoded indexed triangles and verify the map contract.

Run after independent-geometry-check.mjs with its optional private projection
directory. The triangle files are temporary numerical data, not author plans.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box, mapping, shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
PRIVATE = Path(sys.argv[1])


def load(path):
    return json.loads(Path(path).read_text())


def binding(path):
    path = Path(path)
    data = path.read_bytes()
    return {"file": str(path.relative_to(ROOT)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


geometry = load(AUDIT / 'independent-geometry.json')
footprint = load(AUDIT / 'footprint-review.json')
contract = footprint['proposed_placement_contract']
assert contract['id'] == 'huangpu-cathay-mansions'
assert contract['source_feature_ids']['building'] == [footprint['identity']['source_id']]
assert contract['source_feature_ids'].get('building_part', []) == []
assert contract['owner']['feature_local_id'] == 3146
angle = math.radians(contract['heading'])
c, s = math.cos(angle), math.sin(angle)
lat0 = math.radians(contract['lat'])
radius = 6371008.8
physical_scale = radius * math.cos(lat0)
mercator_y0 = math.log(math.tan(math.pi / 4 + lat0 / 2))


def local(lng, lat, z=None):
    east = math.radians(lng - contract['lng']) * physical_scale
    north = (math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
             - mercator_y0) * physical_scale
    return c * east - s * north, s * east + c * north


source = transform(local, shape(contract['source_limit_geometry']))
replacement = transform(local, shape(contract['replacement_geometry']))
collision = transform(local, shape(contract['collision_geometry']))
assert source.is_valid and replacement.is_valid and collision.is_valid
assert source.difference(replacement).area < 1e-7
clearance_review = footprint['native_rendering_clearance_review']
assert clearance_review['normal_expansion_m'] == .13
expected_replacement = source.buffer(.13, join_style=2)
assert expected_replacement.symmetric_difference(replacement).area < 1e-5
expansion = max(source.distance(Point(p)) for p in replacement.exterior.coords)
assert abs(expansion - clearance_review['maximum_euclidean_expansion_m']) < 1e-6
exclusions = footprint.get('exclusions', {})
nearby = next((v for k, v in exclusions.items()
               if 'macro_neighbors' in k and isinstance(v, list)), [])
neighbors = list({row['source_id']: row for row in
                  [*nearby, *exclusions.get('required_context_sources', [])]}.values())

report = {
    'schema': 'cathay-independent-placement-v1',
    'building_id': contract['id'],
    'method': 'Independent actual GLB indexed triangles -> nondegenerate XY projection union. Independent MapLibre mean-earth-radius physical-metre Mercator projection and heading inversion. Convex hull is only the external envelope.',
    'bindings': [binding(AUDIT / 'independent-geometry-check.mjs'),
                 binding(AUDIT / 'independent-geometry.json'),
                 binding(AUDIT / 'footprint-review.json')],
    'placement': {key: contract[key] for key in ['lng', 'lat', 'heading', 'scale', 'altitude']},
    'owner': contract['owner'],
    'source_area_m2': source.area,
    'replacement_symmetric_difference_from_own_source_m2': source.symmetric_difference(replacement).area,
    'original_source_uncovered_by_replacement_m2': source.difference(replacement).area,
    'replacement_extra_area_outside_source_m2': replacement.difference(source).area,
    'replacement_normal_expansion_m': .13,
    'replacement_maximum_euclidean_corner_expansion_m': expansion,
    'replacement_matches_independent_source_mitre_buffer_m2': expected_replacement.symmetric_difference(replacement).area,
    'source_scope_notes': 'Only the named Cathay Mansions main slab source. Projection geometry is an exterior occupancy envelope; it does not verify interiors or a hidden courtyard.',
    'assets': {},
}
unions = {}
for role in ['raw', 'full', 'lod']:
    payload = (PRIVATE / (role + '-plan-triangles.json')).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == geometry['assets'][role]['actualPlanProjection']['trianglePayloadSHA256']
    triangles = json.loads(payload)
    occupied = unary_union([Polygon(points) for points in triangles])
    assert occupied.is_valid and not occupied.is_empty
    unions[role] = occupied
    hull = Polygon(geometry['assets'][role]['actualPlanConvexHull'])
    assert occupied.difference(hull.buffer(1e-6)).area < 1e-5
    outside = occupied.difference(collision).area
    assert outside < 1e-5, (role, outside)
    source_outside_allowance = source.difference(occupied.buffer(.65)).area
    clip_outside_allowance = replacement.difference(occupied.buffer(.84)).area
    assert source_outside_allowance < 1e-7, (role, source_outside_allowance)
    assert clip_outside_allowance < 1e-7, (role, clip_outside_allowance)
    north_void = box(-9, 8.3, 9, 15.8)
    void_overlap = occupied.intersection(north_void).area
    assert void_overlap < 1e-7, (role, 'north recess filled', void_overlap)
    neighbor_rows = []
    for neighbor in neighbors:
        other = transform(local, shape(neighbor['source_geometry']))
        intersections = {
            'actual_plan_intersection_m2': occupied.intersection(other).area,
            'replacement_intersection_m2': replacement.intersection(other).area,
            'collision_intersection_m2': collision.intersection(other).area,
        }
        # Both the frozen source and its bounded native-overhang correction
        # can spatially overlap an independently owned neighbor. Actual no-ID
        # near protection requires the separate runtime group-owner filter.
        assert intersections['actual_plan_intersection_m2'] < 1e-5, (role, neighbor['source_id'], intersections)
        assert intersections['collision_intersection_m2'] < 1e-5, (role, neighbor['source_id'], intersections)
        source_overlap = source.intersection(other).area
        assert abs(intersections['replacement_intersection_m2'] - expected_replacement.intersection(other).area) < 1e-6
        neighbor_rows.append({'source_id': neighbor['source_id'], 'name': neighbor.get('name'),
                              **intersections, 'frozen_source_spatial_overlap_m2': source_overlap,
                              'replacement_names_this_neighbor': neighbor['source_id'] in contract['source_feature_ids']['building'],
                              'actual_plan_clearance_m': occupied.distance(other)})
    report['assets'][role] = {
        'sha256': geometry['assets'][role]['sha256'],
        'decoded_projection_triangles': len(triangles),
        'actual_occupied_plan_area_m2': occupied.area,
        'actual_plan_convex_hull_area_m2': hull.area,
        'actual_plan_projection_local_xy': mapping(occupied),
        'occupied_plan_outside_collision_m2': outside,
        'source_outside_occupied_plan_m2': source.difference(occupied).area,
        'source_outside_actual_plan_buffer_0_65m_m2': source_outside_allowance,
        'display_clip_outside_actual_plan_buffer_0_84m_m2': clip_outside_allowance,
        'source_max_vertex_distance_to_actual_plan_m': max(occupied.distance(Point(p)) for p in source.exterior.coords),
        'north_recess_box_local_xy': [-9, 8.3, 9, 15.8],
        'north_recess_box_area_m2': north_void.area,
        'north_recess_occupied_area_m2': void_overlap,
        'neighbors': neighbor_rows,
    }
assert unions['raw'].symmetric_difference(unions['full']).area < 1e-7
report['raw_full_actual_plan_symmetric_difference_m2'] = unions['raw'].symmetric_difference(unions['full']).area
report['raw_lod_actual_plan_symmetric_difference_m2'] = unions['raw'].symmetric_difference(unions['lod']).area
report['source_specific_clip_note'] = 'Replacement is the independently verified 0.13m-normal mitre buffer of the Cathay source and names only owner3146. Spatial overlap is recorded, not hidden. Actual model and collision geometry have zero neighbor area overlap. No-ID near geometry cannot infer protection from metadata alone: separate runtime/browser checks must verify streamed group membership excludes the eastern tile while retaining the other owners in the shared Cathay tile. Actual old-near envelope measurements are attributed to footprint-review, not claimed as repeated here.'
report['status'] = 'pass'
(AUDIT / 'independent-placement.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({role: {k: v for k, v in row.items() if k.endswith('_m2') or k.endswith('_m')} for role, row in report['assets'].items()}, ensure_ascii=False))
