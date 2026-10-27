#!/usr/bin/env python3
"""Fixed V20 identities and read-only preflight shared by isolated preparation tools."""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
V20 = Path('/workspace/shanghai_expansion/building-by-building-v20')
HERE = V20 / 'integration/bajin-integration-v1'
PREPARATION = V20 / 'integration/bajin-preparation-v1'
FINISH = V20 / 'integration/bajin-finish-v1'
MAIN = Path('/workspace/shanghai_project')
ID = 'xuhui-bajin-residence'
MACRO = '14-13718-6695'
LOCAL = 1950
NEAR = '14-13718-6695-1_1-s0-s1'
KEEP = [234, 276, 388, 575, 938, 1040, 1327, 1448, 1689, 1828,
        2602, 2974, 3558, 3671, 3828, 3991, 4118]
ANCHOR = [121.43606524072175, 31.21051863775041]
PRIOR_IDS = ['xuhui-wukang-129', 'xuhui-wukang-210', 'columbia-country-club',
             'xuhui-wukang-mansion', 'changning-hudec-residence']
BASE_COUNTS = {'navigation': 36, 'owners': 22, 'owner_macros': 13,
               'near_chunks': 20, 'ordinary_records': 17, 'catalog_macros': 12}
FINAL_COUNTS = dict(BASE_COUNTS, navigation=37, owners=23, near_chunks=21, ordinary_records=18)
LIMIT = 100_000_000
RESERVE_BYTES = 300_000_000
GEOMETRY = {'path': str(PREPARATION / 'source-owner-input-v1' / ID / 'geometry-input.json'),
            'bytes': 30553, 'sha256': '8fd1d49b6ad3adb29ac0216676883bcd5399286abc990b0eb039508e72393f52'}
NEIGHBORHOOD = {'path': str(PREPARATION / 'source-neighborhood-v1.json'),
                'bytes': 151432, 'sha256': 'ff8577de1dd14218d5a4bd03a117ed3a04b15bce704baaa9f18bf30396414a3e'}
BASELINE = {'path': str(PREPARATION / 'freeze-v1/baseline.json'),
            'bytes': 46551, 'sha256': 'e7e0ea7530311c844564b1b8a8babfe16eb53c5fc89629544ab60429ca143a3f'}
FINISH_HANDOFF = {'path': str(FINISH / 'HANDOFF.json'), 'bytes': 5286,
                  'sha256': '6a8d0baa0fe213f289791497d87d7b1a92e0ec013cdfc1aa2428035e4267171b'}


def need(value, message):
    if not value:
        raise ValueError(message)


def descriptor(path):
    # Existing MAIN source links are intentionally resolved read-only.
    path = Path(path).resolve()
    size = path.stat().st_size
    need(path.is_file() and 0 < size < LIMIT, 'Missing/empty/oversized input: ' + str(path))
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    need(path.stat().st_size == size, 'Input size changed while hashing: ' + str(path))
    return {'path': str(path), 'bytes': size, 'sha256': h.hexdigest()}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Non-finite JSON value: ' + value)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def verify_descriptor(row):
    need(isinstance(row, dict) and {'path', 'bytes', 'sha256'} <= set(row), 'Actual descriptor required')
    actual = descriptor(row['path'])
    need(all(actual[k] == row[k] for k in ('path', 'bytes', 'sha256')), 'Input descriptor differs: ' + row['path'])
    return actual


def finish_gate():
    verify_descriptor(FINISH_HANDOFF)
    handoff = read(FINISH_HANDOFF['path'])
    row = handoff['files']['review_gate.py']
    verify_descriptor(row)
    spec = importlib.util.spec_from_file_location('bajin_frozen_finish_gate', row['path'])
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate


def validate_root_review(path, sha256):
    return finish_gate().validate_root_review(path, sha256)


def recheck_binding(binding):
    finish_gate().recheck_binding(binding)


def check_frozen_inputs():
    verify_descriptor(GEOMETRY)
    verify_descriptor(NEIGHBORHOOD)
    geometry, neighbors = read(GEOMETRY['path']), read(NEIGHBORHOOD['path'])
    need(geometry['id'] == ID and geometry['anchor'] == ANCHOR and
         geometry['current_city_detail']['feature_local_id'] == LOCAL and
         geometry['current_city_detail']['owner_macro_id'] == MACRO and
         geometry['current_city_detail']['near_owner_id'] == NEAR, 'Frozen target identity/frame differs')
    need(geometry['replacement']['feature_local_ids'] == [LOCAL] and
         geometry['replacement']['retained_same_near_feature_local_ids'] == KEEP, 'Incomplete frozen KEEP17 partition')
    need(neighbors['anchor'] == ANCHOR and neighbors['target_key'] == geometry['source']['key'] and
         len(neighbors['features']) == 80 and neighbors['required_frozen_contextual_feature_count'] == 27,
         'Expected complete frozen 80-feature/required27 context')
    return geometry, neighbors


def check_baseline():
    verify_descriptor(BASELINE)
    lock = read(BASELINE['path'])
    need(lock['root_approved_published_head'] == '3048f6f8a16c1cbd35b7d74c3f0483bcf8e059cc' and
         lock['counts'] == BASE_COUNTS and lock['projected_counts_if_one_complete_model_accepted'] == FINAL_COUNTS,
         'Wrong frozen V19 publication/count baseline')
    need(len(lock['files']) == 154 and len(lock['runtime_files']) == 35, 'Incomplete MAIN/runtime baseline')
    for row in lock['files'] + lock['runtime_files']:
        actual = descriptor(MAIN / row['file'])
        need(all(actual[k] == row[k] for k in ('bytes', 'sha256')), 'Frozen MAIN input changed: ' + row['file'])
    return lock


def fresh_output(path, create=False, budget_bytes=2_000_000):
    supplied = Path(path)
    resolved = supplied.resolve()
    need(supplied.is_absolute() and str(supplied) == str(resolved) and
         resolved.is_relative_to(HERE) and resolved != HERE and not resolved.exists(),
         'Output must be a fresh canonical child of bajin-integration-v1')
    need(type(budget_bytes) is int and 0 < budget_bytes < LIMIT, 'Invalid output budget')
    need(shutil.disk_usage(HERE).free >= RESERVE_BYTES + budget_bytes,
         'Insufficient space to preserve 300MB after the bounded output')
    if create:
        resolved.mkdir(parents=True)
    return resolved


def check_owner_binding(owner, binding):
    need(Path(owner).resolve() == FINISH / 'owner-v1', 'Use only the future bound finish/owner-v1')
    proof = read(Path(owner) / 'generation-provenance.json')
    need(proof.get('passed') is True and proof.get('source_owner_only') is True and
         proof.get('source_geometry') == GEOMETRY and
         proof.get('root_source_owner_authorization') == binding and
         proof.get('main_watched_before_after_equal') is True,
         'Owner generation must bind the same actual root review and exact source geometry')
    for row in (proof['generated_registry'], proof['geometry_validation']):
        verify_descriptor(row)
    recheck_binding(binding)
    return proof
