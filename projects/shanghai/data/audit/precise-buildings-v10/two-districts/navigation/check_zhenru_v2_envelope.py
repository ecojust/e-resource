#!/usr/bin/env python3
"""Read actual stored raw positions; bind the unchanged observer proposal only."""
import hashlib
import json
import mmap
from pathlib import Path
import struct
import numpy as np

V10 = Path(__file__).resolve().parent.parent
RUN = V10 / 'zhenru-main-hall/run-geometry-v2'
NAV = V10 / 'two-district-integration/navigation-proposals/putuo-zhenru-main-hall.json'
OUT = V10 / 'two-district-integration/navigation/zhenru-actual-raw-envelope-v2.json'

def descriptor(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'source': str(path), 'bytes': path.stat().st_size, 'sha256': sha}

def checked(value):
    actual = descriptor(value['source'])
    assert actual == value, (actual, value)
    return Path(actual['source'])

assert not OUT.exists(), 'Write a new report only'
registration = json.loads((RUN / 'registration.draft.json').read_bytes())['buildings'][0]
proposal = json.loads(NAV.read_bytes())
nav_descriptor = descriptor(NAV)
assert nav_descriptor['sha256'] == '79024eb60138b349164b3545226cf8225dafe6461085a9bde3f6ee96176cf84e'
assert registration['navigation'] == proposal['navigation']
metadata = json.loads((RUN / 'model-metadata.json').read_bytes())
raw = registration['assets']['raw']
path = checked({key: raw[key] for key in ('source', 'bytes', 'sha256')})
assert raw['sha256'] == 'c5197dc5cf3e4073c4d3ad0b3b237b4b476ad3e5ff3cc6c65421abb79983b3b9'
assert metadata['raw']['sha256'] == raw['sha256']
source_check_path = checked(proposal['source_observation_checks'])
source_check = json.loads(source_check_path.read_bytes())
checked(source_check['controller'])
checked(proposal['geometry_input'])
low, high, vertices = np.full(3, np.inf), np.full(3, -np.inf), 0
with path.open('rb') as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as buf:
    magic, version, length = struct.unpack_from('<III', buf, 0)
    assert (magic, version, length) == (0x46546c67, 2, len(buf))
    n, kind = struct.unpack_from('<II', buf, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(buf[20:20+n])
    bin_length, bin_kind = struct.unpack_from('<II', buf, 20+n)
    assert bin_kind == 0x004e4942 and 28+n+bin_length == len(buf)
    assert all(not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale')) for node in doc['nodes'])
    accessors = {primitive['attributes']['POSITION'] for mesh in doc['meshes'] for primitive in mesh['primitives']}
    for index in sorted(accessors):
        accessor = doc['accessors'][index]
        view = doc['bufferViews'][accessor['bufferView']]
        assert accessor['componentType'] == 5126 and accessor['type'] == 'VEC3'
        assert not accessor.get('sparse') and not accessor.get('normalized') and not view.get('extensions')
        assert view.get('buffer', 0) == 0
        offset = 28+n+view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
        arr = np.ndarray((accessor['count'], 3), dtype='<f4', buffer=buf, offset=offset,
                         strides=(view.get('byteStride', 12), 4))
        assert np.isfinite(arr).all()
        low = np.minimum(low, arr.min(axis=0))
        high = np.maximum(high, arr.max(axis=0))
        vertices += len(arr)
        del arr
enu_low = [float(low[0]), float(-high[2]), float(low[1])]
enu_high = [float(high[0]), float(-low[2]), float(high[1])]
half_width = proposal['model_envelope_estimate']['half_width_m']
assert half_width == 10.2
assert all(-half_width <= coordinate <= half_width for corner in (enu_low, enu_high) for coordinate in corner[:2])
assert enu_low[2] == metadata['ground_base_m'] == 0
assert enu_high[2] == metadata['height_estimate_m'] == registration['height']['metres']
assert registration['height']['estimated'] and not metadata['height_measured']
assert source_check['shortest_arm_finite_2d_clear'] and not source_check['full_14m_arm_clear']
assert not source_check['automatic_shortening_observed_in_browser']
assert source_check['steps'][-1]['distance_m'] == 3.5
assert source_check['steps'][-1]['minimum_arm_distance_to_neighbor_m'] > 0
report = {
    'schema': 'v10-actual-raw-navigation-envelope-v2', 'id': registration['id'], 'passed': True,
    'raw': descriptor(path), 'registration': descriptor(RUN / 'registration.draft.json'),
    'model_metadata': descriptor(RUN / 'model-metadata.json'),
    'source_freeze': descriptor(V10 / 'zhenru-main-hall/geometry-v2/source-freeze.json'),
    'navigation_proposal': nav_descriptor, 'source_observation_checks': descriptor(source_check_path),
    'checker': descriptor(__file__), 'actual_stored_position_vertices_read': vertices,
    'unique_position_accessors_read': len(accessors), 'node_transforms_absent': True,
    'actual_untransformed_raw_enu_bounds_m': [enu_low, enu_high],
    'proposed_conservative_enu_square_half_width_m': half_width,
    'fits_proposed_horizontal_envelope': True,
    'actual_serialized_height_estimate_m': enu_high[2],
    'navigation_identical_to_final_registration': True,
    'unchanged_controller_sha256': source_check['controller']['sha256'],
    'full_14m_arm_source_clear': False, 'shortest_source_replay_arm_m': 3.5,
    'shortest_source_replay_minimum_neighbor_clearance_m': source_check['steps'][-1]['minimum_arm_distance_to_neighbor_m'],
    'scope': 'Independent actual geometry-v2 Float32 POSITION read across every raw primitive, verifying unchanged conservative horizontal envelope and exact navigation/height bindings. Historical source-footprint clearance is finite 2D evidence only. Tianwang Hall remains preserved. The controller still must actually shorten and produce an acceptable front view in root browser QA.',
    'limitations': ['No public-access or entrance certification.', 'No complete collision-freedom, structural, visual, or browser acceptance is inferred from this envelope check.', 'Actual height is a reconstruction estimate, not a surveyed or officially published total height.'],
    'browser_passed': False, 'automatic_shortening_observed_in_browser': False,
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print(json.dumps(descriptor(OUT), indent=2))
print(json.dumps({'bounds': [enu_low, enu_high], 'vertices': vertices}, indent=2))
