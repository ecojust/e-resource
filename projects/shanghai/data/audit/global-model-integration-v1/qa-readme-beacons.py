"""Cross-check final live beacon identities with both published district tables."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
ROOT = PROJECT.parents[1]

def binding(file):
    blob = file.read_bytes()
    return {'file': file.relative_to(ROOT).as_posix(), 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}

browser_path = HERE / 'browser-beacons.json'
browser = json.loads(browser_path.read_text())
assert browser['completed'] is True and browser['changedDestinationTouchVerified'] is True
base = json.loads((PROJECT / 'data/landmarks.json').read_text())
additions = json.loads((PROJECT / 'data/candidate-city-integrations.json').read_text())['models']
district_names = {str(item['id']): item['name'] for item in json.loads((PROJECT / 'data/districts.json').read_text())['districts']}
expected_ids = {item['id'] for item in base + additions}
expected_counts = Counter(district_names[str(item['districtId'])] for item in base + additions)
assert len(expected_ids) == 70 and len(expected_counts) == 16 and sum(expected_counts.values()) == 70
readmes = []
for path in (ROOT / 'README.md', PROJECT / 'README.md'):
    section = path.read_text().split('## 按区查看主要建筑\n', 1)[1].split('\n## ', 1)[0]
    ids = re.findall(r'^\|[^\n]*#landmark=([^&]+)&mode=(?:walk|overview)', section, re.M)
    counts = {name: int(count) for name, count in re.findall(r'^### (.+?)（(\d+)处）$', section, re.M)}
    assert len(ids) == len(set(ids)) == 70 and set(ids) == expected_ids
    assert counts == expected_counts
    readmes.append({**binding(path), 'ids_equal_every_live_beacon_case': True, 'district_counts': counts, 'total': sum(counts.values())})

cases = []
assert len(browser['cases']) == 10
for item in browser['cases']:
    state = item['state']
    assert state['count'] == 70 and len(state['ids']) == 70 and set(state['ids']) == expected_ids
    assert state['districtCount'] == 16
    sources = item['sources']
    assert {source['id'] for source in sources} == set(state['sourceIds'])
    assert len(sources) == 3
    for source in sources:
        assert source['count'] == len(source['ids']) == 70 and set(source['ids']) == expected_ids
    cases.append({'label': item['label'], 'viewport': item['viewport'], 'zoom': item['zoom'], 'registered_beacon_ids': 70, 'viewport_layout_labels': state['viewportLabelCount'], 'districts': 16, 'source_id_sets_match': 3, 'label_mode': state['labelMode']})

result = {'schema': 'readme-live-beacons-crosscheck-v1', 'passed': True, 'browser_report': binding(browser_path), 'readmes': readmes, 'live_cases': cases, 'shared_ids': sorted(expected_ids), 'catalogue_bindings': [binding(PROJECT / 'data/landmarks.json'), binding(PROJECT / 'data/candidate-city-integrations.json')], 'visibility_note': 'Each case registers 70 identities; the number of viewport-visible signs varies. This cross-check does not infer visibility from native label QRF. Pixel, center-pick and real click/touch evidence remains in the bound browser report.', 'scope': 'Exact 70-ID and 16-district agreement between both README tables, shared catalogue and all ten final browser beacon states/sources. This check reuses the bound browser evidence; it does not claim a new WebGL run or that out-of-viewport geographic anchors are visible.'}
(HERE / 'readme-beacons.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': True, 'live_cases': len(cases), 'ids_each': 70, 'districts': 16, 'report_sha256': hashlib.sha256((HERE / 'readme-beacons.json').read_bytes()).hexdigest()}))
