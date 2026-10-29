"""Extract name-string research leads from four already-frozen Bund MVT tiles.

No network is used. Reads working files, or existing Git objects with lazy fetch
explicitly disabled. --output is a proposal snapshot, never the live queue.
Requires opencc-python-reimplemented; all protobuf parsing uses the standard
library. Original extraction code: MIT; OSM-derived fields: ODbL-1.0.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
from opencc import OpenCC

PROJECT = 'projects/shanghai/'
MANIFEST = PROJECT + 'source/bund/street/tile-source.json'
BASELINE = PROJECT + 'data/model-todo/discovered-streets.json'
OFFICIAL = PROJECT + 'data/model-todo/official-road-leads.json'
RECONCILIATION = PROJECT + 'data/model-todo/official-road-reconciliation.json'
NAME_PRIORITY = ['name:zh-Hans', 'name:zh', 'name']


def varint(data, pos):
    value = shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        value |= (byte & 127) << shift
        if not byte & 128:
            return value, pos
        shift += 7
        if shift > 64:
            raise ValueError('Invalid protobuf varint')
    raise ValueError('Truncated protobuf varint')


def fields(data):
    pos = 0
    while pos < len(data):
        tag, pos = varint(data, pos)
        field, wire = tag >> 3, tag & 7
        if wire == 0:
            value, pos = varint(data, pos)
        elif wire == 2:
            length, pos = varint(data, pos)
            value = data[pos:pos + length]
            if len(value) != length:
                raise ValueError('Truncated length-delimited field')
            pos += length
        elif wire in (1, 5):
            length = 8 if wire == 1 else 4
            value = data[pos:pos + length]
            if len(value) != length:
                raise ValueError('Truncated fixed-width field')
            pos += length
        else:
            raise ValueError(f'Unsupported wire type {wire}')
        yield field, wire, value


def tile_value(data):
    field, _, value = next(fields(data))
    if field == 1:
        return value.decode('utf-8')
    if field == 2:
        return struct.unpack('<f', value)[0]
    if field == 3:
        return struct.unpack('<d', value)[0]
    if field in (4, 5):
        return value
    if field == 6:
        return (value >> 1) ^ -(value & 1)
    if field == 7:
        return bool(value)
    raise ValueError(f'Unknown MVT value field {field}')


def transportation_names(raw):
    if raw.startswith(b'\x1f\x8b'):
        raw = gzip.decompress(raw)
    result = []
    layer_count = 0
    for field, _, layer in fields(raw):
        if field != 3:
            continue
        keys, values, feature_data = [], [], []
        name = None
        for field, _, value in fields(layer):
            if field == 1:
                name = value.decode('utf-8')
            elif field == 2:
                feature_data.append(value)
            elif field == 3:
                keys.append(value.decode('utf-8'))
            elif field == 4:
                values.append(tile_value(value))
        if name != 'transportation_name':
            continue
        layer_count += 1
        for ordinal, feature in enumerate(feature_data):
            tags = []
            feature_id = geometry_type = None
            for field, _, value in fields(feature):
                if field == 1:
                    feature_id = value
                elif field == 2:
                    pos = 0
                    while pos < len(value):
                        tag, pos = varint(value, pos)
                        tags.append(tag)
                elif field == 3:
                    geometry_type = value
            if len(tags) % 2:
                raise ValueError('Odd MVT tag count')
            props = {keys[tags[i]]: values[tags[i + 1]] for i in range(0, len(tags), 2)}
            result.append({'feature_ordinal': ordinal, 'tile_feature_id': feature_id,
                           'geometry_type': geometry_type, 'properties': props})
    if layer_count != 1:
        raise ValueError(f'Expected one transportation_name layer, found {layer_count}')
    return result


def label_flags(name, classes):
    flags = set()
    if 'service' in classes:
        flags.add('service_or_access_label_review')
    if 'path' in classes:
        flags.add('path_or_pedestrian_label_review')
    if any('construction' in value for value in classes):
        flags.add('construction_label_review')
    if any(value in name for value in ('入口', '出口', '出入口', '停车场', '枢纽')):
        flags.add('access_or_parking_or_hub_name_review')
    if '隧道' in name or '地道' in name:
        flags.add('tunnel_or_underpass_name_review')
    if name.endswith('桥') or '步行桥' in name:
        flags.add('bridge_name_review')
    if any(value in name for value in ('广场', '会议中心', '小区', '风光带', '绿道', '水廊')):
        flags.add('plaza_area_or_greenway_name_review')
    if not re.search(r'(路|街|大道|公路|弄)$', name):
        flags.add('nonstandard_street_name_suffix_review')
    if not flags:
        flags.add('road_shaped_name_identity_unverified')
    return sorted(flags)


def extract(repo):
    inputs = []
    def read(path):
        local = repo / path
        if local.is_file():
            raw = local.read_bytes()
            mode = 'working-file'
        else:
            env = dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0')
            result = subprocess.run(['git', 'show', 'HEAD:' + path], cwd=repo,
                                    env=env, capture_output=True, check=False)
            if result.returncode:
                raise RuntimeError('Required frozen input unavailable locally; no network attempted: ' + path)
            raw = result.stdout
            mode = 'existing-git-object'
        inputs.append({'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'read_mode': mode})
        return raw
    source = json.loads(read(MANIFEST))
    baseline = json.loads(read(BASELINE))
    official = json.loads(read(OFFICIAL))
    reconciliation = json.loads(read(RECONCILIATION))
    cc = OpenCC('t2s')
    def norm(name):
        return re.sub(r'\s*[（(].*', '', cc.convert(name)).strip()
    base_index = defaultdict(list)
    for row in baseline['roads']:
        base_index[norm(row.get('name_simplified', row['name']))].append({'id': row['id'], 'name': row['name']})
    official_index = defaultdict(list)
    for row in official['records']:
        official_index[norm(row['name'])].append({'source_row_id': row['id'], 'name': row['name'],
                                                'extent': row['extent'], 'source_url': row['source_url']})
    proposal_index = defaultdict(list)
    for row in reconciliation['new_name_intake_proposals']:
        proposal_index[norm(row['name'])].append({'name': row['name'], 'source_rows': row['source_rows']})
    reviewed_index = defaultdict(list)
    for row in reconciliation['records']:
        reviewed_index[norm(row['original_name'])].append(row['source_row_id'])
    groups = defaultdict(list)
    tile_records = []
    excluded_ferry = no_selected_name = total = 0
    all_classes = Counter()
    for tile in source['tiles']:
        path = PROJECT + 'source/bund/street/' + tile['file']
        raw = read(path)
        if len(raw) != tile['bytes'] or hashlib.sha256(raw).hexdigest() != tile['sha256']:
            raise ValueError('Frozen tile hash/size differs from manifest: ' + path)
        features = transportation_names(raw)
        total += len(features)
        tile_records.append({'id': '/'.join(map(str, tile['tile'])), 'file': path, 'tile': tile['tile'],
                             'source_url': tile['url'], 'bounds_wgs84': tile['bounds'],
                             'bytes': len(raw), 'sha256': tile['sha256'], 'transportation_name_features': len(features)})
        for feature in features:
            props = feature['properties']
            all_classes[props.get('class', '')] += 1
            if props.get('class') == 'ferry':
                excluded_ferry += 1
                continue
            selected_field = next((key for key in NAME_PRIORITY if isinstance(props.get(key), str) and props[key]), None)
            if selected_field is None:
                no_selected_name += 1
                continue
            selected_name = props[selected_field]
            language_names = {key: value for key, value in props.items()
                              if key == 'name' or key.startswith('name:') or key.startswith('name_')}
            groups[selected_name].append({'tile_id': tile_records[-1]['id'],
                                          'feature_ordinal': feature['feature_ordinal'],
                                          'tile_feature_id': feature['tile_feature_id'],
                                          'geometry_type': feature['geometry_type'],
                                          'class': props.get('class'), 'subclass': props.get('subclass'),
                                          'selected_name_field': selected_field, 'name_fields': language_names})
    rows = []
    for name, occurrences in sorted(groups.items()):
        classes = sorted({o['class'] for o in occurrences if o['class'] is not None})
        subclasses = sorted({o['subclass'] for o in occurrences if o['subclass'] is not None})
        languages = defaultdict(set)
        for occurrence in occurrences:
            for field, value in occurrence['name_fields'].items():
                languages[field].add(value)
        matching = base_index.get(norm(name), [])
        flags = label_flags(name, classes)
        rows.append({'id': 'bund-label-' + hashlib.sha256(name.encode('utf-8')).hexdigest()[:16],
                     'name': name, 'name_simplified': cc.convert(name), 'districts': [],
                     'grouping': 'Exact selected name string only; not physical-road deduplication',
                     'occurrence_count': len(occurrences), 'tile_ids': sorted({o['tile_id'] for o in occurrences}),
                     'classes': classes, 'subclasses': subclasses,
                     'subclass_missing_occurrences': sum(o['subclass'] is None for o in occurrences),
                     'name_language_fields': {key: sorted(values) for key, values in sorted(languages.items())},
                     'occurrences': occurrences, 'label_review_flags': flags,
                     'baseline_name_match': 'existing_name_string' if matching else 'not_in_baseline_name_strings',
                     'matched_existing_road_ids': [x['id'] for x in matching],
                     'matched_existing_road_names': [x['name'] for x in matching],
                     'official_original_name_matches': official_index.get(norm(name), []),
                     'reconciliation_original_row_ids': reviewed_index.get(norm(name), []),
                     'reconciliation_proposed_name_matches': proposal_index.get(norm(name), []),
                     'identity_status': 'name_match_only_not_physical_identity',
                     'status': 'pending_label_type_alias_and_scope_review',
                     'todo': '核对标签是道路、桥隧、服务通道、出入口、步道或场所名称；核对别名、实体与范围后再查沿线建筑资料。',
                     'building_reference_ready': False, 'may_increment_physical_road_count': False})
    matched = sum(bool(r['matched_existing_road_ids']) for r in rows)
    assert len({r['id'] for r in rows}) == len(rows)
    assert sum(r['occurrence_count'] for r in rows) + excluded_ferry + no_selected_name == total
    return {'schema': 'bund-map-road-label-leads-v1', 'extracted_utc': datetime.now(timezone.utc).isoformat(),
            'scope': 'Local frozen map label leads only; four central-Shanghai tiles, not an all-city road census or building-model evidence. No baseline or task state changed.',
            'reproduction': {'script': 'projects/shanghai/tools/extract_bund_road_labels.py',
                'requirements': 'projects/shanghai/data/model-todo/tooling/requirements.txt',
                'working_directory': 'repository root',
                'command': 'python projects/shanghai/tools/extract_bund_road_labels.py --repo . --output /tmp/bund-label-recheck.json',
                'output_note': 'Write a fresh review snapshot outside the repository; do not overwrite the baseline, queue or published source records.'},
            'input_files': inputs, 'source_manifest': MANIFEST, 'baseline_path': BASELINE,
            'official_path': OFFICIAL, 'reconciliation_path': RECONCILIATION,
            'source_version': re.search(r'/planet/([^/]+)/', source['tilejson']['tiles'][0]).group(1), 'coverage_bounds_wgs84': source['coverage_bounds'],
            'source_date_note': 'Version label only; no verified per-feature survey date or separate HTTP retrieval timestamp.',
            'license': 'ODbL-1.0', 'attribution': source['attribution'],
            'license_scope': 'OSM-derived labels and source data retain ODbL terms and attribution; cross-reference IDs point to independently attributed research registers.',
            'tiles': tile_records, 'dependencies': {'python': sys.version.split()[0],
                'opencc-python-reimplemented': importlib.metadata.version('opencc-python-reimplemented'),
                'protobuf_reader': 'Included standard-library-only MVT wire reader; original code MIT'},
            'method': {'name_priority': NAME_PRIORITY, 'group_id': 'bund-label- plus first16 SHA256 hexadecimal characters of exact UTF-8 selected name string',
                'baseline_matching': 'OpenCC t2s, strip page-title parenthetical qualifier, outer trim; exact resulting string comparison only',
                'cross_reference_matching': 'Same normalization against official source names and proposed names; no alias or physical identity inferred',
                'layer': 'transportation_name', 'excluded_class': 'ferry', 'geometry_decoded': False,
                'network': 'None. Git lazy fetching disabled when reading existing objects.',
                'address_fields_used': False, 'source_feature_id_status': 'Original MVT feature ID preserved; not verified as OSM ID or globally stable identity'},
            'limitations': ['Label names include bridges, tunnels, access drives, parking, paths and plazas; unmatched labels are not automatically new streets.',
                'Same name strings across tiles/segments grouped for research; different physical roads may share one string.',
                'Class/name lexical flags are review prompts, not authoritative land-use or street classification.',
                'MVT buffered features may lie outside nominal tile bounds; geometry clipping/geographic assignment remains pending.',
                'Missing district assignment stays empty; no current legal road-name register or all-city completeness asserted.',
                'Group extents and route aliases from official sources remain unresolved; name matches do not transfer geometry or completion status.'],
            'counts': {'tiles': len(tile_records), 'input_tile_bytes': sum(t['bytes'] for t in tile_records),
                'transportation_name_features': total, 'excluded_ferry_features': excluded_ferry,
                'nonferry_features_without_selected_name': no_selected_name,
                'grouped_occurrences': sum(r['occurrence_count'] for r in rows),
                'exact_name_string_groups': len(rows), 'matching_baseline_groups': matched,
                'not_matching_baseline_groups': len(rows) - matched,
                'groups_matching_official_original_names': sum(bool(r['official_original_name_matches']) for r in rows),
                'groups_matching_reconciliation_proposed_names': sum(bool(r['reconciliation_proposed_name_matches']) for r in rows),
                'input_classes': dict(all_classes), 'physical_new_roads': None}, 'records': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output.resolve()
    if output == repo / BASELINE or output == repo / (PROJECT + 'data/model-todo/queue.json'):
        parser.error('Output must be a discovery proposal, not the baseline or model queue')
    data = extract(repo)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(data['counts'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
