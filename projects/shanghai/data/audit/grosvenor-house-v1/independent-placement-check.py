"""Independently verify the Grosvenor partial correction from decoded triangles.

Input is the private projection directory emitted by this delivery's independent
GLB decoder. Old native-city measurements belong to the mapper; this script
does not claim to repeat their GLTF instance expansion.
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
    return {'file': str(path.relative_to(ROOT)), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


decoded = load(AUDIT / 'independent-geometry.json')
footprint = load(AUDIT / 'footprint-review.json')
contract = footprint['proposed_placement_contract']
assert contract['id'] == 'huangpu-grosvenor-house'
assert contract['owner']['feature_local_id'] == 2398
assert contract['source_feature_ids']['building'] == [footprint['identity']['source_id']]
assert contract['source_feature_ids'].get('building_part', []) == []
assert contract['source_limit_geometry'] == footprint['geometry']['source_geometry']
assert contract['partial_model'] is True
angle = math.radians(contract['heading'])
c, s = math.cos(angle), math.sin(angle)
lat0 = math.radians(contract['lat'])
scale = 6371008.8 * math.cos(lat0)
my0 = math.log(math.tan(math.pi / 4 + lat0 / 2))


def local(lng, lat, z=None):
    east = math.radians(lng - contract['lng']) * scale
    north = (math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) - my0) * scale
    return c * east - s * north, s * east + c * north


source = transform(local, shape(contract['source_limit_geometry']))
clip = transform(local, shape(contract['replacement_geometry']))
collision = transform(local, shape(contract['collision_geometry']))
retained = transform(local, shape(contract['remaining_source_geometry']))
assert all(p.is_valid for p in [source, clip, collision, retained])
assert source.difference(clip).symmetric_difference(retained).area < 1e-5
exclusions = footprint['exclusions']
neighbors = list({n['source_id']: n for n in [
    *exclusions['all_macro_neighbors_within_65m'],
    *exclusions.get('required_context_sources', [])]}.values())
forecourt = box(*footprint['geometry']['south_front_open_space_test_box_local_xy_m'])
assert clip.intersection(forecourt).area < 1e-7
assert collision.intersection(forecourt).area < 1e-7

report = {
    'schema': 'grosvenor-independent-placement-v1', 'building_id': contract['id'],
    'method': 'Independent actual GLB indexed triangles -> nondegenerate horizontal union. Independently reconstruct MapLibre physical-metre Mercator and inverse heading. Verify the declared partial display clip and retained source without treating the convex hull as a filled plan.',
    'bindings': [binding(AUDIT / 'independent-geometry-check.mjs'),
                 binding(AUDIT / 'independent-geometry.json'),
                 binding(AUDIT / 'footprint-review.json')],
    'placement': {key: contract[key] for key in ['lng', 'lat', 'heading', 'scale', 'altitude']},
    'owner': contract['owner'], 'source_area_m2': source.area,
    'display_clip_area_m2': clip.area,
    'display_clip_outside_frozen_source_m2': clip.difference(source).area,
    'retained_original_source_area_m2': retained.area,
    'retained_original_source_fraction': retained.area / source.area,
    'retained_source_matches_exact_source_minus_display_clip_m2': source.difference(clip).symmetric_difference(retained).area,
    'retained_component_areas_m2': sorted(p.area for p in (retained.geoms if hasattr(retained, 'geoms') else [retained])),
    'forecourt_test_box_local_xy': list(forecourt.bounds),
    'forecourt_display_clip_overlap_m2': clip.intersection(forecourt).area,
    'forecourt_collision_overlap_m2': collision.intersection(forecourt).area,
    'assets': {},
    'scope_note': 'The listed place and the source geometry both have an explicit remainder. Unexplained southern steps are not automatically labeled as a measured canopy footprint. An independent adjacent source, including the foreground3049, is not erased merely because it appears inconvenient.'
}
unions = {}
for role in ['raw', 'full', 'lod']:
    payload = (PRIVATE / (role + '-plan-triangles.json')).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == decoded['assets'][role]['actualPlanProjection']['trianglePayloadSHA256']
    triangles = json.loads(payload)
    occupied = unary_union([Polygon(t) for t in triangles])
    assert occupied.is_valid and not occupied.is_empty
    unions[role] = occupied
    expected_clip = source.buffer(.12, join_style=2).intersection(occupied.buffer(.5, join_style=2))
    assert expected_clip.symmetric_difference(clip).area < 1e-5, role
    assert occupied.difference(collision).area < 1e-5, role
    assert occupied.intersection(forecourt).area < 1e-7, role
    assert clip.difference(occupied.buffer(.55)).area < 1e-7, role
    hull = Polygon(decoded['assets'][role]['actualPlanConvexHull'])
    assert occupied.difference(hull.buffer(1e-6)).area < 1e-5
    neighbors_out = []
    for neighbor in neighbors:
        other = transform(local, shape(neighbor['source_geometry']))
        overlap = occupied.intersection(other).area
        collision_overlap = collision.intersection(other).area
        assert overlap < 1e-5, (role, neighbor['source_id'], overlap)
        assert collision_overlap < 1e-5, (role, neighbor['source_id'], collision_overlap)
        assert neighbor['source_id'] not in contract['source_feature_ids']['building']
        neighbors_out.append({'source_id': neighbor['source_id'], 'name': neighbor.get('name'),
                              'actual_plan_overlap_m2': overlap, 'actual_plan_gap_m': occupied.distance(other),
                              'collision_overlap_m2': collision_overlap,
                              'display_clip_spatial_overlap_m2': clip.intersection(other).area,
                              'neighbor_named_by_candidate_mask': False})
    report['assets'][role] = {
        'sha256': decoded['assets'][role]['sha256'],
        'nondegenerate_unique_projected_triangles': len(triangles),
        'actual_occupied_plan_area_m2': occupied.area,
        'actual_plan_convex_hull_area_m2': hull.area,
        'actual_plan_projection_local_xy': mapping(occupied),
        'occupied_plan_outside_collision_m2': occupied.difference(collision).area,
        'forecourt_actual_occupied_area_m2': occupied.intersection(forecourt).area,
        'display_clip_symmetric_difference_from_independent_partial_rule_m2': expected_clip.symmetric_difference(clip).area,
        'display_clip_outside_actual_plan_round_buffer_0_55m_m2': clip.difference(occupied.buffer(.55)).area,
        'maximum_clip_vertex_distance_to_actual_plan_m': max(occupied.distance(Point(pt)) for pt in clip.exterior.coords),
        'neighbors': neighbors_out,
    }
assert unions['raw'].symmetric_difference(unions['full']).area < 1e-7
report['raw_full_actual_plan_symmetric_difference_m2'] = unions['raw'].symmetric_difference(unions['full']).area
report['raw_lod_actual_plan_symmetric_difference_m2'] = unions['raw'].symmetric_difference(unions['lod']).area
report['status'] = 'pass'
(AUDIT / 'independent-placement.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'source_area_m2': source.area, 'clip_area_m2': clip.area,
                  'retained_source_area_m2': retained.area,
                  'assets': {role: row['actual_occupied_plan_area_m2'] for role, row in report['assets'].items()}}))
