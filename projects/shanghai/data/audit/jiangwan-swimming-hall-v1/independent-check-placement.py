"""Independent final swimming-hall placement from reviewer-decoded triangles.

Usage: review-directory immutable-city-input contract.json output.json
Low occupied slabs, conservative enclosed-room fills and display correction
are measured separately. No author geometry rebuild or mapper triangles used.
"""
from pathlib import Path
import gzip, hashlib, json, math, sys
from shapely.geometry import shape, mapping, Polygon, Point
from shapely.ops import transform, unary_union

R, M, C, O = map(Path, sys.argv[1:5])
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

contract = json.loads(C.read_text())
report = json.loads((R / 'independent-geometry-review.json').read_text())
table = json.loads(gzip.decompress((M / 'macro-feature-table.json.gz').read_bytes()))
original = json.loads((R / 'independent-original-city-projection.json').read_text())
package = json.loads((R / 'independent-packaging-binding.json').read_text())
assert contract['id'] == report['modelId'] == 'yangpu-jiangwan-swimming-hall'
assert [contract[k] for k in ['heading', 'scale', 'altitude']] == [0, 1, 0]
immutable_frame = json.loads((M / 'initial-local-frame.json').read_text())['anchor']
assert [contract['lng'], contract['lat']] == [immutable_frame['lng'], immutable_frame['lat']]
assert contract['model_geometry_sha256'] == {
    key: report['assets'][role]['sha256']
    for key, role in [('raw', 'raw'), ('web', 'full'), ('lod', 'lod')]}
assert contract['model_manifest_sha256'] == package['final_manifest']['sha256']
k = 6371008.8 * math.cos(math.radians(contract['lat']))
psi = math.asinh(math.tan(math.radians(contract['lat'])))
def local(lng, lat, z=None):
    return k * math.radians(lng - contract['lng']), k * (math.asinh(math.tan(math.radians(lat))) - psi)

sources = {r['localId']: transform(local, shape(r['geometry'])) for r in table['features']}
assert len(sources) == 2324
source = sources[1666]
mask = transform(local, shape(contract['replacement_geometry']))
preflight = json.loads((M / 'clip-preflight.json').read_text())
assert digest(M / 'clip-preflight.json') == original['bindings']['clip_preflight_sha256']
assert mask.symmetric_difference(shape(preflight['mask_geometry_local_enu'])).area < 1e-5
assert mask.is_valid and source.difference(mask).area < 1e-6
collision_wgs = shape(contract['collision_geometry'])
collision = transform(local, collision_wgs)
assert collision_wgs.is_valid and collision.is_valid
parts = list(collision.geoms) if collision.geom_type == 'MultiPolygon' else [collision]
counts = [[len(p.exterior.coords)] + [len(r.coords) for r in p.interiors] for p in parts]
assert len(parts) <= 32 and max(map(len, counts)) <= 32
assert max(n for r in counts for n in r) <= 256 and sum(map(sum, counts)) <= 4096

occupancies = {}
assetrows = []
for role in ['raw', 'full', 'lod']:
    asset = report['assets'][role]
    path = R / 'independent-occupancy' / (asset['sha256'] + '.json')
    occ = json.loads(path.read_text())
    assert occ['asset_sha256'] == asset['sha256']
    assert occ['triangle_payload_sha256'] == asset['actualTrianglesENU']['sha256']
    full = shape(occ['full_projection']['geometry_local_xy'])
    low = shape(occ['standing_slab']['geometry_local_xy'])
    assert full.is_valid and low.is_valid
    occupancies[role] = (full, low)
    missed = low.difference(collision).area
    assert missed < 1e-5, (role, missed)
    foreign = [{'source_local_id': i, 'full_overlap_m2': full.intersection(s).area,
                'low_overlap_m2': low.intersection(s).area}
               for i, s in sources.items() if i != 1666]
    bad = [r for r in foreign if max(r['full_overlap_m2'], r['low_overlap_m2']) > 1e-6]
    assert not bad, bad
    assetrows.append({'role': role, 'asset_sha256': asset['sha256'],
                      'occupancy_sha256': digest(path),
                      'full_projection_area_m2': full.area, 'standing_slab_area_m2': low.area,
                      'standing_slab_outside_collision_m2': missed,
                      'other_original_sources_checked': len(foreign), 'nonzero_foreign_overlap': bad,
                      'source_projection_comparison': {
                          'source_area_m2': source.area,
                          'source_not_covered_by_full_projection_m2': source.difference(full).area,
                          'full_projection_fraction_of_source': source.intersection(full).area / source.area}})

