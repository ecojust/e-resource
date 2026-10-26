"""Bind real modern registrar outputs; pending assets never become candidates."""
from pathlib import Path
import hashlib
import json


def need(value, message):
    if not value:
        raise ValueError(message)


def identity(value):
    return {key: value[key] for key in ('bytes', 'sha256')}


def actual(value):
    need(isinstance(value, dict) and isinstance(value.get('source'), str), 'Actual modern proof remains pending')
    path = Path(value['source'])
    need(path.is_file() and 0 < path.stat().st_size < 100_000_000, 'Missing or oversized modern proof')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    need({'bytes': path.stat().st_size, 'sha256': digest} == identity(value), 'Modern proof bytes changed')
    return path


def read(value):
    return json.loads(actual(value).read_bytes())


def check_public_set(delivery, public):
    def file_set(document):
        rows = document.get('files', [])
        values = {item['file']: identity(item) for item in rows}
        need(len(values) == len(rows) > 0, 'Distinct actual public source files required')
        return values
    need(file_set(delivery) == file_set(public),
         'Public source publication must exactly match the licensed modern registrar delivery file/bytes/SHA set')


def check_museum_supplement_transfer(transfer, summary_transfer, request, target, package, decoded, suite):
    need(transfer == summary_transfer and isinstance(transfer, dict)
         and transfer.get('schema') == 'modern-museum-supplement-delivery-transfer-v11',
         'Actual Museum supplemental transfer must be identical in metadata and summary')
    for flag in ('bounded_revision_proof_bound_as_raw_history', 'finite_area_pane_seating_preserved',
                 'repair_envelope_and_slot_clearance_preserved', 'all_current_parts_preserved'):
        need(transfer.get(flag) is True, 'Actual Museum supplemental geometry missing: ' + flag)
    names = {'bounded_revision_preservation', 'repair_envelope', 'finite_area_pane_seating', 'all_opaque_slot_rays'}
    proofs = transfer.get('raw_proofs')
    need(isinstance(proofs, dict) and set(proofs) == names
         and proofs == target.get('actual', {}).get('geometry_supplements'),
         'Exact four current Museum raw supplemental proof descriptors required')
    need(transfer.get('source_raw') == package['assets']['raw']
         and transfer.get('source_freeze') == request['source_freeze']
         and transfer.get('source_structure_report') == target['actual']['source_structure_report']
         and transfer.get('actual_decoded_package_report') == request['decoded_report']
         and transfer.get('actual_decoded_finite_suite') == decoded['finite_actual_decoded_report'],
         'Museum supplemental raw/source/structure/decoded bindings differ')
    need(target.get('id') == 'jiading-shanghai-auto-museum'
         and target.get('lod_policy', {}).get('mode') == 'compression-only'
         and target['actual'].get('authored_lod') is None
         and decoded.get('authored_lod') is None and decoded.get('passed') is True
         and suite.get('schema') == 'modern-actual-decoded-finite-suite-v11'
         and suite.get('passed') is True and suite.get('building_id') == target['id']
         and suite.get('raw_sha256') == package['assets']['raw']['sha256']
         and set(suite.get('roles', {})) == {'raw', 'web', 'lod'},
         'Actual Museum original single-suite compression-only roles required')
    roles = transfer.get('roles')
    need(isinstance(roles, dict) and set(roles) == {'raw', 'web', 'lod'},
         'Museum transfer must cover exactly raw/web/LOD')
    for role, row in roles.items():
        finite = suite['roles'][role]
        need(row.get('current_asset') == package['assets'][role]
             and row.get('actual_decoded_finite_report') == finite.get('finite_report')
             and row.get('actual_decoded_array_manifest') == finite.get('array_manifest')
             and finite.get('passed') is True
             and identity(finite['current_asset']) == identity(package['assets'][role])
             and type(row.get('required_retained_part_count')) is int
             and row['required_retained_part_count'] == 12378
             and row.get('exact_oriented_positions_preserved') is True
             and row.get('actual_loaded_materials_preserved') is True
             and type(row.get('normal_policy_degrees')) in (int, float)
             and row['normal_policy_degrees'] == .05
             and row.get('omitted_source_part_keys') == []
             and row.get('raw_supplement_proofs') == proofs,
             'Museum actual delivery role lost protected geometry or evidence: ' + role)
    need(transfer.get('native_accepted') is False and transfer.get('browser_accepted') is False,
         'Museum geometric proof transfer cannot assert native/browser acceptance')


