"""Verify original city triangles and partial replacement independently.

Inputs: private output of independent-city-source-check.mjs, author-scope input,
output JSON. This performs no model generation and does not read other models.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from shapely import polygons
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

directory, scope_path, output_path = map(Path, sys.argv[1:4])
scope = json.loads(scope_path.read_text())
decode = json.loads((directory / 'city-source-decode.json').read_text())
assert scope['source_identity']['local_id'] == 1554
source = shape(scope['current_source_local_geometry'])
historical = shape(scope['historical_scope_local_geometry'])
clip = shape(scope['provisional_replacement']['geometry_local_xy'])
retained = shape(scope['retained_source']['source_geometry_local_xy'])
uncertain = shape(scope['scope_derivation']['uncertainty_band_local_geometry'])
domain = unary_union([box(-1000, 36, 1000, 1000), box(-18, -1000, 1000, 1000)])
assert all(p.is_valid for p in [source, historical, clip, retained, uncertain])
assert historical.symmetric_difference(source.intersection(domain)).area < 1e-8
assert clip.symmetric_difference(source.buffer(.13, join_style=2).intersection(domain)).area < 1e-8
assert retained.symmetric_difference(source.difference(clip)).area < 1e-8
assert clip.intersection(uncertain).area < 1e-8
assert uncertain.difference(retained).area < 1e-8
source_map = {1554: source}
source_names = {1554: scope['source_identity']['source_id']}
for row in scope['context_sources_within_80m']:
    source_map[row['local_id']] = shape(row['source_geometry_local_xy'])
    source_names[row['local_id']] = row['source_id']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


results = []
for variant in ['far', 'near']:
    file = directory / (variant + '-triangles.f64')
    row = next(r for r in decode['variants'] if r['variant'] == variant)
    assert sha(file) == row['output']['sha256']
    vertices = np.fromfile(file, dtype='<f8').reshape(-1, 3, 3)
    xy = vertices[:, :, :2]
    delta1 = xy[:, 1] - xy[:, 0]
    delta2 = xy[:, 2] - xy[:, 0]
    twice_area = delta1[:, 0] * delta2[:, 1] - delta1[:, 1] * delta2[:, 0]
    projected = xy[np.abs(twice_area) > 1e-10]
    union = unary_union(polygons(projected))
    assert union.is_valid
    components = list(union.geoms) if hasattr(union, 'geoms') else [union]
    assert len(components) == 5
    matches = []
    own = None
    for component in components:
        overlaps = sorted(((component.intersection(p).area, key) for key, p in source_map.items()), reverse=True)
        best_area, local_id = overlaps[0]
        # Small roofs have proportionally larger eaves. Require essentially
        # complete source coverage, no alternative source overlap and a
        # bounded 0.13m normal envelope, instead of treating eaves as identity
        # mismatches merely because a small footprint has a low area ratio.
        assert best_area / source_map[local_id].area > .99999
        assert overlaps[1][0] < 1e-8
        assert component.difference(source_map[local_id].buffer(.13, join_style=2)).area < 1e-8
        if local_id == 1554:
            assert own is None
            own = component
        else:
            assert component.intersection(clip).area < 1e-8
        matches.append({'local_id': local_id, 'source_id': source_names[local_id], 'area_m2': component.area,
                        'source_intersection_fraction': best_area / component.area,
                        'source_coverage_fraction': best_area / source_map[local_id].area,
                        'outside_source_0_13m_normal_envelope_m2': component.difference(source_map[local_id].buffer(.13, join_style=2)).area,
                        'clip_intersection_m2': component.intersection(clip).area,
                        'clip_distance_m': component.distance(clip),
                        'geometry_local_xy': mapping(component)})
    assert {r['local_id'] for r in matches} == {1554, 1898, 1086, 2652, 211}
    assert own is not None
    assert own.intersection(domain).difference(clip).area < 1e-8
    native_retained = own.difference(clip)
    assert native_retained.intersection(uncertain).symmetric_difference(own.intersection(uncertain)).area < 1e-8
    results.append({'variant': variant, 'input_binding': row, 'selected_triangles': len(vertices),
                    'nondegenerate_projected_triangles': len(projected), 'component_count': len(components),
                    'owner_components': matches, 'own_projection_area_m2': own.area,
                    'own_historical_domain_uncovered_m2': own.intersection(domain).difference(clip).area,
                    'retained_own_native_projection_area_m2': native_retained.area,
                    'retained_own_native_projection_geometry_local_xy': mapping(native_retained),
                    'uncertainty_band_native_coverage_preserved_m2': native_retained.intersection(uncertain).area,
                    'native_min_height_m': float(vertices[:, :, 2].min()),
                    'native_group_max_height_m': float(vertices[:, :, 2].max())})

negative = []
for name, bounds in scope['courtyard_negative_test_boxes_local_xy_m'].items():
    test = box(*bounds)
    assert clip.intersection(test).area < 1e-8
    assert historical.intersection(test).area < 1e-8
    assert all(test.intersection(p).area < 1e-8 for p in source_map.values())
    negative.append({'name': name, 'bounds': bounds, 'clip_and_context_source_overlap_m2': 0})
report = {'schema': 'municipal-council-independent-original-city-projection-v1', 'passed': True,
          'scope': 'Original current city source and proposed partial historical domain; no authored model acceptance is claimed.',
          'method': 'Union of independently decoded actual indexed/instanced triangles, classified by dominant source overlap; not convex hulls or nominal source outlines.',
          'bindings': [{'path': str(directory / 'city-source-decode.json'), 'sha256': sha(directory / 'city-source-decode.json')},
                       {'path': str(scope_path), 'sha256': sha(scope_path)}],
          'source_area_m2': source.area, 'historical_domain_source_area_m2': historical.area,
          'display_clip_area_m2': clip.area, 'source_retained_area_m2': retained.area,
          'join_uncertainty_band_preserved_m2': uncertain.area, 'variants': results,
          'courtyard_negative_boxes': negative}
output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': True, 'source_retained': retained.area,
                  'variants': [{k: r[k] for k in ['variant', 'own_projection_area_m2', 'retained_own_native_projection_area_m2', 'own_historical_domain_uncovered_m2']} for r in results]}))
