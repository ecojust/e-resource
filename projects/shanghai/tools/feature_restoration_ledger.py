"""Join every frozen render feature to model registrations; never infer acceptance.

No network or mesh writes. Requires all 1,708 feature tables and READY manifests.
Outputs deterministic district JSONL gzip shards and a hash-bound metadata index.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile

from ordinary_assets import inspect as inspect_ordinary


def require(value, message):
    if not value:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def descriptor(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def join_registration(joined, key, value):
    require(key not in joined or joined[key] == value, 'Conflicting source ownership: ' + key)
    joined[key] = value


def validate_table(table, count, seen):
    keys = table['keys']
    require(table['feature_id_base'] == 1 and len(keys) == count + 1 and keys[0] is None,
            'Invalid feature table count/base')
    require(len(table['features']) == count and len(set(keys[1:])) == count,
            'Missing or duplicate local feature')
    require(not seen.intersection(keys[1:]), 'Duplicate feature across macros')
    for local_id, row in enumerate(table['features'], 1):
        props = row['properties']
        require(row['localId'] == local_id and row['key'] == keys[local_id] ==
                str(props['source_layer']) + ':' + str(props['id']), 'Feature identity/order mismatch')
    seen.update(keys[1:])


def build(project, output):
    inputs = {'tools/feature_restoration_ledger.py': descriptor(Path(__file__).read_bytes())}

    def read(name, expected=None):
        data = (project / name).read_bytes()
        meta = descriptor(data)
        if expected:
            require(meta == {k: expected[k] for k in meta}, 'Input hash/size mismatch: ' + name)
        inputs[name] = meta
        return json.loads(gzip.decompress(data) if name.endswith('.gz') else data)

    city = read('assets/city/manifest.json')
    detail = read('assets/city-detail/manifest.json')
    raw = read('data/fullcity-raw/manifest.json')
    registry = read('data/precise-buildings-v6.json')
    landmarks = read('data/landmarks.json')
    require(all(row.get('model') or row.get('url') for row in landmarks), 'Missing registered model URL')
    exclusions = read('data/landmark-exclusions.json')
    surface = read('assets/surfaces/manifest.json')
    read('data/districts.json')
    # Validate existing ordinary ownership and catalog descriptors, without
    # promoting metadata declarations into fresh asset/photo acceptance.
    ordinary = inspect_ordinary(project, landmarks, registry, verify_files=False)
    for name, data in ordinary['immutable'].items():
        inputs[name] = descriptor(data)
    joined = {}
    for reg in ordinary['registries']:
        for macro in reg['macros']:
            for near in macro['near']:
                for group in near['groups']:
                    require(len(group['feature_keys']) == len(group['local_ids']), 'Group key/ID mismatch')
                    for key, local_id in zip(group['feature_keys'], group['local_ids']):
                        join_registration(joined, key, {
                            'model_id': group['landmark_id'], 'macro': macro['id'],
                            'local_id': local_id,
                            'feature_table_sha256': macro['baseline_feature_table_sha256'],
                            'ready_sha256': macro['baseline_ready_sha256'],
                            'configuration_sha256': macro['baseline_configuration_sha256'],
                        })
    external = {}
    for model in exclusions['landmark_sources']:
        for match in model['matches']:
            key = match['source_layer'] + ':' + match['id']
            join_registration(external, key, {
                'key': key, 'model_id': model['landmark_id'],
                'source_renderable': match['source_renderable'],
                'parent_building_id': match.get('building_id'),
                'source_record_ids': match.get('source_record_ids', []),
                'representation': 'excluded-for-landmark', 'acceptance_revalidated': False,
            })
    protected = {layer + ':' + key for layer in ('building', 'building_part')
                 for key in exclusions[layer + '_ids']}
    require(set(external) == protected and not protected.intersection(joined),
            'Exclusion ownership missing or conflicts with precise replacement')

    repo = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=project, text=True).strip())
    prefix = project.relative_to(repo).as_posix() + '/'
    tracked = subprocess.check_output(['git', 'ls-files', '--', prefix + 'assets/models/candidates/*/manifest.json'],
                                      cwd=repo, text=True).splitlines()
    candidates = []
    integrated_previews = []
    candidate_keys = defaultdict(list)
    for file in tracked:
        name = file[len(prefix):]
        candidate = read(name)
        if candidate.get('map_replacement') or candidate.get('walk_integration'):
            require(candidate.get('map_replacement') is True and candidate.get('walk_integration') is True, 'Partial candidate integration declaration')
            owner = joined.get(candidate.get('source_owner'))
            require(owner and owner['model_id']==candidate['id'] and owner['local_id']==candidate.get('source_local_id') and any(r['id']==candidate['id'] and r.get('accepted') and r.get('navigation',{}).get('listed') for r in landmarks), 'Integrated preview lacks matching source owner and navigation')
            integrated_previews.append({'id':candidate['id'],'manifest':name,'source_key':candidate['source_owner']})
            continue
        require(candidate.get('map_replacement') is False and candidate.get('walk_integration') is False,
                'Candidate integration changed; reassess ledger')
        record = {'id': candidate['id'], 'manifest': name, 'status': candidate['status'],
                  'source_key': candidate.get('source_owner'), 'source_local_id': candidate.get('source_local_id')}
        candidates.append(record)
        if record['source_key']:
            candidate_keys[record['source_key']].append(record)

    districts = {d['id']: d for d in city['districts']}
    macro_rows = {t['id']: t for t in city['tiles']}
    require(len(macro_rows) == len(city['tiles']) == len(detail['tiles']) == city['model_count'] == detail['model_count'],
            'Incomplete macro inventory')
    require(set(macro_rows) == {t['id'] for t in detail['tiles']}, 'Macro inventory differs')
    require({d['id']: d['features'] for d in detail['districts']} ==
            {d['id']: d['features'] for d in city['districts']}, 'District inventories differ')
    output.mkdir(parents=True, exist_ok=True)
    counts, height_counts, role_counts = Counter(), Counter(), Counter()
    residuals, excluded, nonrenderable, seen, resolved = set(), set(), set(), set(), set()
    macros = []
    # Stream by district to keep memory proportional to one feature table plus
    # the global unique-key set, not 1.8 million expanded JSON dictionaries.
    streams = {district: gzip.GzipFile(filename='', mode='wb', mtime=0, compresslevel=9,
               fileobj=(output / (district + '.jsonl.gz')).open('wb')) for district in districts}
    try:
        for tile in sorted(detail['tiles'], key=lambda row: row['id']):
            macro = tile['id']
            ready = read('assets/city-detail/' + tile['near_manifest_file'])
            table_name = 'assets/city-detail/' + tile['feature_table_file']
            require(ready['id'] == macro and ready['complete'] is True, 'Incomplete READY: ' + macro)
            require(ready['configuration_sha256'] == detail['configuration_sha256'], 'Mixed configuration: ' + macro)
            count = tile['feature_count']
            require(count == ready['feature_count'] == macro_rows[macro]['building_count'], 'Macro count mismatch: ' + macro)
            require(ready['source_sha256'] == macro_rows[macro]['source_sha256'], 'Source version mismatch: ' + macro)
            require(Path(tile['feature_table_file']).parent == Path(tile['near_manifest_file']).parent and
                    Path(tile['feature_table_file']).name == ready['feature_table_file'], 'Feature table path mismatch')
            table = read(table_name, ready['published_files'][ready['feature_table_file']])
            validate_table(table, count, seen)
            local_counts = Counter()
            local_residuals = 0
            for feature in table['features']:
                props = feature['properties']
                key, district = feature['key'], str(props['district_id'])
                require(district in districts, 'Unknown district: ' + district)
                binding = joined.get(key)
                if binding:
                    require(binding['macro'] == macro and binding['local_id'] == feature['localId'] and
                            binding['feature_table_sha256'] == inputs[table_name]['sha256'] and
                            binding['ready_sha256'] == inputs['assets/city-detail/' + tile['near_manifest_file']]['sha256'] and
                            binding['configuration_sha256'] == ready['configuration_sha256'], 'Registration binding mismatch: ' + key)
                    resolved.add(key)
                residual = bool(feature.get('residual'))
                if residual:
                    residuals.add(key)
                    local_residuals += 1
                role = 'registered-precise-replacement' if binding else 'baseline-generated'
                record = {'key': key, 'macro': macro, 'local_id': feature['localId'],
                          'district_id': district, 'residual': residual,
                          'parent_building_id': props.get('building_id'),
                          'height_quality': feature['height_quality'], 'representation': role,
                          'acceptance_revalidated': False}
                if binding:
                    record['model_id'] = binding['model_id']
                if key in candidate_keys:
                    require(all(c['source_local_id'] == feature['localId'] for c in candidate_keys[key]),
                            'Candidate local ID mismatch: ' + key)
                    record['candidate_ids'] = sorted(c['id'] for c in candidate_keys[key])
                streams[district].write(encoded(record))
                counts[district] += 1
                local_counts[district] += 1
                height_counts[feature['height_quality']] += 1
                role_counts[role] += 1
            require(dict(local_counts) == {str(k): v['features'] for k, v in macro_rows[macro]['district_counts'].items()},
                    'Macro district partition mismatch: ' + macro)
            require(local_residuals == ready['residual_count'], 'Residual count mismatch: ' + macro)
            excluded.update(ready['excluded_renderable_keys'])
            nonrenderable.update(ready['nonrenderable_keys'])
            macros.append({'id': macro, 'feature_table': table_name,
                           'ready': 'assets/city-detail/' + tile['near_manifest_file'], 'features': count})
    finally:
        for stream in streams.values():
            underlying = stream.fileobj
            stream.close()
            underlying.close()
    require(set(joined) == resolved, 'Registered features missing from baseline')
    require(set(candidate_keys) <= seen, 'Candidate source owner missing from baseline')
    require(not seen.intersection(protected), 'Excluded source reappears in baseline')
    require(excluded == {key for key, val in external.items() if val['source_renderable']}, 'Excluded renderable set mismatch')
    excluded_parents = {key for key, val in external.items() if not val['source_renderable']}
    require(not nonrenderable.intersection(residuals | excluded_parents) and not residuals.intersection(excluded_parents),
            'Nonrenderable source roles overlap unexpectedly')
    unrepresented_parents = sorted(nonrenderable)
    # READY lists only parents that have no generated representation. Residual
    # parents and protected landmark parents are separate source roles.
    nonrenderable.update(residuals | excluded_parents)
    require(seen.intersection(nonrenderable) == residuals, 'Residual/nonrenderable identity mismatch')
    require(len(seen) == city['feature_count'] == detail['feature_count'], 'Global render count mismatch')
    require(len(residuals) == city['residual_parent_features'] and len(excluded) == city['landmark_replacement_count'] and
            len(nonrenderable) == city['nonrenderable_parent_count'], 'Global source-role counts mismatch')
    require(len(seen | excluded | nonrenderable) == raw['feature_count'], 'Source unique-key conservation failed')
    require(len(seen) - len(residuals) + len(excluded) == raw['renderable_feature_count'], 'Source renderable conservation failed')
    require(dict(counts) == {key: row['features'] for key, row in districts.items()}, 'District feature count mismatch')
    external_document = {'schema': 'source-outside-render-baseline-v1',
                         'landmark_exclusions': [external[k] for k in sorted(external)],
                         'nonrenderable_parent_keys': sorted(nonrenderable),
                         'nonrenderable_parents_without_representation': unrepresented_parents,
                         'residual_parent_keys_in_render_baseline': sorted(residuals)}
    (output / 'source-roles.json').write_bytes(encoded(external_document))
    represented_models = {v['model_id'] for v in joined.values()} | {v['model_id'] for v in external.values()}
    require(represented_models == {row['id'] for row in landmarks}, 'Navigation/model ownership coverage differs')
    require({d['id'] for d in surface['districts']} == set(districts), 'Surface district coverage differs')
    summary = {
        'schema': 'feature-restoration-ledger-v1',
        'scope': 'Full frozen feature identity and registration join; metadata only, no new restoration acceptance',
        'source_release': raw['release'], 'source_license': raw['license'], 'source_attribution': raw['attribution'],
        'inputs': dict(sorted(inputs.items())), 'macros': macros,
        'counts': {'baseline_render_features': len(seen), 'source_unique_above_ground': raw['feature_count'],
                   'source_renderable_features': raw['renderable_feature_count'],
                   'residual_parent_representations': len(residuals), 'nonrenderable_parents': len(nonrenderable),
                   'nonrenderable_parents_without_representation': len(unrepresented_parents),
                   'excluded_renderable_source_features': len(excluded),
                   'registered_precise_source_keys_in_baseline': len(joined),
                   'excluded_source_keys_with_landmark_registration': len(external),
                   'registered_model_ids': len(represented_models),
                   'standalone_candidates': len(candidates), 'candidates_with_source_key': sum(bool(c['source_key']) for c in candidates)},
        'accepted_source_feature_count': None, 'completion_percentage': None,
        'height_quality': dict(sorted(height_counts.items())), 'representations': dict(sorted(role_counts.items())),
        'districts': [{'id': key, 'name': districts[key]['name'], 'features': counts[key],
                       'file': key + '.jsonl.gz', **descriptor((output / (key + '.jsonl.gz')).read_bytes())}
                      for key in sorted(districts)],
        'source_roles': {'file': 'source-roles.json', **descriptor((output / 'source-roles.json').read_bytes())},
        'model_registrations': [{'id': row['id'], 'name': row['name'], 'model': row.get('model') or row['url'],
                                 'source_keys': sorted(k for k, v in {**joined, **external}.items() if v['model_id'] == row['id']),
                                 'catalog_accepted_declaration': row.get('accepted'),
                                 'acceptance_revalidated': False} for row in sorted(landmarks, key=lambda row: row['id'])],
        'candidates': candidates,
        'integrated_model_previews': integrated_previews,
        'surfaces': {'scope': surface['scope'], 'districts': len(surface['districts']),
                     'triangles': sum(d['triangles'] for d in surface['districts']),
                     'measured_elevation_accepted': False, 'riverbed_accepted': False},
        'limitations': [
            'Registration joins establish identity only, not measured geometry or current photographic fidelity.',
            'Baseline rows include parent residuals and building parts; they are not all independent buildings.',
            'Nonrenderable parent keys overlap residual rows and some landmark exclusions; do not sum these sets.',
            'Source versions, geometry and provenance remain in the hash-bound feature table at the listed local ID.',
            'Model assets and historic evidence attachments were not revalidated by this metadata audit.',
            'Unanchored candidates are listed separately and never assigned to a nearby source building.',
            'Ground and water are flat proxies; riverbeds, vertical datum and measured terrain remain unsupported.',
        ],
    }
    (output / 'index.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    return summary


def lookup(directory, key):
    index = json.loads((directory / 'index.json').read_bytes())
    roles = (directory / index['source_roles']['file']).read_bytes()
    require(descriptor(roles) == {k: index['source_roles'][k] for k in ('bytes', 'sha256')}, 'Source roles hash mismatch')
    roles = json.loads(roles)
    matches = [r for r in roles['landmark_exclusions'] if r['key'] == key]
    for district in index['districts']:
        data = (directory / district['file']).read_bytes()
        require(descriptor(data) == {k: district[k] for k in ('bytes', 'sha256')}, 'Ledger shard hash mismatch')
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            for line in stream:
                # Cheap byte filter before parsing nearly two million records.
                if key.encode() in line:
                    row = json.loads(line)
                    if row['key'] == key:
                        matches.append(row)
    return {'key': key, 'records': matches, 'nonrenderable_parent': key in roles['nonrenderable_parent_keys'],
            'residual_parent': key in roles['residual_parent_keys_in_render_baseline']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--key', help='Look up an exact building:UUID or building_part:UUID')
    args = parser.parse_args()
    project = args.project.resolve()
    output = project / 'data/feature-restoration'
    if args.key:
        print(json.dumps(lookup(output, args.key), ensure_ascii=False, indent=2))
        return
    # Only publish after every source and count has passed. A failed rebuild
    # leaves the previously reviewed ledger untouched.
    with tempfile.TemporaryDirectory(prefix='shanghai-feature-ledger-') as temporary:
        directory = Path(temporary)
        summary = build(project, directory)
        if not args.check:
            output.mkdir(parents=True, exist_ok=True)
        for file in sorted(directory.iterdir()):
            if args.check:
                require((output / file.name).read_bytes() == file.read_bytes(), 'Outdated ledger: ' + file.name)
            else:
                (output / file.name).write_bytes(file.read_bytes())
        print(json.dumps(summary['counts'], ensure_ascii=False))


if __name__ == '__main__':
    main()
