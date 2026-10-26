#!/usr/bin/env python3
"""Freeze an existing Overture footprint with an independently verified real OSM source.

Only reads existing city sources and explicit identity-evidence JSON. Writes
geometry-input.json and mapping-report.json beside --spec. No network or models.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Point, shape, mapping
from shapely.ops import transform

R = 6378137.0
CONFIG = 'bc00ae98308d26661b45dd7dab7b5098cab3ca4c7c7f9c1490122212af5e9956'


def read(path):
    with gzip.open(path, 'rt') if path.suffix == '.gz' else path.open() as stream:
        return json.load(stream)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def mercator(lon, lat):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def inverse(x, y):
    return math.degrees(x / R), math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--spec', type=Path, required=True)
    args = parser.parse_args()
    project, spec_path = args.project.resolve(), args.spec.resolve()
    out = spec_path.parent
    assert project != out and project not in out.parents
    spec = read(spec_path)
    assert spec['geometry_source_kind'] == 'existing_overture_osm_footprint'
    evidence = read(out / spec['identity_evidence'])
    official = read(out / spec['address_identity_evidence'])
    context_record = read(out / spec['location_context_evidence'])
    osm_evidence = read(out / spec['osm_way_evidence'])
    for name, checksum in spec['evidence_sha256'].items():
        assert sha(out / 'evidence' / name) == checksum
    assert evidence['overture']['key'] == spec['key']
    assert evidence['city_detail']['macro_id'] == spec['owner_macro_id']
    sources = {}

    def record(label, path):
        item = {'bytes': path.stat().st_size, 'sha256': sha(path)}
        if path.is_relative_to(project):
            item['project_relative_path'] = str(path.relative_to(project))
        else:
            item['stage_relative_path'] = str(path.relative_to(out))
        sources[label] = item
        return item

    record('spec', spec_path)
    for label in ('identity_evidence', 'address_identity_evidence', 'location_context_evidence', 'osm_way_evidence'):
        record(label, out / spec[label])
    raw_root, city_root = project / 'data/fullcity-raw', project / 'assets/city-detail'
    raw_manifest = read(raw_root / 'manifest.json')
    manifest = read(city_root / 'manifest.json')
    record('raw_manifest', raw_root / 'manifest.json')
    record('complete_city_manifest', city_root / 'manifest.json')
    assert manifest['complete'] and manifest['configuration_sha256'] == CONFIG
    assert manifest['model_count'] == 1708 and manifest['feature_count'] == 1796419
    raw_index = {'-'.join(map(str, row['tile'])): row for row in raw_manifest['tiles']}
    city_index = {row['id']: row for row in manifest['tiles']}
    zoom, ox, oy = map(int, spec['owner_macro_id'].split('-'))
    features, owner, scanned = {}, {}, []
    for tx in range(ox - 1, ox + 2):
        for ty in range(oy - 1, oy + 2):
            macro = f'{zoom}-{tx}-{ty}'
            if macro not in raw_index:
                continue
            path = raw_root / raw_index[macro]['file']
            data = read(path)
            record('raw:' + macro, path)
            scanned.append({'macro_id': macro, 'features': len(data['features'])})
            for feature in data['features']:
                props = feature['properties']
                key = props['source_layer'] + ':' + props['id']
                assert key not in features
                features[key], owner[key] = feature, macro
    key = spec['key']
    raw = features[key]
    props = raw['properties']
    assert owner[key] == spec['owner_macro_id'] and props['district_id'] == spec['district_id']
    assert any(s.get('provider') == spec['expected_provider'] and s.get('dataset') == spec['expected_dataset'] for s in props['sources'])
    assert any(s.get('provider') == 'osm' and s.get('record_id') == spec['expected_record_id'] for s in props['sources']), 'Exact OSM source record differs'
    assert spec['expected_record_id'] == f"w{osm_evidence['way']['id']}@{osm_evidence['way']['version']}"
    nodes = {n['id']: n for n in osm_evidence['nodes']}
    assert osm_evidence['geometry']['coordinates'][0] == [[nodes[i]['lon'], nodes[i]['lat']] for i in osm_evidence['way']['nodes']]
    geo = shape(raw['geometry'])
    assert geo.is_valid and geo.geom_type in ('Polygon', 'MultiPolygon') and geo.area > 0
    projected = transform(mercator, geo)
    anchor = list(inverse(projected.centroid.x, projected.centroid.y))
    mx, my = mercator(*anchor)
    scale = math.cos(math.radians(anchor[1]))

    def local(lon, lat):
        x, y = mercator(lon, lat)
        return (x - mx) * scale, (y - my) * scale

    local_geo = transform(local, geo)
    original_osm_local = transform(local, shape(osm_evidence['geometry']))
    osm_distance_m = local_geo.hausdorff_distance(original_osm_local)
    assert osm_distance_m < 1.0, 'Existing quantized Overture footprint no longer matches its exact OSM source'
    osm_comparison = {'record_id': spec['expected_record_id'], 'original_way_version': osm_evidence['way']['version'], 'max_outline_hausdorff_m': osm_distance_m, 'original_osm_area_m2': original_osm_local.area, 'existing_city_area_m2': local_geo.area, 'frozen_geometry_is_existing_city_not_retraced': True, 'note': 'Original OSM polygon and existing MVT-derived polygon differ slightly at tile coordinate precision. Existing source coordinates are preserved exactly; no circle/corner/roof redrawing.'}
    components = [local_geo] if local_geo.geom_type == 'Polygon' else list(local_geo.geoms)
    geographic_components = [geo] if geo.geom_type == 'Polygon' else list(geo.geoms)
    all_edges = []
    for ci, component in enumerate(components):
        ring = list(component.exterior.coords)
        raw_ring = list(geographic_components[ci].exterior.coords)
        winding = 1 if component.exterior.is_ccw else -1
        for ei, (a, b) in enumerate(zip(ring, ring[1:])):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            assert length > 0
            tangent = [dx / length, dy / length]
            outward = [winding * dy / length, -winding * dx / length]
            all_edges.append({'component_index': ci, 'ring_index': 0, 'edge_index': ei,
                'source_vertex_indices': [ei, (ei + 1) % (len(ring) - 1)],
                'endpoints_wgs84': [list(raw_ring[ei]), list(raw_ring[ei + 1])],
                'endpoints_local_east_north_m': [list(a), list(b)],
                'center_local_east_north_m': [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2],
                'length_m': length, 'tangent_east_north': tangent, 'outward_normal_east_north': outward,
                'outward_azimuth_deg': math.degrees(math.atan2(outward[0], outward[1])) % 360})
    front = next(e for e in all_edges if e['component_index'] == spec['front_component_index'] and e['edge_index'] == spec['front_edge_index'])
    tables = {}

    def current(macro):
        if macro in tables:
            return tables[macro]
        index = city_index[macro]
        rp = city_root / index['near_manifest_file']
        ready = read(rp)
        tp = city_root / index['feature_table_file']
        op = rp.parent / ready['ownership_file']
        table, ownership = read(tp), dict(read(op)['owners'])
        assert ready['complete'] and ready['configuration_sha256'] == CONFIG
        assert sha(tp) == ready['published_files'][tp.name]['sha256']
        assert sha(op) == ready['published_files'][op.name]['sha256']
        for label, path in [('ready', rp), ('table', tp), ('ownership', op)]:
            record(label + ':' + macro, path)
        tables[macro] = table, ready, ownership, rp
        return tables[macro]

    macro = owner[key]
    table, ready, ownership, rp = current(macro)
    effective = next(f for f in table['features'] if f['key'] == key)
    assert effective['geometry'] == raw['geometry'] and effective['properties'] == props
    assert not effective['residual'] and effective['roof'] is None
    assert table['keys'][effective['localId']] == key and key not in ready['excluded_renderable_keys']
    near = next(t for t in ready['near'] if t['id'] == ownership[effective['localId']])
    assert effective['localId'] in near['featureLocalIds']
    near_path = rp.parent / near['file']
    assert near_path.stat().st_size == near['size_bytes'] and sha(near_path) == near['sha256']
    siblings = [f for f in table['features'] if f['localId'] in near['featureLocalIds'] and f['localId'] != effective['localId']]
    assert len(siblings) + 1 == len(near['featureLocalIds'])
    linked_parts = [f for f in features.values() if f['properties'].get('source_layer') == 'building_part' and f['properties'].get('building_id') == props['id']]
    linked_residuals = [f for f in table['features'] if f['residual'] and (f['properties'].get('id') == props['id'] or f['properties'].get('building_id') == props['id'])]
    assert not props['has_parts'] and not linked_parts and not linked_residuals
    assert key not in ready['source_roof_keys']
    adjacent = []
    search = geo.envelope.buffer(.00002)
    for other_key, feature in features.items():
        if other_key == key:
            continue
        geometry = shape(feature['geometry'])
        if not geometry.envelope.intersects(search):
            continue
        other = transform(local, geometry)
        distance = local_geo.distance(other)
        overlap = local_geo.intersection(other).area
        if distance > .75 and overlap <= 1e-8:
            continue
        ot, ore, oo, _ = current(owner[other_key])
        ef = next((f for f in ot['features'] if f['key'] == other_key), None)
        adjacent.append({'key': other_key, 'owner_macro_id': owner[other_key], 'intersection_area_m2': overlap,
            'outline_distance_m': distance, 'feature_local_id': ef['localId'] if ef else None,
            'near_owner_id': oo[ef['localId']] if ef else None, 'source_roof': other_key in ore['source_roof_keys'],
            'source_layer': feature['properties']['source_layer'], 'linked_parent_id': feature['properties'].get('building_id'),
            'residual': ef['residual'] if ef else None, 'source_geometry': feature['geometry'], 'retain': True})
    assert not any(f['source_layer'] == 'building_part' and f['intersection_area_m2'] > 1e-6 for f in adjacent), 'Unassociated overlapping source part needs explicit review'
    poi = evidence['location_reference']
    poi_local = Point(local(*poi['coordinates']))
    original_rings = sum(1 + len(p.interiors) for p in geographic_components)
    input_record = {'schema': 'building-v6-frozen-existing-osm-geometry-input-v1', 'id': spec['id'],
        'name_zh': spec['name_zh'], 'name_en': spec['name_en'], 'district_id': props['district_id'], 'district_name': props['district_name'],
        'geometry_source_kind': 'existing_overture_osm_footprint', 'is_osm_building_geometry': True,
        'status': 'Source footprint and exact city identity frozen; architecture and height require independent photographic evidence',
        'anchor': anchor, 'origin_longitude': anchor[0], 'origin_latitude': anchor[1],
        'anchor_method': 'Centroid of the exact existing source polygon in EPSG:3857, inverse projected; not address POI, image crop or bounding-box center.',
        'geometry': raw['geometry'], 'geographic_bbox': list(geo.bounds),
        'model_geometry_local_east_north_m': mapping(local_geo),
        'polygon_local_east_north': [list(p) for p in components[spec['front_component_index']].exterior.coords[:-1]],
        'geometry_components': len(components), 'geometry_rings': original_rings,
        'coordinate_contract': {'earth_radius_m': R, 'geographic': 'EPSG:4326', 'metre_frame': 'Existing source-builder Web Mercator difference times cos(anchor latitude)',
            'gltf_xyz': '[east_m, elevation_m, -north_m]', 'original_source_vertex_order_and_all_rings_preserved': True,
            'geometry_exactly_equals_existing_source': True, 'no_image_retracing_or_bbox_substitution': True,
            'runtime_radius_note': 'Retains R6378137 source-builder convention; no silent change to existing MapLibre radius convention.'},
        'front_edge': front, 'streetfront': {'primary_edge_index': front['edge_index'], 'primary_component_index': front['component_index'],
            'candidate_edges': all_edges, 'method': 'The current OSM building is explicitly named Fitch Memorial Church; photo title and59 doorplate agree. Source north edge3 faces the named Duolun Road; independent photographic orientation review is required before architectural calibration. Camera geotag does not set the anchor.',
            'frontage_uncertainty': 'Mapped outline may follow roof edges rather than surveyed wall feet; the original mapper tracing method is not established here. Mapped front width is an approximate source scale.'},
        'facade_frame': {'origin_local_east_north_m': front['center_local_east_north_m'], 'u_east_north': front['tangent_east_north'],
            'inward_v_east_north': [-v for v in front['outward_normal_east_north']], 'front_width_m': front['length_m'],
            'photographic_left_to_right_native_u_sign': spec.get('photographic_front_u_sign'),
            'photographic_axis_note': spec.get('photographic_axis_note'),
            'conversion': 'localENU = facade_origin + u*s + inward_v*depth; glTF=[east,height,-north]. Source winding is preserved; do not assume u is photo-left-to-right until viewing direction is checked.'},
        'source': {'release': raw_manifest['release'], 'key': key, 'overture_id': props['id'], 'owner_macro_id': macro,
            'owner_tile': list(map(int, macro.split('-'))), 'provider_records': props['sources'], 'properties': props,
            'source_geometry': raw['geometry'], 'frozen_raw_feature': raw, 'raw_feature_canonical_sha256': object_sha(raw),
            'raw_macro_source_file': sources['raw:' + macro], 'is_osm_geometry': True, 'osm_source_comparison': osm_comparison, 'osm_way_evidence': osm_evidence},
        'identity_evidence': {'frozen_research_proposal': evidence, 'address_identity_record': official, 'location_context': context_record,
            'photo_geotag_used_as_anchor': False, 'photo_geotag_inside_footprint': local_geo.covers(poi_local), 'photo_geotag_to_outline_distance_m': local_geo.boundary.distance(poi_local),
            'geotag_warning': 'Photograph geotag is approximate and may locate the camera on the road. It is neither a measured building coordinate nor an address POI.',
            'scope': spec['identity_scope']},
        'current_city_detail': {'configuration_sha256': CONFIG, 'complete_city_macro_count':1708, 'complete_city_feature_count':1796419,
            'owner_macro_id':macro, 'feature_local_id':effective['localId'], 'feature_id_base':1, 'near_owner_id':near['id'],
            'far_file':city_index[macro]['file'], 'near_file':str(Path(city_index[macro]['near_manifest_file']).parent / near['file']),
            'near_asset_sha256':near['sha256'], 'near_asset_size_bytes':near['size_bytes'], 'near_feature_local_ids':near['featureLocalIds'],
            'original_macro_origin':table['origin'], 'frozen_effective_feature':effective,
            'feature_table_source_file':sources['table:'+macro], 'ready_source_file':sources['ready:'+macro], 'ownership_source_file':sources['ownership:'+macro],
            'same_near_neighbors_to_retain':[{'key':f['key'],'feature_local_id':f['localId'],'residual':f['residual'],'source_roof':f['key'] in ready['source_roof_keys'],'geometry':f['geometry']} for f in siblings]},
        'existing_height': {'base_m':effective['base'], 'height_m':effective['height'], 'height_quality':effective['height_quality'],
            'height_provenance':effective['height_provenance'], 'height_is_measured':False,
            'note':'Existing city height and its provenance are retained as source baseline only. A raster-cell or floor estimate is not a measured height of this building and is never imposed on photographic calibration.'},
        'parts':[], 'parts_audit':{'source_has_parts':props['has_parts'], 'linked_source_parts':len(linked_parts), 'raw_linked_parts':len(linked_parts), 'related_residuals':len(linked_residuals),
            'overlapping_unassociated_parts':0, 'scanned_raw_macros':[x['macro_id'] for x in scanned],
            'scope':'Existing parent flag, linked parts in owner+8neighbor macro halo and overlapping parts; no claim of real-world absence of roof/parcel subdivisions.'},
        'replacement':{'building_ids':[props['id']], 'building_part_ids':[], 'feature_local_ids':[effective['localId']],
            'retained_same_near_feature_local_ids':[f['localId'] for f in siblings], 'only_exact_ids':True,
            'do_not_delete_nearby_buildings_by_radius':True, 'adjacent_or_overlapping_source_features':adjacent,
            'target_is_qualified_source_roof':False, 'macro_source_roof_count_unchanged':len(ready['source_roof_keys']),
            'macro_residual_count_unchanged':ready['residual_count'], 'applied':False,
            'mask_contract':'Mask only the target local ID in far; omit only the exact source key in regenerated near geometry. Never remove its entire shared microtile or nearby buildings.'},
        'license':{'overture_aggregate':'ODbL-1.0','underlying_source':spec['underlying_dataset_license']},
        'attribution':'© Overture Maps Foundation; underlying footprint: ' + spec['underlying_dataset_license']['attribution'] + ', ' + spec['underlying_dataset_license']['id'] + '; address/context OSM: © OpenStreetMap contributors, ODbL-1.0',
        'limitations':['Existing simplified OSM/MVT rectangle is not cadastral or laser measured; it does not individually trace the tower, wing recesses, projecting eaves or wall feet.','No hidden rear opening/parcel ownership or roof height is established by this freeze.','OSM names this actual source building; the59 address is photographically visible but is not a surveyed cadastral polygon.']}
    write(out / 'geometry-input.json', input_record)
    report = {'schema':'building-v6-existing-osm-mapping-report-v1', 'passed':True, 'id':spec['id'],
        'geometry_file':'geometry-input.json','geometry_sha256':sha(out/'geometry-input.json'),
        'source_files':sources,'raw_tiles_scanned':scanned,'raw_features_scanned':len(features),'current_tables_read':sorted(tables),
        'source_key':key,'owner_macro_id':macro,'local_id':effective['localId'],'near_owner_id':near['id'],
        'near_target_ids':[effective['localId']],'near_retained_ids':[f['localId'] for f in siblings],
        'front_edge':front,'area_m2':local_geo.area,'no_osm_building_identity_fabricated':True,
        'geometry_and_properties_equal_raw':True,'no_target_parts_residual_or_roof_override':True,
        'source_photo_and_model_mutations':False,'network_or_sqlite_used':False,
        'osm_source_comparison':osm_comparison, 'script':{'file':'freeze_existing_osm_feature.py','sha256':sha(Path(__file__))}}
    write(out / 'mapping-report.json', report)
    print(json.dumps({k:report[k] for k in ['passed','source_key','owner_macro_id','local_id','near_owner_id','geometry_sha256']},indent=2))


if __name__ == '__main__':
    main()
