"""Independent final placement checks from delivered and original city triangles.

Usage: python independent-placement-check.py new-plan-triangles-dir old-city-decode-dir
No author construction or mapper triangle payloads are imported. Six further city
near groups are geometric crosschecks of the mapper's bound decoded projections,
explicitly separate from the independently decoded complete own near group.
"""
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
from shapely import polygons
from shapely.geometry import Point, Polygon, box, mapping, shape
from shapely.ops import transform, unary_union

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parents[2]
NEW, OLD = map(Path, sys.argv[1:3])

def load(p):
    return json.loads(Path(p).read_text())

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def binding(p):
    p = Path(p)
    return {'file': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)}

geometry = load(AUDIT / 'independent-geometry.json')
footprint = load(AUDIT / 'footprint-review.json')
city = load(OLD / 'city-source-decode.json')
c = footprint['proposed_placement_contract']
assert c['id'] == 'huangpu-shanghai-municipal-council'
assert c['owner']['feature_local_id'] == 1554
assert c['owner']['macro_id'] == '14-13720-6694'
assert c['partial_model'] is True and c['listed_place_scope_is_partial'] is True
assert c['source_feature_ids'] == {'building': [footprint['identity']['source_id']], 'building_part': []}
assert c['source_limit_geometry'] == footprint['geometry']['source_geometry_wgs84']
assert (c['scale'], c['altitude']) == (1, 0)
assert c['expected_replacement_triangle_count'] == 24
assert c['expected_global_clip_triangle_count'] == 137
assert c['navigation']['listed'] is False
ang = math.radians(c['heading'])
co, si = math.cos(ang), math.sin(ang)
k = 6371008.8 * math.cos(math.radians(c['lat']))
psi = math.asinh(math.tan(math.radians(c['lat'])))

def local(lng, lat, z=None):
    east = math.radians(lng - c['lng']) * k
    north = (math.asinh(math.tan(math.radians(lat))) - psi) * k
    return co * east - si * north, si * east + co * north

source = transform(local, shape(c['source_limit_geometry']))
clip = transform(local, shape(c['replacement_geometry']))
collision = transform(local, shape(c['collision_geometry']))
retained = transform(local, shape(c['remaining_source_geometry']))
historical = shape(footprint['historical_scope_review']['source_historical_subset_geometry_local_xy'])
uncertain = shape(footprint['historical_scope_review']['uncertainty_band_local_geometry'])
domain = unary_union([box(-1000, 36, 1000, 1000), box(-18, -1000, 1000, 1000)])
assert all(p.is_valid for p in [source, clip, collision, retained, uncertain, historical])
TOL = 1e-5  # WGS84 storage/roundtrip polygon area tolerance, in square metres.
assert historical.symmetric_difference(source.intersection(domain)).area < TOL
assert clip.symmetric_difference(source.buffer(.13, join_style=2).intersection(domain)).area < TOL
assert retained.symmetric_difference(source.difference(clip)).area < TOL
assert uncertain.difference(retained.buffer(1e-7)).area < TOL
assert clip.intersection(uncertain).area < TOL
assert collision.intersection(uncertain).area < TOL
assert collision.difference(domain).area < TOL
assert len(collision.exterior.coords) <= 65 and len(collision.interiors) == 0
neighbors = footprint['exclusions']['context_sources_within_80m']
assert len(neighbors) == 66
neighbor_shapes = {row['local_id']: transform(local, shape(row['source_geometry_wgs84'])) for row in neighbors}
source_map = {1554: source, **neighbor_shapes}
negative_boxes = {name: box(*bounds) for name, bounds in footprint['exclusions']['courtyard_negative_test_boxes_local_xy_m'].items()}
for test in negative_boxes.values():
    assert clip.intersection(test).area < TOL
    assert collision.intersection(test).area < TOL
    assert all(p.intersection(test).area < TOL for p in source_map.values())

