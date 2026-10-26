"""Adapters only for the actual V11 independent geometry/decoded interfaces."""
from pathlib import Path
import json
import re
from contracts import need, identity, safe_relative, text


def engine_descriptor(row):
    # The independent engine intentionally uses `file`, unlike delivery descriptors.
    return {'source': row.get('source', row.get('file')), **identity(row)}


def validate_structure(request, target, package, inputs):
    selected = target['actual'].get('source_structure_report')
    report = inputs.json(selected)
    need(report.get('schema') == 'modern-actual-raw-structure-v1'
         and report.get('model_id') == target['id'] and report.get('structure_passed') is True,
         'Unknown, unrelated or failed independent actual raw structure report')
    need(identity(report.get('asset_identity', {}).get('raw')) == identity(package['assets']['raw'])
         and report.get('source_geometry_sha256') == request['source_geometry']['sha256']
         and report.get('calibration_sha256') == request['source_roles']['calibration']['sha256']
         and identity(report.get('frozen_source_manifest')) == identity(request['source_freeze']),
         'Independent actual structure input binding differs')
    inputs.file(engine_descriptor(report['asset_identity']['raw']))
    inputs.file(engine_descriptor(report['frozen_source_manifest']))
    need(report.get('normal_tolerance_degrees') == .001 and report.get('failed_part_keys') == []
         and report.get('model_appearance_accepted') is False and report.get('browser_or_native_reviewed') is False,
         'Raw structure proof scope or normal tolerance differs')
    parts = report.get('part_results')
    need(isinstance(parts, list) and parts and report.get('parts') == len(parts)
         and len({p.get('key') for p in parts}) == len(parts), 'Actual structure part coverage is empty/duplicate')
    for part in parts:
        need(part.get('closed_oriented_positive_components') is True
             and part.get('flat_normals_match_actual_triangles') is True
             and type(part.get('triangles')) is int and part['triangles'] > 0
             and re.fullmatch('[0-9a-f]{64}', part.get('oriented_position_triangles_sha256', '')),
             'Actual raw part lacks passed closure/orientation/positive-volume/normal proof')
    need(report.get('triangles') == sum(p['triangles'] for p in parts), 'Raw structure triangle coverage differs')
    checkers = report.get('checker_files')
    need(isinstance(checkers, list) and {Path(r.get('file', '')).name for r in checkers}
         == {'modern_mesh.py', 'audit_raw_structure.py'}, 'Exact independent raw checker set required')
    for row in checkers:
        inputs.file(engine_descriptor(row))
    return report


