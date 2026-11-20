"""Cross-check the frozen browser inputs, installed assets and postal directory routes."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from shapely.geometry import Point, shape

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
REPO = PROJECT.parents[1]
MODEL = 'hongkou-general-post-office'


def read(path):
    return json.loads(path.read_bytes())


def receipt(path):
    if path.is_file():
        data = path.read_bytes()
    else:
        data = subprocess.check_output(['git', 'show', f'HEAD:{path.relative_to(REPO)}'], cwd=REPO)
    return {'bytes': len(data), 'sha256': sha256(data).hexdigest()}


def check_binding(path, binding):
    actual = receipt(path)
    assert all(binding[key] == value for key, value in actual.items()), path
    return {'file': str(path.relative_to(REPO)), **actual}


def main():
    contract = read(AUDIT / 'qa-contract.json')
    assert contract['frozen'] and not contract['preliminary_only'] and contract['model_id'] == MODEL
    catalogue = read(PROJECT / 'data/candidate-city-integrations.json')
    model, = [item for item in catalogue['models'] if item['id'] == MODEL]
    inventory = read(PROJECT / 'data/global-models/candidate-inventory.json')
    record, = [item for item in inventory['records'] if item['id'] == MODEL]
    manifest_path = PROJECT / record['manifest']
    manifest = read(manifest_path)
    assert manifest['id'] == MODEL and receipt(manifest_path)['sha256'] == record['manifest_sha256'] == contract['model_manifest_sha256']
    assets = {}
    for key, asset in manifest['assets'].items():
        role = 'web' if key == 'full' else key
        pathname = manifest_path.parent / asset['file']
        assert pathname == PROJECT / record['assets'][role]['file']
        assets[role] = check_binding(pathname, record['assets'][role])
        check_binding(pathname, asset)
        if role in ('web', 'lod'):
            assert model['assets'][role] == record['assets'][role]
        if role != 'native':
            assert contract['model_geometry_sha256'][role] == asset['sha256']

    sources = [check_binding(PROJECT / row['path'], row) for row in contract['source_bindings']]
    inputs = [check_binding(AUDIT / row['file'], row) for row in contract['input_receipts']]
    checked_points = {}
    for key, probes, coord, expected in [
        ('replacement_geometry', 'actual_source_roof_probes', 'position_wgs84', 'expected_target_clip'),
        ('collision_geometry', 'ground_probes', 'wgs84', 'expected'),
    ]:
        assert contract[key] == model[key]
        geometry = shape(model[key])
        assert geometry.is_valid
        checked_points[key] = {}
        for point in contract[probes]:
            label = point.get('qa_name') or point['name']
            inside = geometry.covers(Point(point[coord]))
            assert inside == bool(point[expected]), label
            checked_points[key][label] = inside
    assert model['owner']['feature_local_id'] == 1959
    assert not checked_points['replacement_geometry']['neighbor-3148']
    assert not checked_points['replacement_geometry']['retained-joint-same-owner-1959']

    queue = read(PROJECT / 'data/model-todo/queue.json')['production_queue']
    job, = [item for item in queue if item['id'] == MODEL]
    viewer, = [item for item in read(PROJECT / 'data/model-viewers.json') if item['id'] == MODEL]
    assert viewer['name'] == job['name'] == model['name']
    assert viewer['page'] == model['individual_page'] == 'postal-office.html'
    assert not viewer['model_walk'] and not model['navigation']['listed']
    for path in [REPO / 'README.md', PROJECT / 'README.md']:
        heading = '### 虹口区（5处）'
        district = path.read_text().split(heading, 1)[1].split('\n### ', 1)[0]
        matches = [row for row in district.splitlines() if '[查看网页](' + job['preview'] + ')' in row]
        assert len(matches) == 1 and matches[0].startswith('| ' + job['name'] + ' |'), path

    report = {'model_id': MODEL, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'passed': True, 'script_sha256': receipt(Path(__file__))['sha256'],
              'qa_contract_sha256': receipt(AUDIT / 'qa-contract.json')['sha256'],
              'assets': assets, 'map_source_bytes': sources, 'contract_inputs': inputs,
              'polygon_covers_probe': checked_points, 'name': job['name'],
              'district': viewer['district'], 'directory_route': job['preview'],
              'scope': 'Local asset and contract bindings, roof and ground point membership, named directory routes and overview-only registration. Browser rendering and public HTTP delivery have separate evidence.'}
    (AUDIT / 'independent-metadata-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