original = []
original_near_foreign = []
for variant in ['far', 'near']:
    row = next(r for r in city['variants'] if r['variant'] == variant)
    assert any(b['sha256'] == row['input']['sha256'] for b in footprint['source_bindings'])
    path = OLD / row['output']['file']
    assert sha(path) == row['output']['sha256']
    vertices = np.fromfile(path, dtype='<f8').reshape(-1, 3, 3)
    xy = vertices[:, :, :2]
    e1, e2 = xy[:, 1] - xy[:, 0], xy[:, 2] - xy[:, 0]
    nondegenerate = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) > 1e-10
    projection = unary_union(polygons(xy[nondegenerate]))
    components = list(projection.geoms)
    assert len(components) == 5
    classified = []
    own = None
    for component in components:
        hits = sorted(((component.intersection(p).area, key) for key, p in source_map.items()), reverse=True)
        area, owner = hits[0]
        assert area / source_map[owner].area > .99999
        assert hits[1][0] < TOL
        assert component.difference(source_map[owner].buffer(.13, join_style=2)).area < TOL
        if owner == 1554:
            assert own is None
            own = component
        else:
            assert component.intersection(clip).area < TOL
            assert component.intersection(collision).area < TOL
            if variant == 'near':
                original_near_foreign.append(component)
        classified.append({'owner': owner, 'area_m2': component.area,
                           'source_coverage_fraction': area / source_map[owner].area,
                           'clip_overlap_m2': component.intersection(clip).area})
    assert {r['owner'] for r in classified} == {1554, 1898, 1086, 2652, 211}
    assert own.intersection(domain).difference(clip).area < TOL
    remainder = own.difference(clip)
    assert own.intersection(uncertain).difference(remainder.buffer(1e-7)).area < TOL
    # Independent vertical ray/triangle test: barycentric XY inclusion yields
    # actual indexed triangle surface height, including normalized instances.
    probe_rows = []
    for p in footprint['retained_source_regions']['roof_probes']:
        x, y = p['local_xy_m']
        a = xy[:, 0]
        determinant = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
        valid = np.abs(determinant) > 1e-10
        u = np.zeros(len(xy)); v = np.zeros(len(xy))
        u[valid] = ((x-a[:, 0])*e2[:, 1] - (y-a[:, 1])*e2[:, 0])[valid] / determinant[valid]
        v[valid] = (e1[:, 0]*(y-a[:, 1]) - e1[:, 1]*(x-a[:, 0]))[valid] / determinant[valid]
        inside = valid & (u >= -1e-7) & (v >= -1e-7) & (u+v <= 1+1e-7)
        heights = (vertices[:, 0, 2] + u*(vertices[:, 1, 2]-vertices[:, 0, 2]) + v*(vertices[:, 2, 2]-vertices[:, 0, 2]))[inside]
        assert len(heights) and abs(float(heights.max()) - p['actual_native_roof_height_m']) < .001
        assert remainder.covers(Point(x, y)) and not clip.covers(Point(x, y))
        assert math.dist(local(*p['wgs84']), [x, y]) < 1e-5
        probe_rows.append({'name': p['name'], 'local_xy_m': [x, y], 'actual_indexed_roof_height_m': float(heights.max()), 'surface_hits': len(heights), 'remains_outside_clip': True})
    original.append({'variant': variant, 'input': row['input'], 'expanded_triangles': row['expandedTriangles'],
                     'selected_triangles': len(vertices), 'decoded_triangle_binding': row['output'],
                     'components': classified, 'own_projection_area_m2': own.area,
                     'own_domain_uncovered_m2': own.intersection(domain).difference(clip).area,
                     'retained_projection_area_m2': remainder.area,
                     'uncertain_band_preserved_m2': remainder.intersection(uncertain).area,
                     'roof_probes': probe_rows})
    if variant == 'near':
        retained_near = remainder

# These extra six groups were decoded by the independent mapping agent, not
# by this script. Their bound polygons provide an additional crosscheck only.
extra_groups = footprint['baseline_foreign_native_group_preservation']['groups']
assert len(extra_groups) == 6
external = [shape(r['actual_group_projection_local_xy']) for r in extra_groups]
for p in [*original_near_foreign, *external]:
    assert p.intersection(clip).area < TOL
    assert p.intersection(collision).area < TOL

report = {'schema': 'municipal-council-independent-placement-v1', 'model_id': c['id'],
          'method': 'Independent actual indexed/instanced triangles and physical-Mercator coordinate transform. Preserve concave unions, source remainder and uncertain join bands; convex hull is not occupied courtyard geometry.',
          'bindings': [binding(AUDIT / name) for name in ['independent-placement-check.py', 'independent-geometry-check.mjs', 'independent-geometry.json', 'independent-probes.json', 'independent-city-source-check.mjs', 'footprint-review.json']],
          'source_area_m2': source.area, 'historical_source_subset_area_m2': historical.area,
          'display_clip_area_m2': clip.area, 'display_clip_outside_source_m2': clip.difference(source).area,
          'source_retained_area_m2': retained.area, 'source_retained_fraction': retained.area/source.area,
          'retained_uncertain_band_area_m2': uncertain.area, 'uncertain_band_clip_overlap_m2': clip.intersection(uncertain).area,
          'collision_closed_ring_points': len(collision.exterior.coords),
          'roundtrip_area_tolerance_m2': TOL, 'original_city_independent_checks': original,
          'other_six_native_group_crosscheck': {'dependency': 'Mapper independently decoded actual groups; not claimed as reviewer re-decoding', 'groups': [{'representative_owner': r['representative_owner'], 'file': r['file'], 'sha256': r['sha256'], 'clip_overlap_m2': p.intersection(clip).area, 'collision_overlap_m2': p.intersection(collision).area} for r,p in zip(extra_groups,external)]},
          'assets': {}, 'navigation': 'Overview-only: conservative horizontal collision includes roofs and does not certify navigable ground passages.'}