def validate_finite(report, current, request, target, structure, inputs):
    need(report.get('schema') == 'modern-actual-finite-checks-v1'
         and report.get('model_id') == target['id'] and report.get('finite_checks_passed') is True,
         'Unknown, unrelated or failed actual finite geometry report')
    bound = report.get('source_binding') or {}
    wanted = {'raw_sha256': target['actual']['raw']['sha256'],
              'source_freeze_sha256': request['source_freeze']['sha256'],
              'geometry_input_sha256': request['source_geometry']['sha256'],
              'calibration_sha256': request['source_roles']['calibration']['sha256'],
              'structure_report_sha256': target['actual']['source_structure_report']['sha256']}
    need(all(bound.get(key) == value for key, value in wanted.items()), 'Finite proof source/structure binding differs')
    inputs.file(engine_descriptor(report.get('source_structure_report')))
    need(identity(report['source_structure_report']) == identity(target['actual']['source_structure_report']), 'Finite actual source structure differs')
    asset = report.get('asset_identity', {})
    actual = asset.get('asset', asset.get('raw'))
    need(identity(actual) == identity(current), 'Finite proof belongs to another actual asset')
    inputs.file(engine_descriptor(actual))
    probes = inputs.json(target['actual'].get('probe_set'))
    need(probes.get('schema') == 'modern-finite-requests-v1' and probes.get('state') == 'READY_FOR_ACTUAL_AUDIT'
         and probes.get('model_id') == target['id'] and probes.get('source_binding') == bound,
         'Actual finite requests remain pending or differ')
    checks = probes.get('checks')
    results = report.get('check_results')
    need(isinstance(checks, list) and checks and isinstance(results, list) and len(results) == len(checks)
         and len({row.get('id') for row in checks}) == len(checks)
         and len({row.get('id') for row in results}) == len(results), 'Finite request/result coverage is empty or duplicate')
    actual_by_id = {row['id']: row for row in results}
    for check in checks:
        row = actual_by_id.get(check['id'], {})
        need(check.get('kind') in {'wall_aperture_projection', 'ray_intervals', 'support_each', 'measure_part_extents', 'closed_plane_sections'}
             and row.get('kind') == check['kind'] and row.get('passed') is True
             and row.get('state') == 'ACTUAL_FINITE_CHECK', 'Actual finite question is missing, failed or unimplemented')
    carry = report.get('actual_structure_carryforward') or {}
    need(carry.get('all_present_parts_position_identical') is True
         and identity(carry.get('actual_current_asset')) == identity(current)
         and carry.get('source_raw_sha256') == wanted['raw_sha256'], 'Actual per-part position transfer evidence missing')
    baseline = {row['key']: row for row in structure['part_results']}
    comparisons = carry.get('actual_part_comparisons')
    omitted = carry.get('omitted_source_part_keys')
    need(isinstance(comparisons, list) and comparisons and isinstance(omitted, list)
         and len({row.get('key') for row in comparisons}) == len(comparisons)
         and len(set(omitted)) == len(omitted), 'Actual part transfer coverage empty/duplicate')
    present = {row['key'] for row in comparisons}
    need(not present.intersection(omitted) and present.union(omitted) == set(baseline), 'Actual part transfer omitted or added unreported geometry')
    for row in comparisons:
        original = baseline[row['key']]
        need(row.get('triangles') == original['triangles']
             and row.get('actual_oriented_position_sha256') == original['oriented_position_triangles_sha256'], 'Current part triangles differ from independent raw proof')
    for key in omitted:
        value = json.loads(key)
        need(key in probes.get('allowed_omitted_part_keys', [])
             and any(re.search(pattern, value[0]) for pattern in target['lod_policy']['allowed_omission_label_patterns']),
             'Finite proof permits unapproved LOD part deletion')
    if current['sha256'] == wanted['raw_sha256'] or target['lod_policy']['mode'] == 'compression-only':
        need(omitted == [], 'Raw/compression-only proof must preserve every source part')
    need(report.get('model_appearance_accepted') is False and report.get('complete_collision_checked') is False
         and report.get('physical_structural_safety_verified') is False, 'Finite proof improperly expands scope')
    text(report.get('scope'), 'finite actual scope')
    return report


def validate_independent_raw(request, target, package, inputs):
    structure = validate_structure(request, target, package, inputs)
    report = inputs.json(request['independent_raw_review'])
    need('raw' in report.get('asset_identity', {}) and 'asset' not in report.get('asset_identity', {}),
         'Independent raw review must be the actual raw runner report')
    validate_finite(report, package['assets']['raw'], request, target, structure, inputs)
    need(identity(report.get('requests_file')) == identity(target['actual']['probe_set']), 'Independent raw requests differ')
    inputs.file(engine_descriptor(report['requests_file']))
    checkers = report.get('checker_files')
    need(isinstance(checkers, list) and {Path(r.get('file', '')).name for r in checkers}
         == {'modern_mesh.py', 'finite_checks.py', 'run_finite_checks.py'}, 'Exact independent finite checker set required')
    for row in checkers:
        inputs.file(engine_descriptor(row))
    return report, structure


