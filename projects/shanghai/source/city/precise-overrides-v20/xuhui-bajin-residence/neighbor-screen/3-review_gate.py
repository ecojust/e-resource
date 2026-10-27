#!/usr/bin/env python3
"""Read-only, fail-closed binding of a real root mesh review to source-owner work.

This module never creates a root review or accepts a model. The caller must obtain
the actual review path and its SHA256 from root after root has reviewed v2.
"""
import hashlib
import json
import re
import shutil
from pathlib import Path

V20 = Path('/workspace/shanghai_expansion/building-by-building-v20')
PREPARATION = V20 / 'integration/bajin-preparation-v1'
FINISH = V20 / 'integration/bajin-finish-v1'
FREEZE = PREPARATION / 'source-owner-input-v1'
OUTPUT = FINISH / 'owner-v1'
MAIN = Path('/workspace/shanghai_project')
MODEL_ROOT = V20 / 'model/bajin-detailed-v2'
FILE_LIMIT = 100_000_000
RESERVE_BYTES = 300_000_000
OWNER_BUDGET_BYTES = 40_000_000
KEEP = [234, 276, 388, 575, 938, 1040, 1327, 1448, 1689, 1828,
        2602, 2974, 3558, 3671, 3828, 3991, 4118]
TARGET = {
    'model_id': 'xuhui-bajin-residence',
    'source_uuid': '7b106e12-e86d-48ad-9d07-888fcebe7f25',
    'source_key': 'building:7b106e12-e86d-48ad-9d07-888fcebe7f25',
    'source_osm_record': 'w582302404@1',
    'macro': '14-13718-6695', 'local_id': 1950,
    'near': '14-13718-6695-1_1-s0-s1',
}
GEOMETRY = {
    'path': str(FREEZE / TARGET['model_id'] / 'geometry-input.json'),
    'bytes': 30553,
    'sha256': '8fd1d49b6ad3adb29ac0216676883bcd5399286abc990b0eb039508e72393f52',
}
ROOT_SOURCE = {
    'path': str(V20 / 'review/root-bajin-source-context-v3.json'),
    'bytes': 4121,
    'sha256': '750337eac7b7adaefa6a787874b75b15f25cb9813d9008ba66b501733acc040d',
}
BASELINE = {
    'path': str(PREPARATION / 'freeze-v1/baseline.json'),
    'bytes': 46551,
    'sha256': 'e7e0ea7530311c844564b1b8a8babfe16eb53c5fc89629544ab60429ca143a3f',
}
OLD_HELPER = {
    'path': str(PREPARATION / 'owner-tools-v1/run_owner.py'),
    'bytes': 8216,
    'sha256': 'f98dc4b83575134f1bbefa682f6427723a79db6d9e17d6d2591c87835b305352',
}
HELD_V1_ASSET_HASHES = {
    '022513062bd7e534531cd07acb72ccd25f5f6ff4b480b5de0c52df95c320fa61',
    'a05c805d5ff8a37c80283c51900b3cfee1801623ad8162511c156acc13acb238',
    '3dc34ee8009333a577342cf8f42df8415ede96ab0dc06dff9d2fefe9ded7c424',
}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha_value(value, label):
    need(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value),
         label + ': expected lowercase SHA256')
    return value


def canonical_path(value, label):
    need(isinstance(value, (str, Path)), label + ': expected path')
    path = Path(value)
    need(path.is_absolute() and str(path) == str(path.resolve()),
         label + ': use a canonical absolute path without symlinks or traversal')
    return path


def descriptor(path):
    # Existing MAIN contains frozen links into the shared all-city source tree.
    # Preserve the legacy reader's resolution semantics here. Supplied review,
    # assets, freeze and output paths are separately required to be canonical.
    path = Path(path).resolve()
    need(path.is_file(), 'Missing regular file: ' + str(path))
    size = path.stat().st_size
    need(0 < size < FILE_LIMIT, 'File must be nonempty and strictly below 100MB: ' + str(path))
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    need(path.stat().st_size == size, 'File size changed while hashing: ' + str(path))
    return {'path': str(path), 'bytes': size, 'sha256': digest.hexdigest()}


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        need(key not in obj, 'Duplicate JSON key: ' + key)
        obj[key] = value
    return obj


def reject_constant(value):
    raise ValueError('Non-finite JSON value: ' + value)


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def check_descriptor(value, label, expected=None):
    need(isinstance(value, dict) and set(value) == {'path', 'bytes', 'sha256'},
         label + ': requires exactly path, bytes and sha256')
    canonical_path(value['path'], label)
    need(type(value['bytes']) is int and 0 < value['bytes'] < FILE_LIMIT,
         label + ': invalid byte count')
    sha_value(value['sha256'], label)
    if expected is not None:
        need(value == expected, label + ': does not bind the pinned frozen input')
    actual = descriptor(value['path'])
    need(actual == value, label + ': actual file descriptor differs')
    return actual


def check_output(output, execute_owner=False):
    path = canonical_path(output, 'output')
    need(path == OUTPUT and not path.exists(),
         'Use only the fresh finish/owner-v1 output; existing output is not reusable')
    required = RESERVE_BYTES + (OWNER_BUDGET_BYTES if execute_owner else 0)
    free = shutil.disk_usage(FINISH).free
    need(free >= required, f'Insufficient free space: need {required}, have {free}')
    return free


