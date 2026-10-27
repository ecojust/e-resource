"""Exact one-file runtime exception; original 31-file MAIN guard stays intact."""
from pathlib import Path
import copy
import hashlib
import json

HERE = Path(__file__).resolve().parent
INTEGRATION = HERE.parent
V12 = INTEGRATION.parent
FILE = 'src/map-scene.js'
BEFORE = {'bytes': 52958, 'sha256': '5b9fa5902e1648106d12c3b5c000ef36a1d43bb400fc86db261ef2c12e4710d2'}
AFTER = {'bytes': 53169, 'sha256': 'aa1b37016754bbe288f17447db20401e077de6f2e05efccbcce18c8fe886c0d7'}
BASELINE = {'source': '/workspace/shanghai_expansion/building-by-building-v11/integration-modern-app-preparation-per-model-v2/runtime-baseline.json',
            'bytes': 5267, 'sha256': '139c5291e476029c2a11ef3523985140722a87a210fabc69b327d77a7e223b39'}


def need(value, message):
    if not value:
        raise ValueError(message)


def meta(path):
    path = Path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'sha256': digest}


def descriptor(path):
    return {'source': str(Path(path).resolve()), **meta(path)}


def identity(value):
    need(isinstance(value, dict), 'Actual runtime descriptor required')
    return {key: value[key] for key in ('bytes', 'sha256')}


def actual(value):
    path = Path(value['source'])
    need(path.is_absolute() and path.is_file() and 0 < value['bytes'] < 100_000_000
         and meta(path) == identity(value), 'Runtime evidence bytes differ: ' + str(path))
    return path


def read(value):
    return json.loads(actual(value).read_bytes())


def effective_from(delta):
    baseline = read(BASELINE)
    need(baseline.get('schema') == 'modern-app-immutable-runtime-baseline-v11'
         and baseline.get('file_count') == len(baseline.get('files', [])) == 31,
         'Original complete 31-file runtime baseline required')
    rows = copy.deepcopy(baseline['files'])
    need(len({row['file'] for row in rows}) == 31, 'Duplicate original runtime file')
    selected = [row for row in rows if row['file'] == FILE]
    need(len(selected) == 1 and identity(selected[0]) == BEFORE, 'Original map-scene preimage differs')
    selected[0].update(AFTER)
    return rows


def check_vendor(value, delta):
    proof = read(value)
    need(proof.get('schema') == 'sihang-empty-filter-tiny-counterexample-v1'
         and proof.get('passed') is True and proof.get('full_page_acceptance') is False
         and proof.get('main_changed') is False and not proof.get('error')
         and proof.get('page_errors') == [], 'Actual passing vendored counterexample required')
    prep_desc = proof.get('preparation') or {}
    prep = read({'source': prep_desc.get('path'), **identity(prep_desc)})
    need(identity(prep['baseline']) == BEFORE and identity(prep['candidate']) == AFTER,
         'Vendor counterexample tested different before/after source')
    for key in ('baseline', 'candidate', 'vendor', 'vendor_css', 'fixture', 'actual_osm_snapshot'):
        row = prep[key]
        actual({'source': row['path'], **identity(row)})
    need(Path(prep['candidate']['path']).resolve() == Path(delta['files'][0]['source']).resolve(),
         'Vendor tested another candidate payload')
    for key in ('script', 'browser_check'):
        row = proof[key]
        actual({'source': row['path'], **identity(row)})
    served = proof.get('actual_served_vendor', [])
    need(len(served) == 2 and [identity(row) for row in served]
         == [identity(prep[key]) for key in ('vendor', 'vendor_css')], 'Actual served vendor bytes differ')
    check = proof.get('check') or {}
    results = check.get('results', [])
    need(check.get('passed') is True and [row.get('name') for row in results] == ['before', 'candidate'],
         'Actual baseline/candidate comparison required')
    labels = ['empty-1', 'empty-2', 'empty-3', 'filter-first', 'repeat-real-filter',
              'change-real-filter', 'clear-real-filter', 'empty-after-clear']
    ids = sorted(prep['fixture_ids'])
    for result in results:
        need(result.get('passed') is True and result.get('errors') == []
             and result.get('actualSourceType') == 'geojson'
             and [row['label'] for row in result['stages']] == labels, 'Complete actual eight-stage vendor evidence required')
        for stage in result['stages']:
            label = stage['label']
            reload_expected = label in ('filter-first', 'change-real-filter', 'clear-real-filter')
            if label.startswith('empty-'):
                reload_expected = result['name'] == 'before'
            need((stage['reloads'] > 0) if reload_expected else stage['reloads'] == 0,
                 'Actual vendor reload outcome differs: ' + label)
            visible = [ids[0]] if label in ('filter-first', 'repeat-real-filter') else [ids[1]] if label == 'change-real-filter' else ids
            final = stage['final']
            need(final['sourceLoaded'] is True and final['tilesLoaded'] is True and final['visibleIds'] == visible,
                 'Actual vendor visible/source-ready outcome differs: ' + label)
    return proof


