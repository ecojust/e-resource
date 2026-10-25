#!/usr/bin/env python3
"""Recover uncovered parent footprints without altering the original raw archive.

For each suppressed building parent, subtract the union of ALL explicit child
parts. Preserve polygon holes. Landmark replacements remain excluded. Parent
height is audit metadata only: it may describe the tallest tower, not the podium.

Default inputs are project-relative and offline. --sqlite is an optional fast
path for developers who still have the extraction cache.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3

from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import mapping, shape
from shapely.ops import transform, unary_union

PROJECT = Path(__file__).resolve().parents[2]
TO_METERS = Transformer.from_crs(4326, 32651, always_xy=True).transform


def area(geometry):
    return transform(TO_METERS, geometry).area


def polygons(geometry):
    if geometry.geom_type == 'Polygon':
        return [geometry] if not geometry.is_empty else []
    if hasattr(geometry, 'geoms'):
        return [part for child in geometry.geoms for part in polygons(child)]
    return []


def read(path):
    return json.loads(path.read_text())


def load_features(raw, manifest, sqlite_path=None):
    parents, children, scanned = {}, defaultdict(list), 0
    if sqlite_path:
        connection = sqlite3.connect(f'file:{sqlite_path.resolve()}?mode=ro', uri=True)
        boundary = connection.execute("SELECT value FROM state WHERE key='boundary_hash'").fetchone()
        if not boundary or boundary[0] != manifest['boundary_sha256']:
            raise ValueError('SQLite boundary does not match the raw snapshot.')
        count = connection.execute('SELECT COUNT(*) FROM assembled').fetchone()[0]
        if count != manifest['unique_feature_count']:
            raise ValueError('SQLite feature count does not match the raw snapshot.')
        features = (json.loads(row[0]) for row in connection.execute(
            "SELECT feature FROM assembled WHERE renderable=0 OR layer='building_part'"))
        for feature in features:
            props = feature['properties']
            if props['source_layer'] == 'building_part':
                children[props['building_id']].append(feature)
            elif not props.get('renderable', True):
                parents[props['id']] = feature
        connection.close()
        return parents, children, count

    for index, tile in enumerate(manifest['tiles'], 1):
        with gzip.open(raw / tile['file'], 'rt', encoding='utf-8') as stream:
            collection = json.load(stream)
        if len(collection['features']) != tile['feature_count'] or not collection['metadata'].get('complete'):
            raise ValueError(f'Incomplete raw tile: {tile["file"]}')
        for feature in collection['features']:
            scanned += 1
            props = feature['properties']
            if props['source_layer'] == 'building_part':
                children[props['building_id']].append(feature)
            elif not props.get('renderable', True):
                parents[props['id']] = feature
        if index % 250 == 0 or index == len(manifest['tiles']):
            print(f'Scanned {index}/{len(manifest["tiles"])} tiles; {scanned:,} features.', flush=True)
    if scanned != manifest['unique_feature_count']:
        raise ValueError('Raw snapshot feature count mismatch.')
    return parents, children, scanned


def height_summary(features):
    result = {}
    for name in ('height', 'min_height', 'num_floors', 'min_floor'):
        values = [float(f['properties'][name]) for f in features
                  if isinstance(f['properties'].get(name), (int, float))]
        result[name] = {'count': len(values), 'minimum': min(values) if values else None,
                        'maximum': max(values) if values else None}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--exclusions', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--sqlite', type=Path, help='Optional extraction cache; never needed for the published snapshot')
    parser.add_argument('--min-area', type=float, default=1.0, help='Minimum total residual area in square meters')
    args = parser.parse_args()
    raw = (args.raw or args.project / 'data/fullcity-raw').resolve()
    exclusions_path = (args.exclusions or args.project / 'data/landmark-exclusions.json').resolve()
    output = (args.output or args.project / 'data/parent-residual-overrides.json').resolve()
    manifest = read(raw / 'manifest.json')
    if not manifest.get('complete'):
        raise ValueError('A complete raw snapshot is required.')
    exclusions = read(exclusions_path)
    if exclusions['release'] != manifest['release']:
        raise ValueError('Landmark exclusions and raw snapshot have different releases.')
    excluded_parents = set(exclusions['building_ids'])
    parents, parts_by_parent, scanned = load_features(raw, manifest, args.sqlite)
    overrides, metadata, districts, audit = {}, {}, Counter(), []
    recovered_area = 0
    below_threshold_area = 0
    fully_covered, excluded_landmarks, trivial = 0, 0, 0
    for parent_id, feature in sorted(parents.items()):
        props = feature['properties']
        geometry = make_valid(shape(feature['geometry']))
        children = parts_by_parent.get(parent_id, [])
        if not children:
            raise ValueError(f'Suppressed parent has no child parts: {parent_id}')
        union = unary_union([make_valid(shape(f['geometry'])) for f in children])
        residual = unary_union(polygons(make_valid(geometry.difference(union))))
        parent_area = area(geometry)
        overlap_area = area(geometry.intersection(union))
        residual_area = area(residual)
        row = {
            'id': parent_id, 'name': props.get('@name'),
            'district_id': props['district_id'], 'district_name': props.get('district_name'),
            'source_layer': 'building', 'source_renderable': False,
            'parent_area_m2': round(parent_area, 4),
            'parts_overlap_area_m2': round(overlap_area, 4),
            'parts_coverage_fraction': round(overlap_area / parent_area, 8),
            'residual_area_m2': round(residual_area, 4),
            'part_ids': sorted(f['properties']['id'] for f in children),
            'parent_height': props.get('height'), 'parent_min_height': props.get('min_height'),
            'parent_num_floors': props.get('num_floors'), 'parent_min_floor': props.get('min_floor'),
            'child_height_statistics': height_summary(children),
            'source_properties': props,
            'height_policy': 'Estimate from the residual footprint only; do not inherit parent height, floors, or tower minimum height.',
            'quantization_sliver_possible': residual_area / parent_area < .01,
        }
        if parent_id in excluded_parents:
            row['status'] = 'excluded_by_detailed_landmark'
            excluded_landmarks += 1
        elif residual.is_empty or residual_area <= 1e-6:
            row['status'] = 'fully_covered_by_parts'
            fully_covered += 1
        elif residual_area <= args.min_area:
            row['status'] = 'below_minimum_residual_area'
            trivial += 1
            below_threshold_area += residual_area
        else:
            row['status'] = 'restore_parent_residual'
            overrides[parent_id] = mapping(residual)
            metadata[parent_id] = row
            districts[props['district_id']] += 1
            recovered_area += residual_area
            assert residual.intersection(union).area < 1e-14
        audit.append(row)
    result = {
        'schema_version': 1, 'generated_utc': datetime.now(timezone.utc).isoformat(),
        'release': manifest['release'], 'crs': 'EPSG:4326', 'area_crs': 'EPSG:32651',
        'method': 'Complete parent footprint minus union of all explicit building_id child footprints; holes preserved.',
        'minimum_residual_area_m2': args.min_area,
        'parent_geometry_overrides': overrides,
        'parent_metadata': metadata,
        'parent_audit': audit,
        'stats': {
            'raw_unique_feature_count': scanned,
            'raw_renderable_feature_count': manifest['renderable_feature_count'],
            'suppressed_parent_count': len(parents),
            'restored_parent_residual_count': len(overrides),
            'restored_residual_area_m2': round(recovered_area, 3),
            'excluded_landmark_parent_count': excluded_landmarks,
            'fully_covered_parent_count': fully_covered,
            'below_minimum_residual_area_count': trivial,
            'below_minimum_residual_area_m2': round(below_threshold_area, 6),
            'retained_under_one_percent_residual_count': sum(
                row['quantization_sliver_possible'] for row in metadata.values()),
            'district_restored_counts': dict(sorted(districts.items())),
            'source_part_count': sum(len(children) for children in parts_by_parent.values()),
        },
        'validation': {
            'complete_city_parts_scan': True, 'raw_archive_modified': False,
            'geometry_simplification': False, 'landmark_exclusions_take_precedence': True,
            'raw_manifest_sha256': hashlib.sha256((raw / 'manifest.json').read_bytes()).hexdigest(),
            'landmark_exclusions_sha256': hashlib.sha256(exclusions_path.read_bytes()).hexdigest(),
        },
        'small_residual_policy': {
            'threshold_m2': args.min_area,
            'scope': 'Total residual area per parent; individual small polygon components inside a retained residual remain intact.',
            'reason': 'Suppress only negligible total-area numerical/quantization leftovers; this is an explicit mesh threshold, not proof that a small footprint is absent.',
            'width_filter_used': False, 'coverage_fraction_filter_used': False,
            'geometry_simplification_used': False,
            'less_than_one_percent_flag': 'Audit flag only; it does not remove geometry.',
        },
        'consumer_contract': {
            'selection': 'For raw building renderable:false, restore this residual geometry only if UUID is in parent_geometry_overrides.',
            'geometry': 'UUID -> WGS84 GeoJSON geometry; all other suppressed parents remain suppressed.',
            'height': 'Use the residual footprint with CMAB/CNBH/GHSL/default estimation. Parent height/floors are metadata only; they can refer to the tallest tower.',
            'count_balance': 'emitted = source_renderable - detailed_landmark_replacements - rejected + restored_parent_residuals',
            'ids': 'Keep the original building UUID in sidecars to hide the online full parent footprint.',
        },
    }
    assert len(parents) == len(overrides) + excluded_landmarks + fully_covered + trivial
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
    temporary.replace(output)
    print(json.dumps({'output': str(output), 'bytes': output.stat().st_size, 'stats': result['stats']},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
