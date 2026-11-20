"""Check the signed, separate city visits and the first third-party outage evidence."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
load = lambda name: json.loads((here / name).read_bytes())
before, first, after = [load(name) for name in (
    'before-control-browser.json', 'initial-main-browser.json', 'recovery-main-browser.json'
)]
assert before['completed'] and before['catalog']['count'] == 158
assert first['catalog'] == after['catalog'] and first['catalog']['count'] == 159
assert not first['completed'] and 'retained neighbor 2040' in first['failure']
assert [p['found'] for p in first['ground'][-4:]] == [None] * 4
assert after['completed'] and after['errors'] == after['failed'] == []
assert after['scriptSha256'] == hashlib.sha256((here / 'check-neighbors-and-lod.cjs').read_bytes()).hexdigest()
assert first['scriptSha256'] == before['scriptSha256']
assert after['bindings'] == first['bindings']
for v in (before, first, after):
    for shot in v['screenshots']:
        data = (here / shot['file']).read_bytes()
        assert len(data) == shot['bytes'] and hashlib.sha256(data).hexdigest() == shot['sha256']
shots = [shot['file'] for q in (before, first, after) for shot in q['screenshots']]
assert shots == ['map-before.png', 'map-mobile.png', 'map-desktop.png', 'map-street-facade.png', 'map-roof.png', 'map-distant.png']
for v in [*first['views'], *after['views']]:
    assert v['glError'] == 0 and not v['contextLost'] and v['labels'] == 159
    assert v['asset']['status'] == 'loaded' and v['asset']['visible']
    assert v['asset']['triangles'] == (82244 if v['view'] == 'map-distant' else 126728)
for v in first['views'][-2:]:
    assert v['group']['clip_feature_local_ids'] == [1602] and v['group']['triangles'] == 5
for p, recovered in zip(first['ground'],after['ground'],strict=True):
    assert [p['name'],p['position'],p['expected']] == [recovered['name'],recovered['position'],recovered['found']]
seen = after['collisionSamples'][-1]
assert len(after['ground']) == 16 and seen['ready']
assert [n['id'] for n in seen['neighbors']] == [2040,473,2236,2318]
assert all(n['vectorFeaturePresent'] for n in seen['neighbors'])
assert len(after['files']) == 6 and sum(f['loadedByScene'] for f in after['files']) == 4
project = here.parents[3]
for f in after['files']:
    if '/candidates/' in f['file']:
        actual = (project / f['file']).read_bytes()
        assert len(actual) == f['bytes'] and hashlib.sha256(actual).hexdigest() == f['sha256']
assert load('external-overture-range.json')['status'] == 503
assert load('external-overture-recovery.json')['status'] == 206
result = dict(catalog=after['catalog'], predecessor=before['catalog'], screenshots=shots,
              comparative_assessment='The first 159-place visit retained all four local landmarks views but the four adjacent ground points returned null during a third-party PMTiles outage. A subsequent visit sampled the exact same coordinates and confirmed all four retained UUIDs in the active Overture vector tile.',
              initial_ground_pass=12, initial_ground_count=16, recovered_ground_pass=16,
              vector_features_in_recovery=seen['overtureFeatureCount'], neighbors=seen['neighbors'],
              web_downloads=after['files'], full_triangles=126728, distant_triangles=82244,
              initial_finished=first['finished'], recovery_finished=after['finished'],
              recovery_browser_errors=len(after['errors']), recovery_failed_requests=len(after['failed']))
(here / 'model-delivery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
