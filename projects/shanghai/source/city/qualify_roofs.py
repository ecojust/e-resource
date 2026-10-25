#!/usr/bin/env python3
"""Conservatively qualify cached Overture roofs against exact historical OSM tags.

No model is modified. Requires shapely and the project's build_district_models
module (numpy/mapbox_earcut). OSM requests are bounded to two concurrent workers.
Historical way tags validate parameters, not historical node coordinates.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

from shapely.geometry import Polygon, shape

SCHEMA = 'shanghai-qualified-roofs-v1'
POLICY = {
    'accepted_shapes': ['gabled', 'skillion'],
    'height_semantics': 'OSM height is absolute top above ground; eave=height-roof_height; base=max(0,min_height)',
    'height_arithmetic': 'Require roof_height <= height-base without epsilon inflation; preserve all numeric source values. Negative source min_height would clamp base to zero; no accepted record has a negative min_height.',
    'minimum_area_m2': 1.0,
    'minimum_span_m': 0.25,
    'gabled_minimum_aspect_ratio': 1.20,
    'gabled_minimum_rectangularity': 0.95,
    'gabled_minimum_convexity': 0.98,
    'gabled_maximum_edge_axis_error_degrees': 8.0,
    'numeric_height_tolerance_m': 0.0001,
    'numeric_direction_tolerance_degrees': 0.0001,
    'geometry': 'Keep exact cached polygon; no repairs, clipping, simplification, holes, multipart geometry, or MRR substitution.',
    'direction': 'Use exact-version OSM roof:direction downslope bearing; East/South unit=[sin(theta),-cos(theta)].',
    'orientation': 'Explicit exact-version OSM along/across only; along ridge follows long MRR axis, across follows short MRR axis.',
    'has_parts_parent': 'Reject whole parents with parts, including restored residual parents.',
    'historical_geometry_limit': 'Historical way tags are checked. Way node IDs alone do not verify historical node coordinates; footprints remain the cached Overture geometry.',
    'maximum_network_concurrency': 2,
}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(float(value)) else None


def tag_number(value, allow_metre_suffix=True):
    if not isinstance(value, str):
        return None
    suffix = r'(?:m)?' if allow_metre_suffix else ''
    match = re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*' + suffix + r'\s*', value)
    return float(match.group(1)) if match else None


def angle_delta(a, b):
    return abs((a - b + 180) % 360 - 180)


def load_projection(project):
    path = project / 'source/city/build_district_models.py'
    spec = importlib.util.spec_from_file_location('roof_qualification_project_coordinates', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.local_coordinates, path


def footprint_metrics(geometry, local_coordinates):
    if geometry.get('type') != 'Polygon' or len(geometry.get('coordinates', [])) != 1:
        return None, ['not_single_polygon_without_holes']
    ring = geometry['coordinates'][0]
    if len(ring) < 4 or ring[0] != ring[-1]:
        return None, ['unclosed_or_short_ring']
    if any(len(p) < 2 or number(p[0]) is None or number(p[1]) is None for p in ring):
        return None, ['nonfinite_coordinates']
    geographic = shape(geometry)
    if not geographic.is_valid or geographic.is_empty:
        return None, ['invalid_original_polygon']
    center = geographic.centroid
    origin = [center.x, center.y]
    # Keep coordinates close to zero: large absolute projected coordinates make
    # minimum_rotated_rectangle unstable for very thin footprints.
    local_ring = [local_coordinates(p[0], p[1], origin) for p in ring]
    poly = Polygon(local_ring)
    if not poly.is_valid or poly.area <= 0:
        return None, ['invalid_local_polygon']
    rect = poly.minimum_rotated_rectangle
    if not isinstance(rect, Polygon) or rect.area <= 0:
        return None, ['degenerate_rectangle']
    corners = list(rect.exterior.coords)
    edges = [(corners[i+1][0]-corners[i][0], corners[i+1][1]-corners[i][1]) for i in range(4)]
    lengths = [math.hypot(*e) for e in edges]
    idx = max(range(4), key=lambda i: lengths[i])
    long_span, short_span = lengths[idx], min(lengths)
    axis = [edges[idx][0]/long_span, edges[idx][1]/long_span]
    if axis[0] < -1e-12 or (abs(axis[0]) <= 1e-12 and axis[1] < 0):
        axis = [-v for v in axis]
    perpendicular = [-axis[1], axis[0]]
    axis_errors = []
    for a, b in zip(local_ring, local_ring[1:]):
        dx, dz = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dz)
        if length > 1e-6:
            dot = min(1.0, max(abs((dx*axis[0]+dz*axis[1])/length), abs((dx*perpendicular[0]+dz*perpendicular[1])/length)))
            axis_errors.append(math.degrees(math.acos(dot)))
    result = {
        'origin': origin, 'area_m2': poly.area, 'mrr_area_m2': rect.area,
        'rectangularity': poly.area/rect.area,
        'convexity': poly.area/poly.convex_hull.area,
        'long_span_m': long_span, 'short_span_m': short_span,
        'aspect_ratio': long_span/short_span,
        'maximum_edge_axis_error_degrees': max(axis_errors, default=0),
        'long_axis_xz': axis, 'short_axis_xz': perpendicular,
    }
    reasons = []
    if result['area_m2'] < POLICY['minimum_area_m2']:
        reasons.append('footprint_below_minimum_area')
    if short_span < POLICY['minimum_span_m']:
        reasons.append('footprint_below_minimum_span')
    return result, reasons


def prepare(feature, exclusions, residuals, projection):
    p = feature['properties']
    fid = p.get('id', feature.get('id'))
    layer = p.get('source_layer')
    key = f'{layer}:{fid}'
    reasons = []
    if not p.get('renderable', False): reasons.append('source_not_renderable')
    if layer not in ('building', 'building_part'): reasons.append('unsupported_source_layer')
    if key in exclusions['keys'] or fid in exclusions['ids']:
        reasons.append('detailed_model_replacement')
    if p.get('building_id') in exclusions['building_ids']:
        reasons.append('linked_to_detailed_model_parent')
    if key in exclusions['override_keys']:
        reasons.append('partially_replaced_geometry')
    if layer == 'building' and (p.get('has_parts') or fid in residuals):
        reasons.append('whole_parent_has_parts_or_residual_geometry')
    if p.get('is_underground'): reasons.append('underground')
    roof_shape = p.get('roof_shape')
    if roof_shape not in POLICY['accepted_shapes']:
        reasons.append('hipped_report_only' if roof_shape == 'hipped' else 'unsupported_roof_shape')
    height, rh = number(p.get('height')), number(p.get('roof_height'))
    mh = number(p['min_height']) if 'min_height' in p else 0.0
    if height is None or height <= 0: reasons.append('height_not_positive_finite')
    if rh is None or rh <= 0: reasons.append('roof_height_not_positive_finite')
    if mh is None: reasons.append('min_height_not_finite')
    if height is not None and rh is not None and mh is not None and rh > height-max(0, mh):
        reasons.append('eave_below_base')
    metrics, geometry_reasons = footprint_metrics(feature.get('geometry', {}), projection)
    reasons.extend(geometry_reasons)
    orientation, direction = p.get('roof_orientation'), number(p.get('roof_direction'))
    if roof_shape == 'gabled':
        if orientation not in ('along', 'across'): reasons.append('missing_explicit_gabled_orientation')
        if metrics:
            for metric, bound, reason, is_min in [
                ('aspect_ratio', 1.2, 'ambiguous_long_axis', True),
                ('rectangularity', .95, 'gabled_not_near_rectangle', True),
                ('convexity', .98, 'gabled_not_near_convex', True),
                ('maximum_edge_axis_error_degrees', 8, 'gabled_edges_not_axis_aligned', False),
            ]:
                if (metrics[metric] < bound if is_min else metrics[metric] > bound): reasons.append(reason)
    if roof_shape == 'skillion' and (direction is None or direction < 0 or direction > 360):
        reasons.append('missing_or_invalid_numeric_skillion_direction')
    records = set()
    for source in p.get('sources', []):
        if source.get('provider') == 'osm' or source.get('dataset') == 'OpenStreetMap':
            record = source.get('record_id', '')
            if re.fullmatch(r'w\d+@\d+', record): records.add(record)
            else: reasons.append('osm_source_not_exact_way_version')
    if len(records) != 1: reasons.append('missing_or_ambiguous_osm_way_version')
    osm_record = next(iter(records)) if len(records) == 1 else None
    match = re.fullmatch(r'w(\d+)@(\d+)', osm_record or '')
    source_path = p.get('audit_source_tile', '')
    tile_match = re.fullmatch(r'data/fullcity-raw/tiles/(\d+)/(\d+)/(\d+)\.geojson\.gz', source_path)
    if not tile_match: reasons.append('invalid_source_tile_path')
    tile = [int(v) for v in tile_match.groups()] if tile_match else None
    result = {
        'key': key, 'id': fid, 'source_layer': layer,
        'building_id': p.get('building_id'), 'district_id': p.get('district_id'),
        'district_name': p.get('district_name'), 'tile': tile, 'owner_tile': tile,
        'cell_id': '-'.join(map(str, tile)) if tile else None,
        'source_tile': source_path, 'source_relative_path': source_path,
        'geometry': feature.get('geometry'), 'original_properties': p,
        'roof_shape': roof_shape, 'height': height, 'roof_height': rh,
        'min_height': mh, 'base': max(0, mh) if mh is not None else None,
        'eave_height': height-rh if height is not None and rh is not None else None,
        'roof_orientation': orientation, 'roof_direction': direction,
        'footprint_metrics': metrics,
        'osm': {'way_id': int(match[1]), 'version': int(match[2]), 'record_id': osm_record} if match else None,
    }
    return result, sorted(set(reasons))


def get_evidence(identity, evidence_dir, offline):
    way_id, version = identity
    path = evidence_dir / f'osm-way-{way_id}-v{version}.json'
    url = f'https://api.openstreetmap.org/api/0.6/way/{way_id}/{version}.json'
    fetched = False
    error = None
    if not path.exists() and not offline:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'ShanghaiOpenModelRoofAudit/1.0 (public historical OSM tag verification)', 'Accept': 'application/json'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    payload = response.read()
                decoded = json.loads(payload)
                if not isinstance(decoded.get('elements'), list): raise ValueError('response has no elements array')
                temporary = path.with_suffix('.tmp')
                temporary.write_bytes(payload)
                temporary.replace(path)
                fetched = True
                break
            except Exception as exc:
                error = str(exc)
                if attempt < 2: time.sleep(0.7 * (attempt+1))
    if not path.exists():
        return identity, {'ok': False, 'url': url, 'error': error or 'evidence absent in offline mode'}
    try:
        data = json.loads(path.read_text())
        elements = [e for e in data.get('elements', []) if e.get('type') == 'way' and e.get('id') == way_id and e.get('version') == version]
        if len(elements) != 1: raise ValueError('exact type/id/version not present exactly once')
        return identity, {'ok': True, 'url': url, 'evidence_file': path.name, 'sha256': sha(path), 'fetched': fetched, 'element': elements[0]}
    except Exception as exc:
        return identity, {'ok': False, 'url': url, 'error': str(exc)}


def verify_osm(record, evidence):
    if not evidence['ok']: return ['exact_osm_version_unavailable']
    tags = evidence['element'].get('tags', {})
    reasons = []
    if tags.get('roof:shape') != record['roof_shape']: reasons.append('osm_roof_shape_mismatch')
    verified = {'roof:shape': tags.get('roof:shape')}
    for osm_key, source_key in [('height', 'height'), ('roof:height', 'roof_height')]:
        value = tag_number(tags.get(osm_key))
        if value is None: reasons.append(f'osm_{osm_key.replace(":", "_")}_missing_or_ambiguous')
        elif abs(value-record[source_key]) > POLICY['numeric_height_tolerance_m']:
            reasons.append(f'osm_{osm_key.replace(":", "_")}_mismatch')
        else: verified[osm_key] = value
    value = tag_number(tags.get('min_height')) if 'min_height' in tags else 0.0
    if value is None or abs(value-record['min_height']) > POLICY['numeric_height_tolerance_m']:
        reasons.append('osm_min_height_mismatch_or_ambiguous')
    else: verified['min_height'] = value
    if record['roof_shape'] == 'gabled':
        if tags.get('roof:orientation') != record['roof_orientation']:
            reasons.append('osm_roof_orientation_mismatch_or_missing')
        else: verified['roof:orientation'] = tags['roof:orientation']
        if 'roof:direction' in tags or 'roof_direction' in record['original_properties']:
            # Multiple ways to specify a ridge can contradict. This bounded
            # patch declines both-defined cases instead of guessing priority.
            reasons.append('gabled_direction_and_orientation_both_specified')
    if record['roof_shape'] == 'skillion':
        value = tag_number(tags.get('roof:direction'), allow_metre_suffix=False)
        if value is None or not 0 <= value <= 360:
            reasons.append('osm_skillion_direction_missing_or_ambiguous')
        elif angle_delta(value, record['roof_direction']) > POLICY['numeric_direction_tolerance_degrees']:
            reasons.append('osm_skillion_direction_mismatch')
        else:
            verified['roof:direction'] = value
            record['roof_direction'] = value % 360
        if 'roof:orientation' in tags or record.get('roof_orientation') is not None:
            reasons.append('skillion_direction_with_ambiguous_orientation')
    nodes = evidence['element'].get('nodes', [])
    if len(nodes) < 4 or nodes[0] != nodes[-1]:
        reasons.append('historical_osm_way_not_closed')
    record['osm'].update({k: evidence[k] for k in ('url', 'evidence_file', 'sha256')})
    record['osm'].update({'tags': tags, 'verified_parameters': verified, 'timestamp': evidence['element'].get('timestamp'), 'geometry_validation': 'closed historical node sequence; node coordinates not validated'})
    return reasons


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    inferred_project = Path(__file__).resolve().parents[2]
    ap.add_argument('--project', type=Path, default=inferred_project)
    ap.add_argument('--input', type=Path, help='Defaults to PROJECT/data/roofs/cached-roof-candidates.geojson')
    ap.add_argument('--output', type=Path, help='Defaults to PROJECT/data/roofs/qualified-roofs.json')
    ap.add_argument('--evidence', type=Path, help='Defaults to output sibling source-evidence')
    ap.add_argument('--offline', action='store_true', help='Use cached exact-version evidence; reject missing responses')
    args = ap.parse_args()
    project = args.project.resolve()
    input_path = (args.input or project/'data/roofs/cached-roof-candidates.geojson').resolve()
    output = (args.output or project/'data/roofs/qualified-roofs.json').resolve()
    evidence_dir = (args.evidence or output.parent/'source-evidence').resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    projection, projection_file = load_projection(project)
    exclusion_path = project/'data/landmark-exclusions.json'
    residual_path = project/'data/parent-residual-overrides.json'
    ex = json.loads(exclusion_path.read_text())
    exclusions = {'building_ids': set(ex.get('building_ids', [])), 'ids': set(ex.get('building_ids', [])+ex.get('building_part_ids', [])), 'keys': set(ex.get('excluded_keys', [])), 'override_keys': set(ex.get('geometry_overrides', {}))}
    residuals = set(json.loads(residual_path.read_text()).get('parent_geometry_overrides', {})) if residual_path.exists() else set()
    features = json.loads(input_path.read_text())['features']
    pending, skipped, allrecords = [], [], []
    for feature in features:
        record, reasons = prepare(feature, exclusions, residuals, projection)
        allrecords.append(record)
        if reasons:
            skipped.append({'key': record['key'], 'id': record['id'], 'roof_shape': record['roof_shape'], 'district_id': record['district_id'], 'owner_tile': record['owner_tile'], 'reasons': reasons})
        else: pending.append(record)
    identities = sorted({(r['osm']['way_id'], r['osm']['version']) for r in pending})
    preflight = {'input_count': len(features), 'prefilter_eligible': len(pending), 'eligible_by_shape': dict(Counter(r['roof_shape'] for r in pending)), 'unique_osm_way_versions': len(identities), 'eligible_roof_only_eave_equals_base': sum(abs(r['eave_height']-r['base']) < 1e-7 for r in pending), 'eligible_nonzero_min_height': sum(r['min_height'] != 0 for r in pending)}
    write_json(output.parent/'qualification-preflight.json', preflight)
    print(json.dumps(preflight), flush=True)
    fetched = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(get_evidence, identity, evidence_dir, args.offline) for identity in identities]
        for index, future in enumerate(as_completed(futures), 1):
            identity, result = future.result()
            fetched[identity] = result
            if index % 20 == 0 or index == len(futures): print(f'OSM evidence {index}/{len(futures)}', flush=True)
    # Read each source tile once; verify cache candidates against immutable raw
    # records and copy the exact origin used by the full-city model pipeline.
    tile_paths = sorted({r['source_tile'] for r in pending})
    tile_cache = {}
    for relative in tile_paths:
        path = project/relative
        with gzip.open(path, 'rt') as f: data = json.load(f)
        indexed = {f"{f['properties'].get('source_layer')}:{f['properties'].get('id', f.get('id'))}": f for f in data['features']}
        tile_cache[relative] = {'metadata': data['metadata'], 'sha256': sha(path), 'records': indexed}
    accepted = []
    for record in pending:
        ev = fetched[(record['osm']['way_id'], record['osm']['version'])]
        reasons = verify_osm(record, ev)
        source = tile_cache[record['source_tile']]
        original = source['records'].get(record['key'])
        if original is None: reasons.append('original_source_record_missing')
        elif original['geometry'] != record['geometry']: reasons.append('original_source_geometry_mismatch')
        if original is not None:
            candidate_properties = {k: v for k, v in record['original_properties'].items() if k != 'audit_source_tile'}
            if candidate_properties != original['properties']:
                reasons.append('original_source_properties_mismatch')
            # Keep original_properties byte-for-byte equivalent at the JSON
            # value level; the cached audit path is not a source attribute.
            record['original_properties'] = original['properties']
        if reasons:
            skipped.append({'key': record['key'], 'id': record['id'], 'roof_shape': record['roof_shape'], 'district_id': record['district_id'], 'owner_tile': record['owner_tile'], 'osm': record['osm'], 'reasons': sorted(set(reasons))})
            continue
        record['origin'] = source['metadata']['origin']
        record['source_sha256'] = record['source_tile_sha256'] = source['sha256']
        record['source_release'] = source['metadata'].get('release')
        metrics = record['footprint_metrics']
        record['axes'] = {k: metrics[k] for k in ('long_axis_xz', 'short_axis_xz')}
        if record['roof_shape'] == 'gabled':
            ridge = metrics['long_axis_xz'] if record['roof_orientation'] == 'along' else metrics['short_axis_xz']
            record['axes']['ridge_axis_xz'] = record['ridge_unit'] = ridge
            record['assumptions'] = ['Symmetric two-plane gable; centered ridge; no unsupported roof overhang or dormer detail.', 'Footprint is original cached Overture polygon, not replacement MRR.']
        else:
            theta = math.radians(record['roof_direction'])
            downslope = [math.sin(theta), -math.cos(theta)]
            record['axes']['downslope_axis_xz'] = record['down_slope_unit'] = downslope
            record['direction_interpretation'] = 'verified-osm-downslope-bearing'
            record['assumptions'] = ['Single planar skillion interpolated between exact footprint projection extrema; no unsupported overhang.', 'Footprint is original cached Overture polygon, not reconstructed historical OSM nodes.']
        record['roof_only'] = abs(record['eave_height']-record['base']) < 1e-7
        accepted.append(record)
    accepted.sort(key=lambda r: (r['owner_tile'], r['key']))
    skipped.sort(key=lambda r: r['key'])
    if len(accepted)+len(skipped) != len(features): raise RuntimeError('classification accounting mismatch')
    if len({r['key'] for r in accepted}) != len(accepted): raise RuntimeError('accepted ID collision')
    counts = {
        **preflight, 'qualified': len(accepted), 'skipped': len(skipped),
        'qualified_by_shape': dict(Counter(r['roof_shape'] for r in accepted)),
        'qualified_by_district': dict(Counter(r['district_id'] for r in accepted)),
        'qualified_owner_tiles': len({tuple(r['owner_tile']) for r in accepted}),
        'qualified_roof_only_eave_equals_base': sum(r['roof_only'] for r in accepted),
        'qualified_height_equals_roof_height': sum(r['height'] == r['roof_height'] for r in accepted),
        'qualified_nonzero_min_height': sum(r['min_height'] != 0 for r in accepted),
        'skipped_reason_occurrences': dict(Counter(reason for r in skipped for reason in r['reasons'])),
        'evidence_failed': sum(not e['ok'] for e in fetched.values()),
    }
    evidence_log = [{'way_id': identity[0], 'version': identity[1], **{k:v for k,v in e.items() if k != 'element'}} for identity,e in sorted(fetched.items())]
    write_json(evidence_dir/'qualification-fetch-log.json', evidence_log)
    output_data = {
        'schema_version': SCHEMA, 'complete': True,
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'coordinate_system': 'X east, Y up, Z south; metres; project local Mercator times cos(origin latitude)',
        'input': {'filename': input_path.name, 'sha256': sha(input_path), 'feature_count': len(features)},
        'raw_manifest': {'file': 'data/fullcity-raw/manifest.json', 'sha256': sha(project/'data/fullcity-raw/manifest.json')},
        'evidence_directory': 'source-evidence',
        'qualifier_script_sha256': sha(Path(__file__)),
        'coordinate_function': {'file': 'source/city/build_district_models.py', 'function': 'local_coordinates', 'sha256': sha(projection_file)},
        'exclusions': {'file':'data/landmark-exclusions.json', 'sha256':sha(exclusion_path), 'building_ids':len(exclusions['building_ids']), 'all_ids':len(exclusions['ids']), 'linked_parts_excluded':True, 'parent_residual_file':'data/parent-residual-overrides.json', 'parent_residual_sha256':sha(residual_path) if residual_path.exists() else None},
        'policy': POLICY, 'counts': counts, 'roofs': accepted,
        'attribution': {'footprints':'Overture Maps buildings, release 2026-10-21.0; cached OSM-derived candidates', 'source_tags':'© OpenStreetMap contributors', 'license':'ODbL-1.0', 'license_url':'https://opendatacommons.org/licenses/odbl/1-0/', 'evidence':'Exact historical OSM way responses; validation does not prove surveyed geometry or roof shape.'},
    }
    write_json(output, output_data)
    write_json(output.parent/'skipped-roofs.json', {'schema_version':SCHEMA, 'input_sha256':sha(input_path), 'counts':counts, 'skipped':skipped, 'hipped_report':{'count':sum(r['roof_shape']=='hipped' for r in allrecords), 'positive_valid_height_count':sum(r['roof_shape']=='hipped' and r['height'] is not None and r['roof_height'] is not None and r['height']>0 and r['roof_height']>0 and r['base'] is not None and r['eave_height']>=r['base'] for r in allrecords), 'applied':False, 'reason':'Hip topology and ridge endpoints require a separate qualification contract.'}})
    print(json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