def check_invocation(freeze, geometry_sha256, output, execute_owner=False):
    need(canonical_path(freeze, 'freeze') == FREEZE, 'Only the frozen source-owner input is allowed')
    need(sha_value(geometry_sha256, 'geometry-sha256') == GEOMETRY['sha256'],
         'geometry-sha256 differs from the root-frozen source geometry')
    return check_output(output, execute_owner)


def check_review_fields(review):
    need(isinstance(review, dict), 'Root review must be an object')
    required = {
        'schema': 'bajin-root-source-owner-mesh-review-v1',
        'reviewer': '/root',
        'scope': 'source_owner_generation',
        'model_revision': 'bajin-detailed-v2',
        'mesh_accepted_for_integration': True,
        'can_run_source_owner_generation': True,
        'publication_accepted': False,
        'source_pose_changed': False,
    }
    for key, value in required.items():
        need(type(review.get(key)) is type(value) and review.get(key) == value,
             'Root review does not authorize this scope: ' + key)
    for key, value in TARGET.items():
        need(type(review.get(key)) is type(value) and review.get(key) == value,
             'Root review target mismatch: ' + key)
    need(review.get('preserve_same_near_local_ids') == KEEP and
         all(type(x) is int for x in review['preserve_same_near_local_ids']),
         'Root review must retain the exact sorted KEEP17')
    translation = review.get('source_translation_m')
    need(isinstance(translation, list) and len(translation) == 3 and
         all(type(x) in (int, float) and x == 0 for x in translation),
         'Root review must preserve the unshifted source frame')
    need(review.get('architectural_scope') == 'main_house_exterior_only',
         'Root review must exclude annexes, garden, gates and neighbors')
    need(isinstance(review.get('assets'), dict) and
         set(review['assets']) == {'raw', 'lod_raw', 'native'},
         'Root review must bind exactly raw, lod_raw and native; web/candidate acceptance is later')


def check_asset(value, role):
    need(isinstance(value, dict) and 'path' in value, 'Missing asset descriptor: ' + role)
    path = canonical_path(value['path'], role)
    need(path.is_relative_to(MODEL_ROOT), 'Asset must be the actual frozen bajin-detailed-v2 delivery: ' + role)
    suffix = '.blend' if role == 'native' else '.glb'
    need(path.suffix == suffix, 'Wrong asset extension: ' + role)
    actual = check_descriptor(value, 'assets.' + role)
    need(actual['sha256'] not in HELD_V1_ASSET_HASHES,
         'Held detailed-v1 asset cannot be renamed into v2: ' + role)
    with path.open('rb') as handle:
        header = handle.read(12)
    if role == 'native':
        need(header.startswith(b'BLENDER') or header.startswith(b'\x1f\x8b') or
             header.startswith(b'\x28\xb5\x2f\xfd'), 'Native input is not a Blender file')
    else:
        need(header[:4] == b'glTF' and int.from_bytes(header[4:8], 'little') == 2 and
             int.from_bytes(header[8:12], 'little') == actual['bytes'],
             'Raw asset is not a complete GLB 2.0 file: ' + role)
    return actual


def validate_root_review(path, expected_sha256):
    sha_value(expected_sha256, 'root-model-review-sha256')
    path = canonical_path(path, 'root-model-review')
    need(path.is_relative_to(V20 / 'review') and path.suffix == '.json',
         'Actual root review must be a JSON record under V20/review')
    pinned_review = descriptor(path)
    need(pinned_review['sha256'] == expected_sha256, 'Root model review changed')
    review = read(path)
    check_review_fields(review)
    geometry = check_descriptor(review.get('source_geometry_input'), 'source_geometry_input', GEOMETRY)
    root_source = check_descriptor(review.get('root_source_review'), 'root_source_review', ROOT_SOURCE)
    baseline = check_descriptor(BASELINE, 'baseline', BASELINE)
    old_helper = check_descriptor(OLD_HELPER, 'frozen helper', OLD_HELPER)
    source = read(geometry['path'])
    need(source.get('id') == TARGET['model_id'] and
         source.get('source', {}).get('key') == TARGET['source_key'] and
         source['source'].get('overture_id') == TARGET['source_uuid'],
         'Frozen geometry source identity mismatch')
    assets = {role: check_asset(value, role) for role, value in review['assets'].items()}
    paths = [value['path'] for value in assets.values()]
    need(len(set(paths)) == 3 and len({Path(p).stat().st_ino for p in paths}) == 3,
         'Asset roles must refer to distinct actual files')
    need(descriptor(path) == pinned_review, 'Root review changed while checking inputs')
    return {
        'root_model_review': pinned_review,
        'source_geometry_input': geometry,
        'root_source_review': root_source,
        'frozen_baseline': baseline,
        'frozen_helper': old_helper,
        'assets': assets,
        'scope': 'source_owner_generation',
        'publication_accepted': False,
    }


def recheck_binding(binding):
    rows = [binding[k] for k in ('root_model_review', 'source_geometry_input',
            'root_source_review', 'frozen_baseline', 'frozen_helper')]
    rows.extend(binding['assets'].values())
    for row in rows:
        need(descriptor(row['path']) == row, 'Bound input changed: ' + row['path'])