def load_inputs():
    path = HERE / 'runtime-inputs.actual.json'
    need(path.is_file(), 'Actual vendor counterexample and root runtime review are pending')
    inputs = json.loads(path.read_bytes())
    need(inputs.get('schema') == 'sihang-reviewed-runtime-inputs-v12'
         and inputs.get('status') == 'ACTUAL_ROOT_REVIEW_READY_BROWSER_PENDING', 'Pending runtime input cannot authorize a candidate')
    delta = read(inputs['manifest'])
    need(actual(inputs['manifest']).resolve() == HERE / 'runtime-delta.proposal.json'
         and delta.get('schema') == 'sihang-one-file-runtime-delta-v12'
         and delta.get('original_runtime_baseline') == BASELINE
         and delta.get('browser_accepted') is False, 'Wrong original runtime delta/baseline')
    rows = delta.get('files', [])
    need(len(rows) == 1 and rows[0]['file'] == FILE and rows[0]['before'] == BEFORE
         and rows[0]['after'] == AFTER, 'Only exact reviewed map-scene before/after is permitted')
    actual({'source': rows[0]['source'], **AFTER})
    actual(delta['source_patch'])
    need(Path(rows[0]['source']).resolve() == V12 / 'runtime-fix-preparation/candidate/src/map-scene.js',
         'Runtime payload is outside reviewed candidate location')
    effective = read(inputs['effective_runtime_baseline'])
    need(effective.get('schema') == 'modern-app-immutable-runtime-baseline-v11'
         and effective.get('file_count') == 31 and effective.get('files') == effective_from(delta)
         and effective.get('original_runtime_baseline') == BASELINE
         and effective.get('reviewed_runtime_delta') == inputs['manifest'], 'Effective runtime must change exactly one of 31 files')
    check_vendor(inputs['vendor_evidence'], delta)
    review = read(inputs['root_review'])
    need(review.get('schema') == 'sihang-root-one-file-runtime-review-v12'
         and review.get('reviewer') == 'root' and review.get('passed') is True
         and review.get('final') is True and review.get('actually_reviewed') is True
         and review.get('file') == FILE and review.get('before') == BEFORE and review.get('after') == AFTER
         and review.get('runtime_delta_sha256') == inputs['manifest']['sha256']
         and review.get('vendor_report_sha256') == inputs['vendor_evidence']['sha256']
         and review.get('runtime_file_sha256') == AFTER['sha256'] and review.get('browser_accepted') is False
         and review.get('scope') and review.get('limitations'), 'Root actual exact runtime review required')
    return inputs, delta, effective


def effective_runtime():
    return load_inputs()[2]


def evidence_record():
    inputs, delta, _ = load_inputs()
    return {**{key: inputs[key] for key in ('manifest', 'root_review', 'vendor_evidence', 'effective_runtime_baseline')},
            'file': FILE, 'before': BEFORE, 'after': AFTER, 'original_runtime_baseline': BASELINE,
            'scope': delta['scope']}


def check_tree(project, rows):
    project = Path(project).resolve()
    expected = {row['file']: row for row in rows}
    names = {path.relative_to(project).as_posix() for path in (project / 'src').rglob('*') if path.is_file()}
    need(len(expected) == 31 and names == set(expected), 'Actual runtime inventory must remain exactly 31 files')
    for name, row in expected.items():
        need(meta(project / name) == identity(row), 'Unauthorized runtime bytes: ' + name)


def check_main(project):
    load_inputs()
    check_tree(project, read(BASELINE)['files'])


def check_candidate(project):
    check_tree(project, effective_runtime()['files'])


def plan_entry(project):
    check_main(project)
    row = load_inputs()[1]['files'][0]
    return {'file': FILE, 'source': row['source'], **AFTER, 'old_main': BEFORE}


def check_visual(visual):
    evidence = evidence_record()
    need(visual.get('reviewed_runtime_delta_sha256') == evidence['manifest']['sha256']
         and visual.get('runtime_file_sha256') == AFTER['sha256'], 'Actual root image review must bind the one runtime delta')


def add_files(output, public):
    inputs, delta, _ = load_inputs()
    output.add(FILE, source=delta['files'][0]['source'])
    for name, value in [('runtime-delta.json', inputs['manifest']), ('root-review.json', inputs['root_review']),
                        ('vendor-counterexample.json', inputs['vendor_evidence']),
                        ('effective-runtime31.json', inputs['effective_runtime_baseline']),
                        ('original-runtime31.json', BASELINE), ('source.patch', delta['source_patch']),
                        ('runtime-inputs.json', descriptor(HERE / 'runtime-inputs.actual.json')),
                        ('runtime_delta.py', descriptor(__file__))]:
        output.add(public + '/runtime-fix/' + name, source=actual(value))
