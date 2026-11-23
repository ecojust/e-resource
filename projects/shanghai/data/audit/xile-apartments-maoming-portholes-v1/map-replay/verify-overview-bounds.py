"""Check the two camera contracts and the recorded first-hit tests. Run with Python 3."""
from pathlib import Path
import hashlib
import json

audit = Path(__file__).resolve().parents[1]

def read(name):
    return json.loads((audit / name).read_bytes())

original = read('final-placement-contract.json')
updated = read('overview-placement-rechecked.json')
field = 'overview_focus_bounds_glb'
bounds = updated['bounds_glb']
expected = {
    'min': list(map(max, original[field]['min'], bounds['min'])),
    'max': list(map(min, original[field]['max'], bounds['max'])),
}
assert updated[field] == expected
assert {**original, field: expected} == updated
contract_signature = hashlib.sha256((audit / 'overview-placement-rechecked.json').read_bytes()).hexdigest()
rays = read('bounded-model-sightlines.json')
overview = read('bounded-overview-sightlines.json')
assert rays['passed'] and rays['contract_sha256'] == overview['contract_sha256'] == contract_signature
assert set(rays['views']) == {'full', 'lod'}
features = set(rays['certified_features'])
assert len(features) == 18 and features == set(overview['certified_features'])
for views in rays['views'].values():
    assert {view['screen'] for view in views} == {'desktop', 'mobile'}
    for view in views:
        assert len(view['samples']) == 18
        assert {s['feature'] for s in view['samples']} == features
        for sample in view['samples']:
            assert sample['visible'] and sample['screen_visible']
            assert sample['first_hit']['material'] == sample['expected_material']
print('Checked the clipped overview bounds and 72 recorded first-hit material tests.')
