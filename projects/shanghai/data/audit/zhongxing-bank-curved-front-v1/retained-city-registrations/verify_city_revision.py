"""Verify the field-tested Zhongxing Bank release and separately verify the retained city registrations."""
import gzip
import hashlib
import json

def verify(read, audit, original, expected_camera, canonical):
    folder = audit + '/retained-city-registrations/'
    def sha(body):
        return hashlib.sha256(body).hexdigest()
    def archived(name):
        return gzip.decompress(read(folder + name + '.gz'))
    release = json.loads(read(folder + 'verified.json'))
    baseline_body = archived('historical-published-snapshot.json')
    assert sha(baseline_body) == release['original_publication'] == 'c2f50580b84cb7f1f59d2acef57e2b5d4dd54513ba41b41d60630a6cfe37bccd'
    old = json.loads(baseline_body)
    raw = json.loads(archived('historical-31-production.json'))
    assert canonical(raw) == canonical(original)
    assert old['resulting_count'] == raw['resulting_count'] == 319
    streams = json.loads(read(folder + 'layer-checks.json'))
    assert set(map(int, streams)) == {15,*range(17,29),31}
    for level, row in streams.items():
        restored = archived(level + '-284-production.json')
        assert sha(restored) == row['new']
        assert json.loads(restored)['resulting_count'] == row['records']
    if release['city_entries'] == 321:
        observations = archived('840-per-layer-http.json')
        assert sha(observations) == '6fef8282120671f771319d41ad5e1a02b3792223f38ab28f6210b6cc5071a8b0'
        trace = json.loads(observations)
        assert set(trace['layers']) == set(streams) and trace['master'] == release['parent'] == '21478cf5bb67d53ecffcb35407c618a519e0ebb5'
        count = 0
        for level, row in streams.items():
            saved = json.loads(archived(level + '-284-production.json'))['files']
            group = trace['layers'][level]
            assert group['end'] == row['new'] and group['old'] == row['accepted_320'] and group['historical'] == row['original']
            assert group['previous_catalog_sha256'] == row['previous_catalog']
            assert len(group['records']) == 189
            for path, sample in group['records'].items():
                assert sample['http'] == [200, 200, 206] and sample['after'] == saved[path]
                count += len(sample['http'])
        assert count == trace['requests'] == 7938
    measured = json.loads(archived('31-284-production.json'))
    assert sha(canonical(measured)) == release['measured_snapshot']
    final = dict(old, files=measured['files'].copy(), resulting_count=measured['resulting_count'], previous_catalog_sha256=measured['previous_catalog_sha256'])
    for key, updated in release['publication_inputs'].items():
        assert updated['measured'] == measured['files'].get(key)
        final['files'][key] = updated['published']
        if key != 'data/model-todo/queue.json':
            assert sha(read(key)) == updated['published'], key
    assert canonical(final) == read(audit + '/production-snapshot.json')
    assert sha(canonical(final)) == release['published_snapshot']
    catalog = json.loads(read('data/candidate-city-integrations.json'))
    static = json.loads(read('data/landmarks.json'))
    assert final['files']['data/candidate-city-integrations.json'] == sha(canonical(catalog))
    assert len(static) == catalog['existing_city_count'] == 41
    assert len({row['id'] for row in static + catalog['models']}) == catalog['resulting_city_count'] == final['resulting_count']
    assert len([row for row in static if row.get('walkStart')]) == 40
    assert catalog['models'][-1]['id'] == 'huangpu-zhongxing-bank-curved-front'
    assert len(json.loads(read('data/model-todo/standalone-heritage-models.json'))['records']) == release['registered_heritage_models']
    confirmed = expected_camera.copy()
    for key in confirmed:
        assert confirmed[key] == raw['files'][key], key
        confirmed[key] = final['files'][key]
        assert sha(read(key)) == confirmed[key], key
    return confirmed