mapper_raw = shape(next(r for r in footprint['actual_model_envelope_review']['records'] if r['variant'] == 'raw')['actual_triangle_projection_geometry_local_xy'])
ordered_formula = mapper_raw.buffer(.22, join_style=2).simplify(.30, preserve_topology=True).intersection(domain)
assert ordered_formula.symmetric_difference(collision).area < TOL
report['collision_formula_replay'] = {
    'method': 'Replay on the frozen mapper raw union ring ordering, after independent triangle-union equivalence is checked below. Douglas-Peucker is sensitive to boundary start/order; that is distinct from occupied-plan geometry.',
    'formula': 'actual_raw_union.buffer(0.22, join_style=mitre).simplify(0.30, preserve_topology=True) intersect D',
    'ordered_formula_symmetric_difference_from_stored_wgs_collision_m2': ordered_formula.symmetric_difference(collision).area,
    'ordered_formula_closed_ring_points': len(ordered_formula.exterior.coords)}
unions = {}
for role in ['raw', 'full', 'lod']:
    path = NEW / (role+'-plan-triangles.json')
    assert sha(path) == geometry['assets'][role]['actualPlanProjection']['trianglePayloadSHA256']
    triangles = load(path)
    actual = unary_union(polygons(np.asarray(triangles)))
    assert actual.is_valid and not actual.is_empty
    unions[role] = actual
    assert actual.symmetric_difference(mapper_raw).area < TOL
    hull = Polygon(geometry['assets'][role]['actualPlanConvexHull'])
    assert actual.difference(hull.buffer(1e-6)).area < TOL
    assert actual.difference(collision).area < TOL
    assert actual.intersection(retained).area < TOL
    assert actual.intersection(retained_near).area < TOL
    assert actual.intersection(uncertain).area < TOL
    assert actual.difference(domain).area < TOL
    assert clip.difference(actual.buffer(1)).area < TOL
    assert collision.difference(actual.buffer(.55)).area < TOL
    assert all(actual.intersection(p).area < TOL for p in [*original_near_foreign, *external])
    formula_collision = actual.buffer(.22, join_style=2).simplify(.30, preserve_topology=True).intersection(domain)
    # Douglas-Peucker simplification depends on the ring start/order; record
    # symmetric difference and independently enforce the declared safety bounds.
    formula_difference = formula_collision.symmetric_difference(collision).area
    neighbor_rows = []
    for row in neighbors:
        p = neighbor_shapes[row['local_id']]
        overlaps = [actual.intersection(p).area, clip.intersection(p).area, collision.intersection(p).area]
        assert max(overlaps) < TOL
        neighbor_rows.append({'local_id': row['local_id'], 'source_id': row['source_id'], 'actual_clip_collision_overlap_m2': overlaps, 'actual_gap_m': actual.distance(p)})
    negative = {}
    for name, p in negative_boxes.items():
        overlap = actual.intersection(p).area
        assert overlap < TOL
        negative[name] = {'actual_area_m2': overlap, 'clip_area_m2': clip.intersection(p).area, 'collision_area_m2': collision.intersection(p).area}
    boundary = clip.exterior
    distances = [actual.distance(boundary.interpolate(d)) for d in np.arange(0, boundary.length, .05)]
    report['assets'][role] = {'sha256': geometry['assets'][role]['sha256'], 'actual_plan_area_m2': actual.area,
                            'actual_convex_hull_area_m2': hull.area, 'actual_plan_projection_local_xy': mapping(actual),
                            'occupied_outside_collision_m2': actual.difference(collision).area,
                            'occupied_retained_native_overlap_m2': actual.intersection(retained_near).area,
                            'occupied_uncertain_band_overlap_m2': actual.intersection(uncertain).area,
                            'clip_outside_actual_round_0_55m_buffer_m2': clip.difference(actual.buffer(.55)).area,
                            'clip_outside_actual_round_1m_buffer_m2': clip.difference(actual.buffer(1)).area,
                            'maximum_sampled_clip_boundary_to_actual_gap_m': max(distances), 'boundary_sampling_step_m': .05,
                            'collision_formula_symmetric_difference_m2': formula_difference,
                            'mapper_raw_union_symmetric_difference_m2': actual.symmetric_difference(mapper_raw).area,
                            'collision_outside_actual_round_0_55m_buffer_m2': collision.difference(actual.buffer(.55)).area,
                            'negative_courtyards': negative, 'neighbors': neighbor_rows}
assert unions['raw'].symmetric_difference(unions['full']).area < 1e-8
assert unions['raw'].symmetric_difference(unions['lod']).area < TOL
report['raw_full_symmetric_difference_m2'] = unions['raw'].symmetric_difference(unions['full']).area
report['raw_lod_symmetric_difference_m2'] = unions['raw'].symmetric_difference(unions['lod']).area
report['status'] = 'pass'
(AUDIT/'independent-placement.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'passed': True, 'source_retained_m2': retained.area, 'near_retained_m2': retained_near.area, 'asset_areas_m2': {k:v['actual_plan_area_m2'] for k,v in report['assets'].items()}, 'collision_formula_diff_m2': {k:v['collision_formula_symmetric_difference_m2'] for k,v in report['assets'].items()}}))
