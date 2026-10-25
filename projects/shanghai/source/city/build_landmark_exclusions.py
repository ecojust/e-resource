#!/usr/bin/env python3
"""Audit exact Overture IDs replaced by the five detailed landmark models.

No radius or proximity-based deletion. Main buildings match an exact OSM way
record; child parts match Overture's explicit building_id relationship.

Defaults resolve from the installed project, independent of the current working
directory. Rebuilds read the published raw gzip snapshot and bundled OSM audit
files, without downloading data or requiring a private SQLite database.
"""
import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, Polygon, mapping, shape
from shapely.ops import transform

DEFAULT_PROJECT = Path(__file__).resolve().parents[2]
TRANSFORM = Transformer.from_crs(4326, 32651, always_xy=True).transform
LANDMARKS = [
    ('shanghai-tower', '上海中心大厦', '165792123', 121.5012667, 31.2356172),
    ('oriental-pearl', '东方明珠', '40778038', 121.4951673, 31.2419382),
    ('swfc', '上海环球金融中心', '10691100', 121.5030405, 31.2365768),
    ('jin-mao', '金茂大厦', '376075961', 121.5014197, 31.2372502),
    ('customs-house', '上海海关临江前楼', '178407318', 121.4854354265109, 31.238615036350964),
]


def read(path):
    return json.loads(path.read_text())


def source_records(feature):
    return [source['record_id'] for source in feature['properties'].get('sources', [])
            if source.get('record_id')]


def osm_polygon(way_id, customs, audit):
    if way_id == '178407318':
        return next(shape(f['geometry']) for f in customs
                    if str(f['properties']['id']) == way_id)
    elements = read(audit / 'landmark-osm' / f'{way_id}.json')['elements']
    nodes = {n['id']: (n['lon'], n['lat']) for n in elements if n['type'] == 'node'}
    way = next(e for e in elements if e['type'] == 'way' and str(e['id']) == way_id)
    return Polygon([nodes[node] for node in way['nodes']])


def metric(feature, reference, anchor, reason):
    geometry = shape(feature['geometry'])
    projected = transform(TRANSFORM, geometry)
    ref = transform(TRANSFORM, reference)
    overlap = projected.intersection(ref).area
    union = projected.union(ref).area
    props = feature['properties']
    return {
        'id': props['id'], 'source_layer': props['source_layer'],
        'building_id': props.get('building_id'), 'reason': reason,
        'source_record_ids': source_records(feature),
        'source_renderable': props.get('renderable', True),
        'area_m2': round(projected.area, 3),
        'overlap_m2': round(overlap, 3),
        'iou': round(overlap / union, 8) if union else 0,
        'source_fraction_covered': round(overlap / projected.area, 8) if projected.area else 0,
        'anchor_inside': geometry.covers(Point(anchor)),
        'height': props.get('height'), 'min_height': props.get('min_height'),
        'source_geometry': feature['geometry'],
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--project', type=Path, default=DEFAULT_PROJECT,
                        help='Project root containing data/audit and data/fullcity-raw')
    parser.add_argument('--raw', type=Path,
                        help='Raw snapshot directory (default: PROJECT/data/fullcity-raw)')
    parser.add_argument('--output', type=Path,
                        help='Output JSON (default: PROJECT/data/landmark-exclusions.json)')
    parser.add_argument('--audit', type=Path,
                        help='Audit input directory (default: PROJECT/data/audit)')
    args = parser.parse_args()
    args.project = args.project.resolve()
    args.raw = (args.raw or args.project / 'data' / 'fullcity-raw').resolve()
    args.output = (args.output or args.project / 'data' / 'landmark-exclusions.json').resolve()
    args.audit = (args.audit or args.project / 'data' / 'audit').resolve()
    return args


def scan_related_parts(raw_dir, raw_manifest, parent_ids):
    """Read every published tile and verify counts before claiming full closure."""
    if not raw_manifest.get('complete'):
        raise ValueError('A complete raw snapshot is required for landmark relationship verification.')
    tiles = raw_manifest['tiles']
    if len(tiles) != raw_manifest['output_tile_count']:
        raise ValueError('Raw manifest tile count mismatch.')
    parts = []
    scanned = 0
    for index, tile in enumerate(tiles, 1):
        path = raw_dir / tile['file']
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            collection = json.load(stream)
        features = collection['features']
        if len(features) != tile['feature_count'] or not collection['metadata'].get('complete'):
            raise ValueError(f'Incomplete raw tile: {path}')
        scanned += len(features)
        parts.extend(feature for feature in features
                     if feature['properties'].get('source_layer') == 'building_part'
                     and feature['properties'].get('building_id') in parent_ids)
        if index % 250 == 0 or index == len(tiles):
            print(f'Scanned {index}/{len(tiles)} raw tiles; {scanned:,} features; '
                  f'{len(parts)} related parts.', flush=True)
    if scanned != raw_manifest['unique_feature_count']:
        raise ValueError(f'Raw feature count mismatch: {scanned}')
    return parts


