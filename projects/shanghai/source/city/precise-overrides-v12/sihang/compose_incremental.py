#!/usr/bin/env python3
"""Compose audited fresh near blocks with byte-identical audited prior blocks.

Only writes a new directory beneath this isolated stage. It does not claim a
browser or new-building appearance review; the runtime owner test is separate.
"""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIMIT = 100_000_000

def need(ok, message):
    if not ok: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_bytes())
def encode(value): return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
def meta(path):
    data = path.read_bytes(); return {'file': str(path), 'bytes': len(data), 'sha256': sha(data)}
def write(path, value):
    need(not path.exists(), 'Refuse to overwrite candidate output')
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(value if isinstance(value, bytes) else encode(value))

def audited(root):
    root = root.resolve(); registry_path = root / 'precise-buildings-v6.json'
    registry = read(registry_path)
    need(registry.get('complete') is True, 'Registry is not geometry-audited')
    validation = registry['validation']; name = validation['file']
    need(name == 'geometry-validation.json', 'Expected local frozen geometry evidence')
    report_path = root / name; report = read(report_path)
    need(meta(report_path)['sha256'] == validation['sha256'] and report.get('pass') is True, 'Geometry evidence differs or failed')
    comparisons = read(root / 'geometry-comparison-input.json')
    checks = {row['id']: row for row in comparisons['checks']}
    results = {row['id']: row for row in report['checks']}
    near = {row['id']: row for macro in registry['macros'] for row in macro['near']}
    need(len(near) == sum(len(macro['near']) for macro in registry['macros']) and set(near) == set(checks) == set(results), 'Audit/check/registry near sets differ')
    for ident, row in near.items():
        need(results[ident].get('pass') is True and checks[ident]['groups'] == row['groups'], 'Near proof/group mismatch')
        need(results[ident]['baseline_sha256'] == checks[ident]['baseline_sha256'] == row['baseline_sha256'], 'Geometry proof baseline binding differs')
        data = Path(checks[ident]['override']).read_bytes(); decoded = gzip.decompress(data); model = row['model']
        need(len(data) == model['size_bytes'] and sha(data) == model['sha256'] and len(data) < LIMIT, 'Audited stored near changed')
        need(len(decoded) == model['decoded_size_bytes'] and sha(decoded) == model['decoded_sha256'] and len(decoded) < LIMIT, 'Audited decoded near changed')
        need(results[ident]['override_sha256'] == model['sha256'], 'Geometry result has another variant')
        baseline = Path(checks[ident]['baseline']).read_bytes()
        need(sha(baseline) == row['baseline_sha256'] and sha(gzip.decompress(baseline)) == row['baseline_decoded_sha256'], 'Original near changed after audit')
    return {'root': root, 'registry': registry, 'report': report, 'checks': checks, 'results': results,
            'near': near, 'registry_proof': meta(registry_path), 'geometry_proof': meta(report_path)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--prior-root', type=Path, required=True)
    parser.add_argument('--fresh-root', type=Path, action='append', required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); project = args.project.resolve(); output = args.output.resolve()
    need(output.is_relative_to(HERE) and output != HERE and not output.exists(), 'Use a fresh isolated output directory')
    prior = audited(args.prior_root); fresh = [audited(path) for path in args.fresh_root]
    registry = copy.deepcopy(prior['registry'])
    # This revision adds a distinct macro. Preserve every current accepted
    # existing ten-record / eight-macro catalog byte and descriptor; never attach Sihang compound before review.
    main_path = project / 'data/precise-buildings-v6.json'
    current = read(main_path)
    for key in ('macros', 'landmarks', 'geometry_inputs', 'baseline_configuration_sha256', 'engine_sha256'):
        need(current[key] == registry[key], 'Current project and audited prior differ: ' + key)
    for macro in current['macros']:
        for near in macro['near']:
            need(meta(project / near['model']['file'])['sha256'] == near['model']['sha256'], 'Current prior near bytes changed')
    catalog_descriptor = current.get('ordinary_catalog')
    need(catalog_descriptor is not None, 'Expected current accepted existing ten-record / eight-macro catalog')
    catalog_path = project / catalog_descriptor['file']
    need({k: meta(catalog_path)[k] for k in ('bytes', 'sha256')} == {k: catalog_descriptor[k] for k in ('bytes', 'sha256')}, 'Current catalog hash differs')
    catalog_macro_ids = {row['id'] for row in read(catalog_path)['macros']}
    need(all(not ({m['id'] for m in source['registry']['macros']} & catalog_macro_ids) for source in fresh), 'New macro overlaps accepted catalog; use a complete macro review instead')
    registry['ordinary_catalog'] = copy.deepcopy(catalog_descriptor)
    macros = {row['id']: row for row in registry['macros']}
    landmarks = {row['id']: row for row in registry['landmarks']}
    selected = {ident: (prior, False) for ident in prior['near']}
    incoming = set()
    for source in fresh:
        doc = source['registry']
        need(doc['baseline_configuration_sha256'] == registry['baseline_configuration_sha256'] and doc['engine_sha256'] == registry['engine_sha256'], 'Frozen baseline/engine changed')
        for ident, value in doc['geometry_inputs'].items():
            if ident in registry['geometry_inputs']:
                need(registry['geometry_inputs'][ident] == value, 'Existing target input changed')
            registry['geometry_inputs'][ident] = value
        for row in doc['landmarks']:
            if row['id'] in landmarks: need(landmarks[row['id']] == row, 'Existing target boundary changed')
            landmarks[row['id']] = row
        for macro in doc['macros']:
            mid = macro['id']
            if mid not in macros:
                macros[mid] = copy.deepcopy(macro)
            else:
                old = macros[mid]
                need({k: v for k, v in old.items() if k != 'near'} == {k: v for k, v in macro.items() if k != 'near'}, 'Same macro frozen provenance changed')
                combined = {near['id']: near for near in old['near']}
                for near in macro['near']:
                    if near['id'] in combined:
                        before = combined[near['id']]
                        need(near['featureLocalIds'] == before['featureLocalIds'] and near['baseline_sha256'] == before['baseline_sha256'], 'Affected near baseline changed')
                        before_owners = {group['landmark_id']: (group['local_ids'], group['feature_keys']) for group in before['groups']}
                        after_owners = {group['landmark_id']: (group['local_ids'], group['feature_keys']) for group in near['groups']}
                        need(all(after_owners.get(key) == value for key, value in before_owners.items()), 'Fresh near would drop an existing exact owner')
                    combined[near['id']] = copy.deepcopy(near)
                old['near'] = sorted(combined.values(), key=lambda near: near['id'])
            for near in macro['near']:
                need(near['id'] not in incoming, 'Two fresh outputs claim one near block')
                incoming.add(near['id']); selected[near['id']] = (source, True)
    registry['macros'] = sorted(macros.values(), key=lambda macro: macro['id'])
    registry['landmarks'] = sorted(landmarks.values(), key=lambda row: row['id'])
    targets = sorted(landmarks)
    generator = HERE / 'tools/build_precise_overrides.py'
    spec = importlib.util.spec_from_file_location('frozen_override_generator', generator)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    inputs, claimed, boundaries = module.parse_inputs(project, [args.inputs.resolve()], targets)
    need({row['id']: row for row in boundaries} == landmarks, 'Merged boundaries differ from frozen input')
    need(sha((project / 'source/city/detail/geometry_engine.py').read_bytes()) == registry['engine_sha256'], 'Actual frozen engine changed')
    for ident, row in inputs.items():
        need(row['sha256'] == registry['geometry_inputs'][ident]['sha256'], 'Merged source SHA mismatch')
        need(row.get('mapping_report') == registry['geometry_inputs'][ident].get('mapping_report'), 'Provider mapping-report binding differs')
    need(set(inputs) == set(registry['geometry_inputs']), 'Merged geometry input set differs')
    expected_owners = {(mid, local, ident, key) for mid, values in claimed.items() for local, (ident, key) in values.items()}
    actual_owners = []
    for macro in registry['macros']:
        for near in macro['near']:
            for group in near['groups']:
                need(len(group['local_ids']) == len(group['feature_keys']), 'Owner key cardinality differs')
                actual_owners.extend((macro['id'], local, group['landmark_id'], key)
                                     for local, key in zip(group['local_ids'], group['feature_keys']))
    need(len(actual_owners) == len(set(actual_owners)) and set(actual_owners) == expected_owners,
         'Merged exact owner groups are missing, duplicated or assigned to another source')
    for mid, macro in macros.items():
        root = project / 'assets/city-detail/macros' / mid
        need(meta(root / 'READY.json')['sha256'] == macro['baseline_ready_sha256']
             and meta(root / 'feature-table.json.gz')['sha256'] == macro['baseline_feature_table_sha256'], 'Current macro metadata differs')
        ready = read(root / 'READY.json'); table = json.loads(gzip.decompress((root / 'feature-table.json.gz').read_bytes()))
        by_id = {row['localId']: row for row in table['features']}
        for local, (ident, key) in claimed[mid].items():
            need(by_id[local] == inputs[ident]['data']['current_city_detail']['frozen_effective_feature'], 'Current complete target feature differs')
        for near in macro['near']:
            original = next(row for row in ready['near'] if row['id'] == near['id'])
            need(original['featureLocalIds'] == near['featureLocalIds'] and original['sha256'] == near['baseline_sha256'], 'Exact near ownership differs')

    checks = []; results = []; reuse = []; files = []
    output.mkdir()
    for macro in registry['macros']:
        for near in macro['near']:
            source, is_fresh = selected[near['id']]
            model = near['model']; prefix = 'assets/city-overrides-v6/'
            need(model['file'].startswith(prefix), 'Unexpected variant output namespace')
            rel = model['file'][len(prefix):]
            need(Path(rel).parts[0] == macro['id'] and '..' not in Path(rel).parts and not Path(rel).is_absolute(), 'Variant is not macro-qualified')
            data = Path(source['checks'][near['id']]['override']).read_bytes()
            need(sha(data) == model['sha256'], 'Near changed between validation and copy')
            target = output / rel; write(target, data)
            check = copy.deepcopy(source['checks'][near['id']]); check['override'] = str(target)
            check['audit_scope_this_revision'] = 'fresh actual decoded geometry check' if is_fresh else 'prior actual decoded check reused after exact current baseline/source/asset SHA verification'
            checks.append(check)
            result = copy.deepcopy(source['results'][near['id']])
            result['audit_origin'] = {'fresh_in_this_revision': is_fresh, 'registry': source['registry_proof'], 'geometry_report': source['geometry_proof']}
            results.append(result)
            files.append({'file': model['file'], 'source': str(target), 'bytes': len(data), 'sha256': sha(data), 'fresh_generated': is_fresh})
            if not is_fresh:
                reuse.append({'id': near['id'], 'model_sha256': model['sha256'], 'bytes': len(data),
                              'same_decoded_sha256': True, 'byte_identical': True, 'regenerated': False})
    geometry_report = {'schema': 'city-precise-geometry-comparison-incremental-v1', 'pass': True,
        'scope': 'Fresh affected near blocks use actual production Three/Meshopt decoded position/material/winding/normal/owner tests. Unchanged blocks reuse their byte-bound prior actual decoded evidence after current baseline, source inputs, stored and decoded hashes are checked; they were not regenerated or re-decoded for this geometry comparison.',
        'normal_policy': fresh[0]['report']['normal_policy'], 'checks': results,
        'fresh_near_ids': sorted(incoming), 'reused_near_ids': sorted(set(selected) - incoming),
        'fresh_reports': [source['geometry_proof'] for source in fresh], 'prior_report': prior['geometry_proof'],
        'browser_or_new_precise_building_appearance_acceptance': False}
    write(output / 'geometry-validation.json', geometry_report)
    registry['reuse_validation'] = reuse
    registry['complete'] = True
    registry['status'] = 'incremental exact-source geometry audit passed; new precise-model/browser acceptance remains separate'
    registry['validation'] = {'file': 'geometry-validation.json', 'sha256': meta(output / 'geometry-validation.json')['sha256']}
    draft = copy.deepcopy(registry); draft['complete'] = False; draft['status'] = 'Full optional recheck draft; do not use for runtime'
    write(output / 'precise-buildings-v6.draft.json', draft)
    write(output / 'precise-buildings-v6.json', registry)
    write(output / 'geometry-comparison-input.json', {'project': str(project), 'output': str(output), 'checks': checks,
         'negative_control_target_ids': sorted({group['landmark_id'] for source in fresh for macro in source['registry']['macros'] for near in macro['near'] for group in near['groups']})})
    write(output / 'asset-files.json', {'schema': 'precise-override-asset-files-v1', 'files': files,
        'registry': {'file': 'data/precise-buildings-v6.json', 'source': str(output / 'precise-buildings-v6.json'),
                     **{key: value for key, value in meta(output / 'precise-buildings-v6.json').items() if key != 'file'}},
        'production_or_candidate_installed': False})
    summary = {'schema': 'incremental-precise-owner-handoff-v1', 'geometry_passed': True,
        'runtime_owner_test_passed': False, 'browser_passed': False, 'new_building_model_accepted': False,
        'targets': len(landmarks), 'macros': len(macros), 'near_blocks': len(checks),
        'fresh_near_blocks': len(incoming), 'reused_near_blocks': len(reuse),
        'total_source_features': sum(len(near['featureLocalIds']) for macro in registry['macros'] for near in macro['near']),
        'target_source_features': sum(len(group['local_ids']) for macro in registry['macros'] for near in macro['near'] for group in near['groups']),
        'stored_bytes': sum(row['bytes'] for row in files),
        'expanded_triangles': sum(near['model']['expandedTriangles'] for macro in registry['macros'] for near in macro['near']),
        'registry': meta(output / 'precise-buildings-v6.json'), 'geometry_report': meta(output / 'geometry-validation.json'),
        'ordinary_catalog_descriptor_present': True, 'production_or_candidate_installed': False,
        'current_main_registry': meta(main_path),
        'preserved_ordinary_catalog': copy.deepcopy(catalog_descriptor),
        'catalog_scope': 'Existing accepted existing ten-record / eight-macro catalog descriptor and bytes remain unchanged. The Sihang compound is a new separate macro and are not included in that catalog; model, static candidate, browser and later catalog acceptance are still pending.'}
    write(output / 'composition-report.json', summary)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__': main()
