#!/usr/bin/env python3
"""Finite outdoor navigation source screen; no model/browser acceptance.

Ground avatar/path must avoid water. Camera water proximity is informational:
an elevated camera may be over water, while model/building clearance is checked
separately. Reads frozen actual source data and writes a new report directory.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, shape

HERE = Path(__file__).resolve().parent
PROJECT = Path('/workspace/shanghai_project')
ID = 'fengxian-museum'
R = 6378137.0


def read(path):
    return json.loads(Path(path).read_text())


def desc(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def verify(row):
    path = Path(row.get('path') or row.get('source'))
    assert all(desc(path)[key] == row[key] for key in ('bytes', 'sha256')), path
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--navigation', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(HERE) and output != HERE and not output.exists()
    proposal = read(args.navigation)
    nav = proposal.get('navigation', proposal)
    assert len(nav['walkStart']) == 2 and all(math.isfinite(v) for v in nav['walkStart'])
    assert math.isfinite(nav['bearing'])
    contract_path = HERE / 'freeze-v1' / ID / 'geometry-input.json'
    contract = read(contract_path)
    lon0, lat0 = contract['anchor']
    cos0 = math.cos(math.radians(lat0))
    mercator0 = math.asinh(math.tan(math.radians(lat0)))

    def local(lon, lat):
        return (R * math.radians(lon - lon0) * cos0,
                R * (math.asinh(math.tan(math.radians(lat))) - mercator0) * cos0)

    start = local(*nav['walkStart'])
    bearing = math.radians(nav['bearing'])
    forward = (math.sin(bearing), math.cos(bearing))
    target = tuple(start[i] + 2.8 * forward[i] for i in range(2))
    eye = tuple(target[i] - 14 * math.sin(math.radians(82)) * forward[i] for i in range(2))
    probes = {'avatar': (Point(start), .38),
              'forward_5m': (LineString([start, [start[i] + 5 * forward[i] for i in range(2)]]), .38),
              'camera': (Point(eye), .12),
              'camera_boom': (LineString([target, eye]), .12)}

    context_path = HERE / 'orientation-context-v1' / 'osm-map.json'
    receipt = read(context_path.parent / 'fetch.json')
    assert receipt['status'] == 200 and all(desc(context_path)[k] == receipt[k] for k in ('bytes', 'sha256'))
    context = read(context_path)
    elements = context['elements']
    nodes = {e['id']: local(e['lon'], e['lat']) for e in elements if e['type'] == 'node'}
    ways, incomplete, invalid = [], [], []
    for way in (e for e in elements if e['type'] == 'way'):
        refs = way.get('nodes', [])
        if not refs or any(ref not in nodes for ref in refs):
            incomplete.append(way['id'])
            continue
        xy = [nodes[ref] for ref in refs]
        geom = Polygon(xy) if len(xy) > 3 and refs[0] == refs[-1] else LineString(xy) if len(xy) > 1 else Point(xy[0])
        if not geom.is_valid:
            invalid.append(way['id'])
            continue
        ways.append({'id': way['id'], 'version': way.get('version'), 'tags': way.get('tags', {}), 'geometry': geom})

    # Full lake is reconstructed by its own exact member/node identity proof,
    # not by closing the two open outer member ways separately.
    water_report_path = HERE / 'water-source-v1' / 'water-source-review.json'
    water_report = read(water_report_path)
    assert water_report['source_extraction_passed'] and water_report['water_geometry_valid']
    assert water_report['all_relation_way_nodes_present'] and water_report['museum_island_inner_way_id'] == 528982792
    verify(water_report['source'])
    assert verify(water_report['source_contract']) == contract_path.resolve()
    water_doc = read(verify(water_report['water_geometry']))
    assert water_doc['type'] == 'FeatureCollection' and len(water_doc['features']) == 1
    lake = shape(water_doc['features'][0]['geometry'])
    assert lake.is_valid and lake.geom_type == 'Polygon' and len(lake.interiors) == 5
    water_relations = [e for e in elements if e['type'] == 'relation' and (
        e.get('tags', {}).get('natural') == 'water' or 'water' in e.get('tags', {}) or
        'waterway' in e.get('tags', {}) or e.get('tags', {}).get('leisure') == 'swimming_pool')]
    pending_water = [{'id': e['id'], 'tags': e.get('tags', {})} for e in water_relations if e['id'] != 7617592]
    waters = [{'id': 7617592, 'osm_type': 'relation', 'tags': water_report['relation']['tags'], 'geometry': lake}]
    for row in ways:
        tags = row['tags']
        if tags.get('natural') == 'water' or 'waterway' in tags or 'water' in tags or tags.get('landuse') in ('reservoir', 'basin') or tags.get('leisure') == 'swimming_pool' or tags.get('amenity') == 'fountain':
            waters.append({**row, 'osm_type': 'way'})
    water_checks = [{'osm_id': row['id'], 'osm_type': row['osm_type'], 'tags': row['tags'],
                     'geometry_type': row['geometry'].geom_type,
                     'probe_clearance_m': {name: row['geometry'].distance(probe)-radius for name, (probe, radius) in probes.items()},
                     'required_ground_probes': ['avatar', 'forward_5m'],
                     'camera_water_proximity_is_informational': True}
                    for row in waters]

    # Effective retained source footprints plus the exact target owner are
    # conservative mapped obstacles. The independent actual mesh adds detail.
    neighborhood_path = HERE / 'source-neighborhood-v1.json'
    neighborhood = read(neighborhood_path)
    assert neighborhood['anchor'] == contract['anchor'] and all(r['retain'] for r in neighborhood['features'])
    for descriptor in neighborhood['source_files']:
        verify(descriptor)
    buildings = [{'id': 'owner-relation-20262808', 'name': contract['name_zh'],
                  'geometry': shape(contract['model_geometry_local_east_north_m'])}]
    buildings.extend({'id': row['key'], 'name': row.get('name'), 'geometry': shape(row['geometry_local_east_north_m'])}
                     for row in neighborhood['features'])
    buildings.extend({'id': 'live-way-' + str(row['id']), 'name': row['tags'].get('name'), 'geometry': row['geometry']}
                     for row in ways if 'building' in row['tags'] or 'building:part' in row['tags'])
    building_checks = {}
    for name, (probe, radius) in probes.items():
        rows = sorted([{'source_id': row['id'], 'name': row['name'], 'clearance_m': row['geometry'].distance(probe)-radius}
                       for row in buildings], key=lambda row: row['clearance_m'])
        building_checks[name] = {'nearest': rows[:5], 'intersections': [row for row in rows if row['clearance_m'] <= 0]}
    bounds = context['bounds']
    bbox = Polygon([local(bounds['minlon'], bounds['minlat']), local(bounds['maxlon'], bounds['minlat']),
                    local(bounds['maxlon'], bounds['maxlat']), local(bounds['minlon'], bounds['maxlat'])])
    inside_bbox = all(bbox.covers(probe.buffer(radius)) for probe, radius in probes.values())
    highways = sorted([{'osm_way': row['id'], 'tags': row['tags'], 'distance_to_start_m': row['geometry'].distance(Point(start)),
                        'distance_to_forward_sweep_m': row['geometry'].distance(probes['forward_5m'][0])}
                       for row in ways if 'highway' in row['tags']], key=lambda row: row['distance_to_start_m'])
    ground_water_ok = all(row['probe_clearance_m'][name] > 0 for row in water_checks for name in ('avatar', 'forward_5m'))
    passed = inside_bbox and not (incomplete or invalid or pending_water) and ground_water_ok and all(not row['intersections'] for row in building_checks.values())
    runtime = [PROJECT / 'src' / name for name in ('map-scene.js', 'street-interaction.js', 'walk-controller.js')]
    baseline = read(HERE / 'freeze-v1' / 'baseline.json')
    by_name = {row['file']: row for row in baseline['runtime_files']}
    for path in runtime:
        assert all(desc(path)[key] == by_name[str(path.relative_to(PROJECT))][key] for key in ('bytes', 'sha256'))
    report = {'schema': 'fengxian-v17-bounded-source-water-and-ground-review',
              'passed_source_screen_only': passed, 'final_model_accepted': False, 'browser_passed': False, 'main_written': False,
              'candidate_binding': desc(args.navigation), 'candidate_id': proposal.get('id', ID + '-exterior-candidate'),
              'candidate_navigation': {key: nav[key] for key in ('walkStart', 'bearing')},
              'controller_ground_projection_enu_m': {'start': start, 'forward_5m_end': list(probes['forward_5m'][0].coords)[-1], 'target': target, 'eye': eye},
              'fetch': receipt, 'osm_input': desc(context_path), 'query_bbox': bounds,
              'osm_counts': {kind: sum(e['type'] == kind for e in elements) for kind in ('node', 'way', 'relation')},
              'all_probe_buffers_inside_requested_bbox': inside_bbox, 'incomplete_way_node_refs': incomplete,
              'invalid_way_geometries': invalid, 'water_relations_pending': pending_water,
              'mapped_water_or_fountain_ways': water_checks, 'live_osm_building_checks': building_checks,
              'complete_water_evidence': desc(water_report_path), 'water_source_dependencies': [water_report['source'], water_report['water_geometry']],
              'effective_neighborhood': desc(neighborhood_path), 'nearest_highways': highways[:5],
              'nearest_explicit_footway': next((row for row in highways if row['tags']['highway'] == 'footway'), None),
              'runtime_source_inputs': [desc(path) for path in runtime],
              'runtime_ground_findings': {'map_collision_sources': 'Loaded building/building_part and water polygons, not automatic detailed GLB collision.',
                  'surface_registration': 'Only explicit local owner support proxies add raised walk surfaces; this ordinary model does not provide automatic support.',
                  'fallback_player_height_m': .075, 'fallback_is_surveyed_elevation': False,
                  'local_stair_platform_support_or_interior_access_verified': False, 'actual_runtime_groundAt_observed': False},
              'limitations': ['Only the external avatar disc and first 5 m sweep require positive water clearance. Elevated camera water proximity is recorded, not treated as a ground obstacle.',
                  'Camera/model/building clearance is conservative planar screening; actual corrected model and browser screenshots are separate requirements.',
                  'Mapped roads indicate context, not current pavement height, legal access, furniture clearance or an exact pedestrian route.',
                  'Lake geometry is complete for this source relation, not a current shoreline survey or exhaustive inventory of small pools.',
                  'No roof-route, stair climbing, bridge passage, interior access or arbitrary motion collision guarantee.'],
              'tool': desc(__file__)}
    output.mkdir(parents=True)
    path = output / 'source-ground-review.json'
    with path.open('x') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'report': desc(path), 'passed_source_screen_only': passed,
                      'minimum_ground_water_clearance_m': min(row['probe_clearance_m'][key] for row in water_checks for key in ('avatar', 'forward_5m')),
                      'nearest_highway': highways[0] if highways else None}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