def main():
    args = parse_args()
    raw_manifest = read(args.raw / 'manifest.json')
    candidates = read(args.audit / 'landmark-candidate-features.geojson')['features']
    customs = read(args.audit / 'customs-osm-footprints.geojson')['features']
    parents = {}
    for landmark_id, _, way, _, _ in LANDMARKS:
        matches = [f for f in candidates if f['properties']['source_layer'] == 'building'
                   and any(record.split('@')[0] == 'w' + way for record in source_records(f))]
        assert len(matches) == 1, (landmark_id, len(matches))
        parents[landmark_id] = matches[0]

    # Scan the complete raw snapshot, not just nearby candidate tiles, to prove
    # that all parts attached to these five parents have been considered.
    parent_ids = {f['properties']['id'] for f in parents.values()}
    parts = scan_related_parts(args.raw, raw_manifest, parent_ids)

    entries = []
    excluded = []
    for landmark_id, name, way, lon, lat in LANDMARKS:
        parent = parents[landmark_id]
        uuid = parent['properties']['id']
        reference = osm_polygon(way, customs, args.audit)
        assert reference.is_valid and not reference.is_empty
        children = sorted((f for f in parts if f['properties'].get('building_id') == uuid),
                          key=lambda f: f['properties']['id'])
        matches = [metric(parent, reference, (lon, lat), 'exact_osm_way_record_id')]
        assert matches[0]['iou'] > .95, (landmark_id, matches[0]['iou'])
        matches.extend(metric(f, reference, (lon, lat), 'explicit_overture_building_id_relationship')
                       for f in children)
        excluded.extend(matches)
        retained = []
        if landmark_id == 'customs-house':
            # Independent nearby OSM buildings remain. An overlapping footprint
            # alone does not establish that the detailed front model replaces it.
            for feature in candidates:
                if feature['properties']['id'] == uuid:
                    continue
                if shape(feature['geometry']).intersects(reference):
                    record = metric(feature, reference, (lon, lat),
                                    'retained_no_explicit_parent_relationship')
                    if record['overlap_m2'] > 1:
                        retained.append(record)
        entries.append({
            'landmark_id': landmark_id, 'name': name, 'anchor': [lon, lat],
            'osm_way': way, 'osm_url': f'https://www.openstreetmap.org/way/{way}',
            'osm_geometry_url': f'https://api.openstreetmap.org/api/0.6/way/{way}/full.json',
            'building_ids': [uuid],
            'building_part_ids': [f['properties']['id'] for f in children],
            'source_geometry': mapping(reference),
            'confirmed_boundary': mapping(reference),
            'replacement_scope': ('Front building only; no western rear wing or neighboring buildings.'
                                  if landmark_id == 'customs-house' else
                                  'Exact OSM main building and all explicit Overture child parts.'),
            'matches': matches,
            'retained_uncertain': retained,
        })

    ids = [match['source_layer'] + ':' + match['id'] for match in excluded]
    assert len(ids) == len(set(ids))
    renderable = sum(match['source_renderable'] for match in excluded)
    config = {
        'schema_version': 1,
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'release': raw_manifest['release'],
        'crs': 'EPSG:4326', 'area_measurement_crs': 'EPSG:32651',
        'building_ids': sorted(parent_ids),
        'building_part_ids': sorted(f['properties']['id'] for f in parts),
        'excluded_keys': sorted(ids),
        'geometry_overrides': {},
        'landmark_sources': entries,
        'counts': {
            'building_ids': len(parent_ids), 'building_part_ids': len(parts),
            'excluded_ids': len(ids), 'source_renderable_replaced': renderable,
            'source_nonrenderable_parent_ids': len(ids) - renderable,
            'retained_uncertain': sum(len(e['retained_uncertain']) for e in entries),
            'geometry_overrides': 0,
        },
        'validation': {
            'complete_city_parts_relationship_scan': True,
            'exact_osm_parent_matches': True,
            'minimum_parent_iou': min(e['matches'][0]['iou'] for e in entries),
            'radius_deletion_used': False,
            'raw_geometries_modified': False,
            'all_unlisted_ids_retained': True,
            'raw_unique_feature_count': raw_manifest['unique_feature_count'],
            'raw_renderable_feature_count': raw_manifest['renderable_feature_count'],
            'raw_manifest_sha256': hashlib.sha256((args.raw / 'manifest.json').read_bytes()).hexdigest(),
        },
        'consumer_contract': {
            'building_ids': 'Hide these building IDs online and omit their generic mesh if renderable.',
            'building_part_ids': 'Hide these building_part IDs online and omit their generic mesh.',
            'sidecars': 'Keep all excluded IDs in tile sidecars for online feature hiding and audit.',
            'geometry_overrides': 'Optional layer:UUID -> replacement GeoJSON geometry; no full exclusion for an override-only ID.',
            'counts': 'Balance source renderable count as emitted + fully replaced + explicitly rejected.',
        },
        'attribution': '© OpenStreetMap contributors; Overture Maps Foundation, buildings release 2026-10-21.0, ODbL 1.0.',
        'caveats': [
            'Small geometry differences reflect PMTiles coordinate quantization and OSM snapshot dates.',
            'Parts may project outside the ground footprint; explicit building_id provides the exclusion relationship.',
            'Five small overlapping Customs House features without explicit parent relationships remain until independently confirmed.',
        ],
    }
    target = args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(config, ensure_ascii=False, separators=(',', ':')) + '\n')
    temporary.replace(target)
    print(json.dumps({'path': str(target), 'bytes': target.stat().st_size,
                      'counts': config['counts'],
                      'parents': [{'landmark': e['landmark_id'], 'iou': e['matches'][0]['iou'],
                                   'parts': len(e['building_part_ids'])} for e in entries]},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