def verify_modern_model(model, ident, declaration, row, nav, package, metadata):
    lock = read(model.get('modern_registration_input_lock'))
    delivery = read(model.get('registration_delivery_manifest'))
    summary_descriptor = model.get('prebrowser_summary')
    summary = read(summary_descriptor)
    need(lock.get('schema') == 'modern-registration-actual-input-lock-v11'
         and lock.get('browser_accepted') is False and lock.get('registered') is False
         and lock.get('installed') is False, 'Actual model-only modern input lock required')
    need(lock.get('files') and lock.get('outputs'), 'Complete immutable modern registrar inputs/outputs required')
    for descriptor in lock['files'] + lock['outputs']:
        actual(descriptor)
    for key in ('registration_input', 'model_metadata', 'registration_delivery_manifest', 'prebrowser_summary'):
        need(model[key] in lock['outputs'], 'Modern output missing from actual input lock: ' + key)
    request = read(lock['request'])
    need(request.get('tool_source_freeze') == model.get('modern_tool_source_freeze'),
         'Modern registrar/package/decoder must use the explicitly selected immutable tool freeze')
    tool_freeze = read(model.get('modern_tool_source_freeze'))
    bound_inputs = {str(Path(item['source']).resolve()): identity(item) for item in lock['files']}
    need(len(bound_inputs) == len(lock['files']), 'Duplicate modern actual input lock source')
    for item in tool_freeze['files']:
        actual(item)
        need(bound_inputs.get(str(Path(item['source']).resolve())) == identity(item),
             'Reviewed modern tool dependency was not bound by actual registration')
    need(delivery.get('schema') == 'modern-model-stage-delivery-manifest-v11'
         and delivery.get('building_id') == ident and delivery.get('request') == lock['request']
         and delivery.get('registration') == model['registration_input']
         and delivery.get('metadata') == model['model_metadata']
         and delivery.get('model_asset_count') == 4 and delivery.get('browser_accepted') is False,
         'Modern registration delivery binding differs')
    need(metadata.get('schema') == 'modern-actual-model-metadata-v11'
         and metadata.get('native_visual_passed') is True and metadata.get('height_is_measured') is False
         and metadata.get('browser_accepted') is False
         and metadata.get('package') == model['package']
         and metadata.get('source_geometry') == request.get('source_geometry'),
         'Actual modern native/height/package/source binding differs')
    need(summary.get('schema') == 'modern-prebrowser-acceptance-summary-v11'
         and summary.get('building_id') == ident and summary.get('prebrowser_scope_passed') is True
         and summary.get('browser_accepted') is False and summary.get('request') == lock['request']
         and summary.get('raw_sha256') == package['assets']['raw']['sha256'],
         'Actual modern prebrowser summary required')
    need(nav.get('schema') == 'modern-source-bound-navigation-proposal-v11'
         and nav.get('building_id') == ident and nav.get('status') == 'ready'
         and nav.get('browser_accepted') is False
         and nav.get('source_geometry_sha256') == row['geometry_input_sha256']
         and nav.get('raw_sha256') == row['assets']['raw']['sha256']
         and nav.get('anchor') == row['anchor']
         and declaration.get('navigation_evidence') == model['navigation_input'],
         'Navigation must bind actual current raw/source and modern ready proposal')
    need(request.get('navigation') == model['navigation_input']
         and request.get('package_record') == model['package'], 'Registration request inputs differ')
    public = read(model.get('model_source_delivery_manifest'))
    check_public_set(delivery, public)
    if ident == 'jiading-shanghai-auto-museum':
        target = read(request.get('target_spec'))
        decoded = read(request.get('decoded_report'))
        suite = read(decoded.get('finite_actual_decoded_report'))
        check_museum_supplement_transfer(metadata.get('geometry_supplement_transfer'),
            summary.get('geometry_supplement_transfer'), request, target, package, decoded, suite)
    if ident == 'minhang-baoyugang-library':
        transfer = metadata.get('geometry_supplement_transfer') or {}
        need(transfer == summary.get('geometry_supplement_transfer')
             and transfer.get('schema') == 'modern-library-supplement-delivery-transfer-v11'
             and transfer.get('pane_seating_and_cap_clearance_preserved') is True
             and transfer.get('bounded_revision_proof_bound_as_raw_history') is True
             and {'raw', 'web', 'lod'}.issubset(transfer.get('roles', {}))
             and transfer.get('native_accepted') is False and transfer.get('browser_accepted') is False,
             'Actual Library265/2988,788pane and6cap supplemental transfer bindings required')
