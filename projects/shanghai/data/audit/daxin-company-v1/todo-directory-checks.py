"""Check this delivery's active TODO, exact IDs and published directory rows."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
PROJECT = ROOT / 'projects/shanghai'
BASELINE = '248df5c15988bba05f073485cacc93083fb581e8'
ID = 'huangpu-daxin-company'


def read(path):
    file = ROOT / path
    return file.read_bytes() if file.exists() else subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=ROOT)


def main():
    bindings = []
    def document(path):
        raw = read(path)
        bindings.append({'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        return json.loads(raw)
    prefix = 'projects/shanghai/'
    queue = document(prefix + 'data/model-todo/queue.json')
    catalog = document(prefix + 'data/candidate-city-integrations.json')
    legacy = document(prefix + 'data/landmarks.json')
    scopes = document(prefix + 'data/model-todo/completed-model-scope-review.json')
    heritage = document(prefix + 'data/model-todo/discovered-buildings.json')['records']
    named = document(prefix + 'data/model-todo/named-map-leads.json')['records']
    roads = document(prefix + 'data/model-todo/discovered-streets.json')['roads']
    delivered = [r for r in queue['production_queue'] if r['status'] in ('candidate_delivered', 'accepted')]
    pending = [r for r in queue['production_queue'] if r not in delivered]
    assert len(delivered) == 27 and len(queue['existing_models']) == 46
    assert [r['id'] for r in pending] == ['huangpu-cathay-mansions']
    assert len(heritage) == 1058 and len(named) == 1036 and len(roads) == 1038
    ids = {r['id'] for r in legacy + catalog['models']}
    assert len(legacy) == 40 and len(catalog['models']) == 33 and len(ids) == 73
    assert ID in ids and {r['id'] for r in queue['existing_models']} <= ids
    prior = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':' + prefix + 'data/candidate-city-integrations.json'], cwd=ROOT))
    assert catalog['models'][:-1] == prior['models'], 'Earlier 32 model records changed'
    assert catalog['models'][-1]['id'] == ID
    associations = {(layer, source) for row in catalog['models'] for layer, sources in row['source_feature_ids'].items() for source in sources}
    precise = document(prefix + 'data/precise-buildings-v6.json')['landmarks']
    for row in precise:
        if row['id'] in ids:
            associations.update(('building', source) for source in row.get('building_ids', []))
            associations.update(('building_part', source) for source in row.get('building_part_ids', []))
    associated = [r for r in named if (r['source_layer'], r['id']) in associations]
    assert len(associated) == 18
    assert any(r['id'] == 'ca6dccd6-0c72-4376-8978-e6e660629037' for r in associated)
    completed_ids = {r['id'] for r in delivered}
    hidden = [r for r in scopes['records'] if not [t for t in r['remaining_tasks'] if t.get('completed_by_model_id') not in completed_ids]]
    assert len(hidden) == 8
    daxin = next(r for r in scopes['records'] if r['heritage_id'] == 'sh-historic-b1-016')
    assert [r['id'] for r in daxin['completed_models']] == [ID]
    assert daxin['remaining_tasks'] == []
    assert 'B馆' in daxin['exclusions'] and 'C馆' in daxin['exclusions']
    raw_unchanged = []
    for suffix in ['discovered-buildings.json', 'named-map-leads.json', 'discovered-streets.json', 'STREETS.md']:
        path = prefix + 'data/model-todo/' + suffix
        assert read(path) == subprocess.check_output(['git', 'show', BASELINE + ':' + path], cwd=ROOT), path
        raw_unchanged.append(path)
    old_audit_changes = subprocess.check_output(['git', 'diff', '--name-only', BASELINE, '--', prefix + 'data/audit'], cwd=ROOT, text=True).splitlines()
    assert all(path.startswith(prefix + 'data/audit/daxin-company-v1/') for path in old_audit_changes)
    directories = []
    for path in ['README.md', prefix + 'README.md']:
        raw = read(path); text = raw.decode()
        if path == 'README.md':
            assert len(raw) < 500000
            todo = text.split('<!-- model-todo:start -->')[1].split('<!-- model-todo:end -->')[0]
            active = todo.split('### 按顺序执行的模型')[1].split('### 按区列出的未完成建筑与构件 TODO')[0]
            assert len(re.findall(r'^\| \d+ \|', active, re.M)) == 1 and '| 28 |' in active
            assert '剩余1018条／已关联18条' in todo
            assert len(re.findall(r'^\| sh-historic-', todo, re.M)) == 1050
            assert '| sh-historic-b1-016 |' not in todo
            assert '新新公司北侧旅馆、天井与南北连接' in todo
        section = text.split('## 按区查看主要建筑\n')[1].split('\n## ')[0]
        groups = re.findall(r'^### (.+?)（(\d+)处）', section, re.M)
        rows = re.findall(r'\[查看网页\]\((https://[^)]+#landmark=([^&]+)&mode=(walk|overview))\)', section)
        assert len(groups) == 16 and sum(int(n) for _, n in groups) == 73
        assert dict(groups)['黄浦区'] == '25' and len(rows) == 73
        assert {row[1] for row in rows} == ids
        assert Counter(row[2] for row in rows) == {'walk': 40, 'overview': 33}
        assert all(url.startswith('https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#') for url, _, _ in rows)
        directories.append({'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'models': 73, 'districts': 16, 'huangpu': 25})
    report = {'schema': 'daxin-todo-directory-checks-v1', 'passed': True, 'baseline_commit': BASELINE,
              'completed_production_jobs': 27, 'existing_models_omitted_from_active_todo': 46,
              'active_production_id': pending[0]['id'], 'heritage_active_rows': 1050,
              'heritage_completed_main_buildings_omitted': 8, 'named_identity_associations': 18,
              'named_active_rows': 1018, 'daxin_adjoining_blocks_excluded': daxin['exclusions'],
              'old_32_model_records_unchanged': True, 'historical_audits_unchanged': True,
              'raw_data_unchanged': raw_unchanged, 'directories': directories, 'bindings': bindings,
              'scope': 'Identity and task scope checks only. The bounded historic main-building exterior is delivered; this does not complete the adjoining B/C buildings, bridges or interiors.'}
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'models': 73, 'heritage_active': 1050, 'named_active': 1018}))


if __name__ == '__main__':
    main()