lowunion = unary_union([item[1] for item in occupancies.values()])
lowparts = list(lowunion.geoms) if lowunion.geom_type == 'MultiPolygon' else [lowunion]
# Only large closed rooms entirely enclosed by actual wall/threshold occupancy
# and inside the original swimming source may be conservatively inaccessible.
holes = [Polygon(ring) for p in lowparts for ring in p.interiors if Polygon(ring).area > 100]
assert len(holes) == 2, [(p.area, p.bounds) for p in holes]
assert all(p.difference(source).area < 1e-6 for p in holes)
enclosed = unary_union(holes)
filled = lowunion.union(enclosed)
expected_collision = filled.buffer(.05, join_style=2).simplify(.02, preserve_topology=True)
policy_difference = collision.symmetric_difference(expected_collision).area
assert policy_difference < 1e-4, policy_difference
extra = collision.difference(filled.buffer(.08, join_style=2)).area
assert extra < 1e-5, extra
assert enclosed.difference(collision).area < 1e-5
foreign = [{'source_local_id': i, 'collision_overlap_m2': collision.intersection(s).area,
            'display_mask_overlap_m2': mask.intersection(s).area}
           for i, s in sources.items() if i != 1666]
bad = [r for r in foreign if max(r['collision_overlap_m2'], r['display_mask_overlap_m2']) > 1e-6]
assert not bad, bad
neighbors = []
for variant in original['actual_city_sources']:
    for comp in variant['components']:
        if comp['owner'] == 1666:
            assert shape(comp['geometry_local_xy']).difference(mask).area < 1e-6
            continue
        g = shape(comp['geometry_local_xy'])
        row = {'variant': variant['variant'], 'source_local_id': comp['owner'],
               'collision_overlap_m2': g.intersection(collision).area,
               'display_mask_overlap_m2': g.intersection(mask).area,
               'full_model_overlap_m2': max(g.intersection(f).area for f, l in occupancies.values())}
        assert max(row[key] for key in ['collision_overlap_m2', 'display_mask_overlap_m2', 'full_model_overlap_m2']) < 1e-6
        neighbors.append(row)
controls = []
probes = json.loads((R / 'independent-probes.json').read_text())
for control in probes['ground_controls']:
    point = Point(control['point_local_xy'])
    row = {**control, 'actual_low_covered': lowunion.covers(point),
           'collision_covered': collision.covers(point),
           'full_projection_covered': any(f.covers(point) for f, l in occupancies.values())}
    assert row['actual_low_covered'] == control['expected_low_covered']
    assert row['collision_covered'] == control['expected_collision_covered']
    assert row['full_projection_covered'] == control['expected_full_covered']
    controls.append(row)
neighbor_context = json.loads((R / 'independent-neighbor-context.json').read_text())
detailed_neighbors = []
for context in neighbor_context['records']:
    old_frame = context['frame']
    assert [old_frame[x] for x in ['heading','scale','altitude']] == [0,1,0]
    old_k = 6371008.8 * math.cos(math.radians(old_frame['lat']))
    old_psi = math.asinh(math.tan(math.radians(old_frame['lat'])))
    def old_to_current(x,y,z=None):
        lng=old_frame['lng']+math.degrees(x/old_k)
        lat=math.degrees(math.atan(math.sinh(old_psi+y/old_k)))
        return local(lng,lat)
    envelope = transform(old_to_current, Polygon(context['actual_full_projection_convex_hull']))
    overlap = max(f.intersection(envelope).area for f,l in occupancies.values())
    collision_overlap = collision.intersection(envelope).area
    assert max(overlap, collision_overlap) < 1e-6
    detailed_neighbors.append({'id':context['id'],'old_full_asset_sha256':context['old_full_asset_sha256'],
        'full_model_overlap_with_containing_envelope_m2':overlap,
        'collision_overlap_with_containing_envelope_m2':collision_overlap,
        'full_model_distance_to_containing_envelope_m':min(f.distance(envelope) for f,l in occupancies.values()),
        'collision_distance_to_containing_envelope_m':collision.distance(envelope)})
road_context = json.loads((R / 'independent-road-context.json').read_text())
assert road_context['frame'] == immutable_frame
roads = []
old_tolerance_collision = filled.buffer(.12, join_style=2).simplify(.05, preserve_topology=True)
for way in road_context['records']:
    line = shape(way['geometry_local_xy'])
    road = {'id':way['id'],'highway':way['tags']['highway'],
        'actual_low_distance_to_centerline_m':lowunion.distance(line),
        'collision_distance_to_centerline_m':collision.distance(line),
        'centerline_intersection_length_m':line.intersection(collision).length,
        'shoulder_038_overlap_m2':line.buffer(.38).intersection(collision).area,
        'previous_012_buffer_shoulder_038_overlap_m2':line.buffer(.38).intersection(old_tolerance_collision).area}
    assert road['centerline_intersection_length_m'] < 1e-7
    assert road['shoulder_038_overlap_m2'] < 1e-6, road
    roads.append(road)
