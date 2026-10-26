#!/usr/bin/env python3
"""Prepare one immutable model-only draft from actual evidence; never install or accept a browser scene."""
from pathlib import Path
import argparse
import copy
import json
import sys
sys.dont_write_bytecode = True
from contracts import (HERE, SECTIONS, REQUIRED, Inputs, need, text, identity, read_json,
                       no_symlink, descriptor, public_text, ready_target, source_freeze, tool_source_freeze,
                       check_geometry, package_and_photos, decoded, native_review, navigation,
                       prebrowser_review, public_source_whitelist)
from report_adapters import validate_independent_raw, engine_descriptor
from supplement_dispatch import validate_raw_supplements, validate_decoded_supplement_transfer


def write(path, document):
    serialized = public_text(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    need(0 < len(serialized.encode('utf-8')) < 100_000_000, 'Generated file must be strictly below100M')
    with path.open('x', encoding='utf-8') as stream:
        stream.write(serialized)
    return descriptor(path)


def require_frozen_tools(request, package, decoded_report, raw_report, structure, frozen, inputs, supplements=None):
    suite = inputs.json(decoded_report['finite_actual_decoded_report'])
    descriptors = [suite[name] for name in ('decoder', 'decoder_core', 'bridge', 'independent_engine_lock')]
    descriptors += [engine_descriptor(row) for row in raw_report['checker_files'] + structure['checker_files']]
    descriptors += [descriptor(HERE / name) for name in ('contracts.py', 'report_adapters.py', 'prepare_registration.py', 'public_dependency_compat.py', 'public_dependency_allowlist.json', 'geometry_supplements.py', 'supplement_dispatch.py', 'museum_supplements.py')]
    if supplements is not None:
        descriptors += supplements['checker_dependencies']
    descriptors += [descriptor(HERE.parent / name) for name in ('package_modern.py', 'modern_contract.py', 'upstream-lock.json')]
    upstream_descriptor = descriptor(HERE.parent / 'upstream-lock.json')
    need(upstream_descriptor['sha256'] == 'f5e30d8d9c18edc3486c5591d7d86439dd2da3afb6b4217a9111581da1b78275',
         'Reviewed upstream dependency lock changed; explicit registrar revision required')
    upstream = inputs.json(upstream_descriptor)
    for row in upstream['files']:
        matches = [source for source, value in frozen.items()
                   if source.endswith('/' + row['project_relative']) and value == identity(row)]
        need(len(matches) == 1, 'Actual upstream dependency missing or ambiguous in tool freeze: ' + row['project_relative'])
        descriptors.append({'source': matches[0], **identity(row)})
        if row.get('snapshot'):
            descriptors.append({'source': str(HERE.parent / row['snapshot']), **identity(row)})
    need(package.get('generator_sha256') == descriptor(HERE.parent / 'package_modern.py')['sha256'], 'Package generator revision differs')
    core = descriptor(HERE.parent / 'upstream/package_building.py')
    need(package.get('frozen_helper', {}).get('file') == core['source']
         and package['frozen_helper'].get('sha256') == core['sha256'], 'Package core helper differs')
    measurement = next(row for row in upstream['files'] if row['project_relative'] == 'tools/build_bund_lods.py')
    need(package.get('measurement_helper') == {'file': measurement['project_relative'], 'sha256': measurement['sha256']},
         'Package actual measurement helper differs')
    lock = inputs.json(suite['independent_engine_lock'])
    for row in lock['files']:
        descriptors.append(row)
    for row in descriptors:
        path = inputs.file(row)
        need(frozen.get(str(path)) == identity(row), 'Actual decoder/checker/registrar dependency absent from separate tool freeze: ' + str(path))


def run(request_path, output):
    output = no_symlink(output).resolve()
    need(output.is_relative_to(HERE) and output != HERE and not output.exists(),
         'Output must be a new directory within packaging-preparation/registration')
    inputs = Inputs()
    request_descriptor = descriptor(request_path)
    request = inputs.json(request_descriptor)
    ident, target = ready_target(request, inputs)
    for name in REQUIRED:
        inputs.file(request[name])
    geometry = inputs.json(request['source_geometry'])
    check_geometry(geometry, target)
    _, frozen_sources = source_freeze(request, target, inputs)
    _, frozen_tools = tool_source_freeze(request, inputs)
    package, photos = package_and_photos(request, target, inputs)
    raw_report, structure = validate_independent_raw(request, target, package, inputs)
    supplements = validate_raw_supplements(request, target, package, structure, inputs)
    decoded_report = decoded(request, target, package, inputs)
    supplement_transfer = validate_decoded_supplement_transfer(supplements, decoded_report, request, target, package, structure, inputs)
    native, visual = native_review(request, target, package, decoded_report, inputs)
    nav = navigation(request, target, geometry, package, inputs)
    review = prebrowser_review(request, target, package, photos, decoded_report, inputs)
    whitelist, source_files = public_source_whitelist(request, target, package, photos, frozen_sources, frozen_tools, inputs)
    require_frozen_tools(request, package, decoded_report, raw_report, structure, frozen_tools, inputs, supplements)
    reserved = {'source/precise/' + ident + '/delivery/' + name for name in
                ('prebrowser-acceptance-summary.json', 'registration.draft.json', 'model-metadata.json')}
    need(not {row['file'].casefold() for row in source_files}.intersection({name.casefold() for name in reserved}),
         'Explicit source whitelist collides with generated delivery documents')
    # Reject hidden snapshots in fields later copied to public generated documents.
    public_text(json.dumps([review, package['provenance'], nav, visual], ensure_ascii=False, allow_nan=False))
    inputs.recheck()

    # No output directory exists before every current input gate above passes.
    output.mkdir(parents=True, exist_ok=False)
    incomplete = output / 'INCOMPLETE'
    incomplete.write_text('Preparation has not completed. Never install this directory while this marker exists.\n', encoding='utf-8')
    limitations = list(dict.fromkeys(review['limitations'] + visual['limitations'] + nav['limitations']))
    summary = {'schema': 'modern-prebrowser-acceptance-summary-v11', 'building_id': ident,
               'prebrowser_scope_passed': True, 'browser_accepted': False, 'registered': False,
               'request': request_descriptor, 'review': request['prebrowser_review'],
               'evidence': {name: request[name] for name in REQUIRED},
               'raw_sha256': package['assets']['raw']['sha256'], 'limitations': limitations,
               'scope': 'Copies nine existing substantive reviews after actual hash-bound checks; no photographic measurement, complete collision or HTML acceptance is inferred.'}
    summary.update(copy.deepcopy(review['sections']))
    summary['geometry_supplement_transfer'] = supplement_transfer
    summary_descriptor = write(output / 'prebrowser-acceptance-summary.json', summary)
    provenance = package['provenance']
    entry = {key: copy.deepcopy(provenance[key]) for key in ('id', 'name', 'district', 'source_provider', 'source_url',
                                                           'source_license', 'asset_license', 'appearance_epoch')}
    height = review['sections']['height_evidence']
    entry.update(geometry_input=request['source_geometry'], assets=package['registration_assets'],
                 source_photos=photos, primary_photo=review['registration']['primary_photo'],
                 source_package='source/precise/' + ident,
                 height={'metres': height['height_m'], 'estimated': True, 'note': height['scope']},
                 uncertainty=limitations, navigation=nav['navigation'], navigation_evidence=request['navigation'],
                 navigation_scope=nav['scope'], architecture_style=review['registration']['architecture_style'],
                 detail_note=review['registration']['detail_note'], browser_accepted=False,
                 geographic_opening_alignment=None)
    entry['acceptance'] = {key: {'status': 'passed', 'evidence': summary_descriptor, 'section': key} for key in SECTIONS}
    entry['acceptance']['browser_proof'] = {'status': 'pending', 'reason': 'Independent model delivery only. Actual browser, exact-owner and navigation review belong to subsequent integration.'}
    draft_descriptor = write(output / 'registration.draft.json', {'schema': 'precise-registration-input-v1', 'buildings': [entry]})
    metadata = {'schema': 'modern-actual-model-metadata-v11', 'id': ident, 'macro': target['owner_macro_id'],
                'raw': package['registration_assets']['raw'], 'actual_bounds_enu_m': decoded_report['assets']['raw']['bounds_enu_m'],
                'actual_bounds_glb': decoded_report['assets']['raw']['bounds_glb'], 'height_estimate_m': height['height_m'],
                'height_is_measured': False, 'ground_base_m': decoded_report['assets']['raw']['bounds_enu_m'][0][2],
                'source_geometry': request['source_geometry'], 'source_freeze': request['source_freeze'],
                'package': request['package_record'], 'actual_decoded': request['decoded_report'],
                'actual_raw_geometry': request['independent_raw_review'], 'native_render': request['native_report'],
                'native_visual': request['root_native_review'], 'native_visual_passed': True,
                'browser_accepted': False, 'registered': False, 'installed': False, 'limitations': limitations}
    metadata['geometry_supplement_transfer'] = supplement_transfer
    metadata_descriptor = write(output / 'model-metadata.json', metadata)
    all_files = [dict(row, kind='model-asset') for row in package['registration_assets'].values()] + source_files
    for name, item in [('prebrowser-acceptance-summary.json', summary_descriptor), ('registration.draft.json', draft_descriptor),
                       ('model-metadata.json', metadata_descriptor)]:
        all_files.append({'file': 'source/precise/' + ident + '/delivery/' + name, **item, 'kind': 'generated-evidence'})
    names = [row['file'].casefold() for row in all_files]
    need(len(names) == len(set(names)), 'Generated delivery outputs collide with source/model destinations')
    manifest = {'schema': 'modern-model-stage-delivery-manifest-v11', 'building_id': ident,
                'request': request_descriptor, 'registration': draft_descriptor, 'metadata': metadata_descriptor,
                'source_whitelist': request['source_delivery_whitelist'], 'source_document_roles': whitelist['document_roles'],
                'model_asset_count': 4, 'files': all_files, 'file_count': len(all_files),
                'total_bytes': sum(row['bytes'] for row in all_files), 'exclusive_per_file_bytes': 100_000_000,
                'browser_accepted': False, 'registered': False, 'installed': False,
                'requires_fresh_destination_guards_before_install': True,
                'scope': 'Exact references only. No source/payload copy, MAIN mutation, browser launch, Git operation or publication occurred.'}
    manifest_descriptor = write(output / 'delivery-manifest.json', manifest)
    inputs.recheck()
    lock = {'schema': 'modern-registration-actual-input-lock-v11', 'request': request_descriptor,
            'files': [{'source': source, **value} for source, value in sorted(inputs.bound.items())],
            'outputs': [summary_descriptor, draft_descriptor, metadata_descriptor, manifest_descriptor],
            'browser_accepted': False, 'registered': False, 'installed': False}
    lock_descriptor = write(output / 'input-lock.json', lock)
    incomplete.unlink()
    return {'registration': draft_descriptor, 'model_metadata': metadata_descriptor, 'delivery_manifest': manifest_descriptor,
            'input_lock': lock_descriptor, 'browser_accepted': False, 'registered': False, 'installed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.request, args.output)
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        parser.exit(1, 'Registration rejected: ' + str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
