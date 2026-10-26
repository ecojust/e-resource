#!/usr/bin/env python3
"""Explicit byte-bound source delivery; no generation, installation or acceptance."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTEGRATION = HERE.parent / 'integration-v1'
PROJECT = Path('/workspace/shanghai_project')
PUBLIC = 'source/city/precise-overrides-v11/two-modern-buildings'
IDS = ('jiading-shanghai-auto-museum', 'minhang-baoyugang-library')
MACROS = ('14-13706-6691', '14-13718-6705')
NEIGHBORS = ([735, 797], [35, 60, 299, 333, 375, 466, 947])
LIMIT = 100_000_000


def read(path):
    return json.loads(Path(path).read_bytes())


def meta(path):
    path = Path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'sha256': digest}


def check(path, expected):
    assert meta(path) == {key: expected[key] for key in ('bytes', 'sha256')}, str(path)


def write(name, value):
    path = HERE / name
    assert not path.exists(), 'Refuse to overwrite: ' + str(path)
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    path.write_bytes(data)
    return path


def main():
    rows, destinations = [], set()

    def add(source, destination, purpose):
        source = Path(source).resolve()
        assert destination not in destinations, destination
        assert destination.startswith((PUBLIC + '/', *(f'assets/city-overrides-v6/{m}/' for m in MACROS)))
        assert '..' not in Path(destination).parts and not Path(destination).is_absolute()
        identity = meta(source)
        assert 0 < identity['bytes'] < LIMIT
        if (PROJECT / destination).exists():
            check(PROJECT / destination, identity)
        rows.append({'file': destination, 'source': str(source), **identity, 'purpose': purpose})
        destinations.add(destination)

    def owner(source, relative, purpose):
        add(source, PUBLIC + '/' + relative, purpose)

    baseline = read(INTEGRATION / 'baseline-lock.json')
    for row in baseline['files']:
        check(row['snapshot']['file'], row['snapshot'])
        check(row['original']['file'], row['original'])
    freeze = read(INTEGRATION / 'source-tools-freeze.json')
    for row in freeze['files'] + freeze['upstream_v10_files'] + [freeze['independent_static_review']]:
        check(row['file'], row)
        path = Path(row['file'])
        if path == INTEGRATION / 'README.md':
            relative = 'history/integration-stage-README.md'
        elif path.is_relative_to(INTEGRATION):
            relative = path.relative_to(INTEGRATION).as_posix()
        elif path.name == 'freeze_integration_baseline.py':
            relative = 'tools/freeze_integration_baseline.py'
        else:
            relative = 'evidence/independent-tool-review.json'
        owner(path, relative, 'Exact frozen source tool or its unchanged provenance; historical paths retained')

    explicit = {
        'source-tools-freeze.json': 'source-tools-freeze.json',
        'baseline-lock.json': 'baseline-lock.json',
        'baseline-publication-reference.json': 'baseline-publication-reference.json',
        'runtime-dependency-lock.json': 'runtime-dependency-lock.json',
        'preflight-before-generation.json': 'history/preflight-before-generation.json',
        'preflight-history/attempt1/failure.json': 'history/preflight-attempt1/failure.json',
        'preflight-history/attempt1/preflight.py': 'history/preflight-attempt1/preflight.py',
        'post-generation-preservation.json': 'evidence/post-generation-preservation.json',
        'post-runtime-preservation.json': 'evidence/post-runtime-preservation.json',
        'runtime-handoff.json': 'evidence/runtime-handoff.json',
        'geometry-stage-handoff.json': 'history/geometry-stage-handoff.json',
        'fifteen-targets/precise-buildings-v6.json': 'evidence/precise-buildings-v6.json',
        'fifteen-targets/geometry-validation.json': 'evidence/geometry-validation.json',
        'fifteen-targets/runtime-owner-validation.json': 'evidence/runtime-owner-validation.json',
        'fifteen-targets/composition-report.json': 'evidence/composition-report.json',
        'fifteen-targets/geometry-comparison-input.json': 'evidence/geometry-comparison-input.json',
        'fifteen-targets/asset-files.json': 'evidence/asset-files.json',
        'baseline/project/data/precise-buildings-v6.json': 'history/baseline13-precise-buildings-v6.json',
        'baseline/project/source/city/precise-overrides-v10/two-districts/evidence/geometry-validation.json': 'history/prior13-geometry-validation.json',
    }
    for source, relative in explicit.items():
        owner(INTEGRATION / source, relative, 'Unmodified actual source-stage evidence; scope and historical false flags retained')

    registry = read(INTEGRATION / 'fifteen-targets/precise-buildings-v6.json')
    geometry = read(INTEGRATION / 'fifteen-targets/geometry-validation.json')
    runtime = read(INTEGRATION / 'fifteen-targets/runtime-owner-validation.json')
    assert registry['complete'] and geometry['pass'] and runtime['pass']
    assert registry['validation']['sha256'] == meta(INTEGRATION / 'fifteen-targets/geometry-validation.json')['sha256']
    assert runtime['registry_sha256'] == meta(INTEGRATION / 'fifteen-targets/precise-buildings-v6.json')['sha256']
    assert len(registry['landmarks']) == 15 and len(registry['macros']) == 9
    assert sum(len(m['near']) for m in registry['macros']) == 13
    for ident, value in registry['geometry_inputs'].items():
        path = INTEGRATION / 'inputs' / value['file']
        assert meta(path)['sha256'] == value['sha256']
        owner(path, 'inputs/' + value['file'], 'Exact original owner geometry; never reprojected, clipped or rewritten')
        if value.get('mapping_report'):
            mapping = value['mapping_report']
            path = INTEGRATION / 'inputs' / mapping['file']
            assert meta(path)['sha256'] == mapping['sha256']
            owner(path, 'inputs/' + mapping['file'], 'Original provider identity mapping required by the frozen parser')

    # These are explicit original dependencies frozen before generation, not a directory scan.
    code = {'source/city/build_district_models.py', 'source/city/roof_geometry.py',
            'source/city/detail/geometry_engine.py', 'source/city/detail/requirements.lock'}
    for row in baseline['files']:
        path = Path(row['snapshot']['file'])
        if row['kind'] == 'new_target_original_source':
            relative = path.relative_to(INTEGRATION).as_posix()
            owner(path, relative, 'Frozen two-macro source/near/far dependency; source objects and neighbors preserved')
        elif path.is_relative_to(INTEGRATION / 'baseline/project'):
            relative = path.relative_to(INTEGRATION / 'baseline/project').as_posix()
            if relative in code:
                owner(path, 'baseline/project/' + relative, 'Exact frozen city generation code or dependency lock')

    # Keep only the eleven feature references named by the two actual audit inputs.
    for ident, macro, expected_neighbors in zip(IDS, MACROS, NEIGHBORS):
        fresh = INTEGRATION / 'fresh' / ident
        for name in ('precise-buildings-v6.json', 'precise-buildings-v6.draft.json',
                     'geometry-comparison-input.json', 'geometry-validation.json'):
            owner(fresh / name, f'evidence/fresh/{ident}/{name}', 'Exact actual fresh-near generation/decoder evidence')
        comparison = read(fresh / 'geometry-comparison-input.json')
        assert len(comparison['checks']) == 1
        comparison_row = comparison['checks'][0]
        assert comparison_row['macro_id'] == macro and comparison_row['neighbor_local_ids'] == expected_neighbors
        for reference in comparison_row['references']:
            for key in ('file', 'raw_file'):
                source = Path(reference[key])
                assert source.is_relative_to(fresh / 'work')
                owner(source, f'evidence/fresh/{ident}/references/{source.name}',
                      'Explicit per-feature reference actually used by the geometry audit; city geometry only')

    fresh_assets = [row for row in read(INTEGRATION / 'fifteen-targets/asset-files.json')['files'] if row['fresh_generated']]
    assert len(fresh_assets) == 2
    for row in fresh_assets:
        check(row['source'], row)
        add(row['source'], row['file'], 'Required new near variant; old eleven variants remain existing project assets')

    # All original evidence remains unchanged. This index maps only selected published bytes.
    original_mapping = [{key: row[key] for key in ('source', 'file', 'bytes', 'sha256')} for row in rows]
    external = []
    runtime_lock = read(INTEGRATION / 'runtime-dependency-lock.json')
    for row in runtime_lock['files']:
        check(row['file'], row)
        external.append({'file': Path(row['file']).relative_to(PROJECT).as_posix(),
                         'bytes': row['bytes'], 'sha256': row['sha256'],
                         'delivery': 'existing project dependency, not copied by this manifest'})
    for row in baseline['unchanged_near_variants']:
        check(PROJECT / row['file'], row)
        external.append({**row, 'delivery': 'existing exact old near variant, not regenerated or copied'})
    mapping = write('public-path-mapping.json', {
        'schema': 'v11-owner-source-public-path-mapping-v1',
        'scope': 'Map explicit delivered bytes without rewriting original reports or their absolute paths.',
        'files': original_mapping, 'existing_project_dependencies': external,
        'omissions': [
            'Earlier all-city and old per-feature audit work directories are historical dependencies, not republished here.',
            'The baseline lock records 108 original/snapshot pairs; this delivery is an explicit subset, not a copy of every snapshot.',
            'Historical source-stage handoffs mention earlier navigation work; current raw-bound proposals and model/MVT/browser evidence are delivered separately by the application/model pipeline.',
            'Installed gltfpack is hash-pinned, not redistributed by this delivery; its license and exact files remain identified in external-tool-lock.json.'
        ], 'original_evidence_rewritten': False})
    owner(mapping, 'public-path-mapping.json', 'Explicit original-path to public-byte mapping and existing dependency boundaries')
    owner(HERE / 'README.md', 'README.md', 'Current owner-source scope, historical status distinction, attribution and rebuild instructions')
    owner(Path(__file__), 'delivery/prepare_manifest.py', 'Exact explicit whitelist assembly code; workspace orchestration, not a portable model builder')
    rows.sort(key=lambda row: row['file'])
    manifest = write('source-manifest.json', {
        'schema': 'v11-two-modern-owner-source-delivery-v1',
        'status': 'EXPLICIT_BYTE_BOUND_OWNER_SOURCE_READY_FOR_CANDIDATE',
        'files': rows, 'file_count': len(rows), 'total_bytes': sum(row['bytes'] for row in rows),
        'maximum_file_bytes': max(row['bytes'] for row in rows),
        'counts': {'owners': 15, 'macros': 9, 'near': 13, 'fresh_near': 2, 'reused_near': 11,
                   'source_features': 186, 'retained_neighbors': 171},
        'actual_existing_geometry_report': {'source': str(INTEGRATION / 'fifteen-targets/geometry-validation.json'), **meta(INTEGRATION / 'fifteen-targets/geometry-validation.json')},
        'actual_existing_runtime_report': {'source': str(INTEGRATION / 'fifteen-targets/runtime-owner-validation.json'), **meta(INTEGRATION / 'fifteen-targets/runtime-owner-validation.json')},
        'scope': 'Delivery of already-audited source ownership and new near variants only. Model, navigation, MVT suppression, browser, catalog and publication acceptance are separate.',
        'assembly_checks': {'all_108_original_and_snapshot_hash_pairs_match': True,
                            'source_tool_freeze_unchanged': True,
                            'exact_15_inputs_and_two_original_mapping_reports': True,
                            'new_near_assets_bound': True, 'old11_near_assets_exact': True,
                            'all_files_below_100000000_bytes': True},
        'geometry_or_runtime_rerun': False, 'browser_run': False, 'blender_run': False,
        'main_written': False, 'published_by_this_manifest': False,
        'registration_or_model_acceptance_claimed': False})
    print(json.dumps({'source': str(manifest), **meta(manifest), 'file_count': len(rows),
                      'total_bytes': sum(row['bytes'] for row in rows)}, indent=2))


if __name__ == '__main__':
    main()