def validate_finite_decoded(decoded, request, target, package, inputs):
    suite = inputs.json(decoded.get('finite_actual_decoded_report'))
    need(suite.get('schema') == 'modern-actual-decoded-finite-suite-v11' and suite.get('passed') is True
         and suite.get('building_id') == target['id'] and suite.get('all_actual_roles_checked') is True
         and suite.get('browser_accepted') is False and suite.get('native_visual_accepted') is False,
         'Unknown, failed or pending actual decoded finite suite')
    need(suite.get('source_geometry_sha256') == request['source_geometry']['sha256']
         and suite.get('raw_sha256') == package['assets']['raw']['sha256']
         and suite.get('source_structure_report') == target['actual']['source_structure_report']
         and suite.get('probe_set') == target['actual']['probe_set'], 'Decoded finite suite source binding differs')
    structure = validate_structure(request, target, package, inputs)
    roles = {'raw', 'web', 'lod'} | ({'authored_lod'} if target['actual'].get('authored_lod') else set())
    need(set(suite.get('roles', {})) == roles and set(decoded.get('actual_decoded_semantic_arrays', {})) == roles,
         'Every actual selected asset must have its own decoded finite report and manifest')
    for name in ('decoder', 'decoder_core', 'bridge'):
        inputs.file(suite.get(name))
    lock_path = inputs.file(suite.get('independent_engine_lock'))
    lock = inputs.json(suite['independent_engine_lock'])
    need(lock.get('schema') == 'modern-independent-finite-engine-lock-v11'
         and lock.get('status') == 'frozen' and lock.get('files'), 'Actual independent engine is not frozen')
    for row in lock['files']:
        inputs.file(row)
        safe_relative(row['local'])
        inputs.file({'source': str(lock_path.parent / row['local']), **identity(row)})
    for role in sorted(roles):
        row = suite['roles'][role]
        current = target['actual']['authored_lod'] if role == 'authored_lod' else package['assets'][role]
        need(row.get('passed') is True and identity(row.get('current_asset')) == identity(current), 'Decoded finite current role differs')
        actual = inputs.json(row['finite_report'])
        need(actual.get('schema') == 'modern-actual-decoded-finite-role-v11' and actual.get('passed') is True
             and actual.get('building_id') == target['id'] and actual.get('role') == role
             and actual.get('browser_accepted') is False and actual.get('native_visual_accepted') is False,
             'Unknown or failed per-role actual decoded finite report')
        need(identity(actual.get('current_asset')) == identity(current)
             and actual.get('array_manifest') == row['array_manifest'] == decoded['actual_decoded_semantic_arrays'][role]
             and actual.get('requests') == target['actual']['probe_set']
             and actual.get('source_structure_report') == target['actual']['source_structure_report']
             and actual.get('bridge') == suite['bridge'] and actual.get('independent_engine_lock') == suite['independent_engine_lock'],
             'Per-role actual decoder/checker/source binding differs')
        manifest = inputs.json(row['array_manifest'])
        need(manifest.get('schema') == 'modern-decoded-semantic-arrays-v11' and manifest.get('building_id') == target['id']
             and manifest.get('role') == role and manifest.get('source_geometry_sha256') == request['source_geometry']['sha256']
             and manifest.get('coordinate_system') == 'ENU metres' and identity(manifest.get('asset')) == identity(current)
             and manifest.get('browser_accepted') is False, 'Actual semantic manifest identity differs')
        need(manifest.get('chunks') and manifest.get('parts')
             and type(manifest.get('chunk_retention', {}).get('persistent')) is bool, 'Actual semantic chunks/retention record missing')
        for chunk in manifest['chunks']:
            identity(chunk)  # Derived buffers may already be deleted after their actual finite checks.
            need(chunk['bytes'] <= 64 * 1024 * 1024 and chunk['bytes'] % 144 == 0, 'Actual semantic chunk shape differs')
        need(sum(c['bytes'] // 144 for c in manifest['chunks']) == manifest.get('triangle_count'), 'Actual chunk triangle coverage differs')
        retention = inputs.json(row['chunk_retention'])
        need(retention.get('schema') == 'modern-decoded-temporary-array-retention-v11'
             and retention.get('role') == role and retention.get('keep_evidence') == manifest['chunk_retention']['persistent']
             and retention.get('no_preexisting_files_removed') is True, 'Actual derived-array retention policy differs')
        finite = actual.get('actual_finite_result')
        need(finite.get('asset_identity', {}).get('raw_indices_reused_for_compressed_asset') is False
             and finite['asset_identity'].get('decoded_array_manifest') == row['array_manifest']
             and finite['asset_identity'].get('temporary_chunks') == manifest['chunks']
             and finite['asset_identity'].get('temporary_chunk_retention') == manifest['chunk_retention'],
             'Actual decoded semantic reconstruction evidence missing')
        validate_finite(finite, current, request, target, structure, inputs)
    return suite
