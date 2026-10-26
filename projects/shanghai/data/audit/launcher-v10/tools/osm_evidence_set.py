"""Byte-bound actual OSM fixtures per target; no observations or browser run."""
from pathlib import Path
import hashlib
import json
import math
import re


def need(ok, message):
    if not ok:
        raise ValueError(message)


def meta(path):
    path = Path(path)
    body = path.read_bytes()
    return {'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}


def pending(target):
    return {'schema': 'actual-osm-component-qa-pending-v1',
            'landmark_id': target, 'source_id': None, 'geometry': None}


def read_fixture(path, target):
    if path is None:
        return pending(target)
    path = Path(path)
    need(path.is_file() and path.stat().st_size < 8_000_000, 'Actual fixture file missing or oversized')
    evidence = json.loads(path.read_bytes())
    need(evidence.get('schema') == 'actual-osm-component-qa-v1'
         and evidence.get('landmark_id') == target, 'Fixture is pending or belongs to another target')
    identity = evidence.get('source_id')
    need((type(identity) is int and abs(identity) <= 9007199254740991)
         or (isinstance(identity, str) and bool(identity)), 'Unsafe or missing actual OSM source ID')
    geometry = evidence.get('geometry') or {}
    need(evidence.get('source_layer') == 'building' and geometry.get('type') == 'Polygon',
         'Actual complete source Polygon/building layer required')
    rings = geometry.get('coordinates')
    need(isinstance(rings, list) and rings, 'Actual source polygon coordinates missing')
    for ring in rings:
        need(isinstance(ring, list) and len(ring) >= 4 and ring[0] == ring[-1],
             'Actual source ring must remain closed and complete')
        need(all(isinstance(point, list) and len(point) == 2
                 and all(type(n) in (int, float) and math.isfinite(n) for n in point)
                 for point in ring), 'Actual source coordinates must be finite XY pairs')
        need(len({tuple(point) for point in ring[:-1]}) >= 3, 'Degenerate actual source ring')
    need(isinstance(evidence.get('origin'), str) and evidence['origin'].strip(),
         'Actual source observation provenance missing')
    return evidence


def read_fixture_set(path, targets):
    """Return target-specific evidence and exact descriptors, or pending values."""
    need(targets and len(targets) == len(set(targets)), 'Distinct explicit targets required')
    if path is None:
        return ({target: pending(target) for target in targets},
                {'set': None, 'targets': {target: None for target in targets}})
    path = Path(path).resolve()
    need(path.is_file() and path.stat().st_size < 8_000_000, 'Fixture set missing or oversized')
    document = json.loads(path.read_bytes())
    need(document.get('schema') == 'actual-osm-component-set-qa-v1'
         and document.get('inputs_ready') is True, 'Actual per-target fixture set is pending')
    rows = document.get('targets')
    need(isinstance(rows, dict) and set(rows) == set(targets), 'Fixture target set differs from actual selected targets')
    evidence, descriptors = {}, {}
    for target in targets:
        row = rows[target]
        need(isinstance(row, dict) and isinstance(row.get('source'), str)
             and type(row.get('bytes')) is int and 0 < row['bytes'] < 8_000_000
             and isinstance(row.get('sha256'), str)
             and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'Missing actual target fixture descriptor')
        source = Path(row['source'])
        source = (path.parent / source).resolve() if not source.is_absolute() else source.resolve()
        need(meta(source) == {key: row[key] for key in ('bytes', 'sha256')},
             'Target fixture bytes/SHA differ: ' + target)
        evidence[target] = read_fixture(source, target)
        descriptors[target] = {'source': str(source), **meta(source)}
    return evidence, {'set': {'source': str(path), **meta(path)}, 'targets': descriptors}


def capture_names(targets):
    return [target + suffix for target in targets for suffix in
            ('-walk-full', '-windows-oblique', '-distant-lod', '-returned-full')] + [
                'precise-owners-released', 'precise-owners-returned', 'after-city-manifest-reset']


def near_capture_names(targets, target):
    need(target in targets, 'Target absent from actual tested order')
    names = {target + suffix for suffix in ('-walk-full', '-windows-oblique', '-returned-full')}
    if target == targets[-1]:
        names.update(('precise-owners-returned', 'after-city-manifest-reset'))
    return names