assert len(roads) == 22
assert contract['expected_replacement_triangle_count'] == 16
assert contract['expected_global_clip_triangle_count'] == 218
assert contract['expected_global_clip_capacity'] == 224
output = {
    'schema': 'jiangwan-swimming-hall-independent-final-placement-v1', 'passed': True,
    'candidate_id': contract['id'],
    'method': 'Independent actual GLB scene-world indexed triangles, independent z0..2 clipping/union and immutable original-feature projection. Large closed interior voids are separately measured and conservatively blocked. Display mask is not collision.',
    'bindings': {'contract_sha256': digest(C),
                 'geometry_report_sha256': digest(R / 'independent-geometry-review.json'),
                 'packaging_binding_sha256': digest(R / 'independent-packaging-binding.json'),
                 'original_source_review_sha256': digest(R / 'independent-original-city-projection.json'),
                 'script_sha256': digest(Path(__file__)),
                 'reviewer_probes_sha256': digest(R / 'independent-probes.json'),
                 'immutable_detailed_neighbor_context_sha256': digest(R / 'independent-neighbor-context.json'),
                 'independent_road_context_sha256': digest(R / 'independent-road-context.json')},
    'frame': {key: contract[key] for key in ['lng', 'lat', 'heading', 'scale', 'altitude']},
    'assets': assetrows,
    'collision': {'valid_wgs84_and_local': True, 'polygons': len(parts),
                  'ring_point_counts': counts, 'total_ring_points': sum(map(sum, counts)),
                  'area_m2': collision.area, 'actual_all_role_low_union_area_m2': lowunion.area,
                  'conservative_enclosed_room_fills': [{'area_m2': p.area, 'geometry_local_xy': mapping(p),
                                                       'outside_original_source_m2': p.difference(source).area} for p in holes],
                  'conservative_fill_total_area_m2': enclosed.area,
                  'buffer_m':.05,'simplify_m':.02,
                  'symmetric_difference_from_independently_rebuilt_policy_m2':policy_difference,
                  'extra_beyond_filled_low_union_buffer_008m_m2': extra,
                  'other_original_sources_checked': len(foreign), 'nonzero_foreign_overlap': bad},
    'ground_controls': controls, 'actual_foreign_native_projections': neighbors,
    'specific_retained_sources': {str(i): {
        'source_area_m2': sources[i].area,
        'full_model_distance_m': min(f.distance(sources[i]) for f, l in occupancies.values()),
        'collision_distance_m': collision.distance(sources[i]),
        'display_mask_distance_m': mask.distance(sources[i])} for i in [1646, 1816, 1558]},
    'retained_detailed_neighbors': {
        'method':'Immutable prior independent actual full-triangle convex hulls, transformed through both anchor frames; containing envelopes are conservative. No historical asset matrix or old model decode.',
        'records':detailed_neighbors},
    'road_centerlines_and_shoulders':{'source':road_context['source_receipt'],'records':roads,
        'note':'All22 mapped highway ways reconstructed independently. Smaller numerical padding preserves actual low geometry; widths and public access are not surveyed.'},
    'display_mask_unchanged_from_independent_preflight': True,
    'display_mask_expected_triangles': len(mask.exterior.coords) - 3,
    'global_display_mask_catalogue_total_triangles': 218, 'global_display_mask_capacity': 224,
    'model_projection_differences_m2': {
        'raw_full': occupancies['raw'][0].symmetric_difference(occupancies['full'][0]).area,
        'raw_lod': occupancies['raw'][0].symmetric_difference(occupancies['lod'][0]).area},
    'limits': 'Source display removal and actual physical roof projection are distinct. Closed unmodeled interior areas are conservatively blocked. Smaller numerical collision padding does not remove any physical geometry or prove a measured public path width. No interior walkthrough, current survey or whole sports-centre completion is certified.'}
O.write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps({'passed': True, 'assets': len(assetrows), 'collision_points': sum(map(sum, counts)),
                  'actual_low_area_m2': lowunion.area, 'closed_room_fill_area_m2': enclosed.area,
                  'ground_controls': len(controls)}))
