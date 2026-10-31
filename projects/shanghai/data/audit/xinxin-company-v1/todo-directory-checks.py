"""Check this delivery's active TODO, exact IDs and published directory rows."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
PROJECT = ROOT / 'projects/shanghai'
BASELINE = '7b85c03efc436527efeb803b0743e4b2580e78d7'
ID = 'huangpu-xinxin-company'


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
    assert len(delivered) == 26 and len(queue['existing_models']) == 46
    assert [r['id'] for r in pending] == ['huangpu-daxin-company']
    assert len(heritage) == 1058 and len(named) == 1036 and len(roads) == 1038
    ids = {r['id'] for r in legacy + catalog['models']}
    assert len(legacy) == 40 and len(catalog['models']) == 32 and len(ids) == 72
    assert ID in ids and {r['id'] for r in queue['existing_models']} <= ids
    prior = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':' + prefix + 'data/candidate-city-integrations.json'], cwd=ROOT))
    assert catalog['models'][:-1] == prior['models'], 'Earlier 31 model records changed'
    assert catalog['models'][-1]['id'] == ID
    associations = {(layer, source) for row in catalog['models'] for layer, sources in row['source_feature_ids'].items() for source in sources}
    precise = document(prefix + 'data/precise-buildings-v6.json')['landmarks']
    for row in precise:
        if row['id'] in ids:
            associations.update(('building', source) for source in row.get('building_ids', []))
            associations.update(('building_part', source) for source in row.get('building_part_ids', []))
    associated = [r for r in named if (r['source_layer'], r['id']) in associations]
    assert len(associated) == 17
    assert any(r['id'] == '7e69180c-6b22-4417-a40b-f5dcd2235bb9' for r in associated)
    completed_ids = {r['id'] for r in delivered}
    hidden = [r for r in scopes['records'] if not [t for t in r['remaining_tasks'] if t.get('completed_by_model_id') not in completed_ids]]
    assert len(hidden) == 7
    xinxin = next(r for r in scopes['records'] if r['heritage_id'] == 'sh-historic-b1-015')
    assert [r['id'] for r in xinxin['completed_models']] == [ID]
    assert xinxin['remaining_tasks'] and all(t.get('completed_by_model_id') not in completed_ids for t in xinxin['remaining_tasks'])
    assert '北' in json.dumps(xinxin['remaining_tasks'], ensure_ascii=False)
    raw_unchanged = []
    for suffix in ['discovered-buildings.json', 'named-map-leads.json', 'discovered-streets.json', 'STREETS.md']:
        path = prefix + 'data/model-todo/' + suffix
        assert read(path) == subprocess.check_output(['git', 'show', BASELINE + ':' + path], cwd=ROOT), path
        raw_unchanged.append(path)
    old_audit_changes = subprocess.check_output(['git', 'diff', '--name-only', BASELINE, '--', prefix + 'data/audit'], cwd=ROOT, text=True).splitlines()
    assert all(path.startswith(prefix + 'data/audit/xinxin-company-v1/') for path in old_audit_changes)
    directories = []
    for path in ['README.md', prefix + 'README.md']:
        raw = read(path); text = raw.decode()
        if path == 'README.md':
            assert len(raw) < 500000
            todo = text.split('<!-- model-todo:start -->')[1].split('<!-- model-todo:end -->')[0]
            active = todo.split('### 按顺序执行的模型')[1].split('### 按区列出的未完成建筑与构件 TODO')[0]
            assert len(re.findall(r'^\| \d+ \|', active, re.M)) == 1 and '| 27 |' in active
            assert '剩余1019条／已关联17条' in todo
            assert len(re.findall(r'^\| sh-historic-', todo, re.M)) == 1051
            row = next(line for line in todo.splitlines() if line.startswith('| sh-historic-b1-015 |'))
            assert '北' in row and '天井' in row
        section = text.split('## 按区查看主要建筑\n')[1].split('\n## ')[0]
        groups = re.findall(r'^### (.+?)（(\d+)处）', section, re.M)
        rows = re.findall(r'\[查看网页\]\((https://[^)]+#landmark=([^&]+)&mode=(walk|overview))\)', section)
        assert len(groups) == 16 and sum(int(n) for _, n in groups) == 72
        assert dict(groups)['黄浦区'] == '24' and len(rows) == 72
        assert {row[1] for row in rows} == ids
        assert Counter(row[2] for row in rows) == {'walk': 40, 'overview': 32}
        assert all(url.startswith('https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#') for url, _, _ in rows)
        directories.append({'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'models': 72, 'districts': 16, 'huangpu': 24})
    report = {'schema': 'xinxin-todo-directory-checks-v1', 'passed': True, 'baseline_commit': BASELINE,
              'completed_production_jobs': 26, 'existing_models_omitted_from_active_todo': 46,
              'active_production_id': pending[0]['id'], 'heritage_active_rows': 1051,
              'heritage_completed_main_buildings_omitted': 7, 'named_identity_associations': 17,
              'named_active_rows': 1019, 'xinxin_unfinished_scope_retained': xinxin['remaining_tasks'],
              'old_31_model_records_unchanged': True, 'historical_audits_unchanged': True,
              'raw_data_unchanged': raw_unchanged, 'directories': directories, 'bindings': bindings,
              'scope': 'Identity and task scope checks only. The southern exterior is delivered; this does not complete the entire heritage place or northern source building.'}
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'models': 72, 'heritage_active': 1051, 'named_active': 1019}))


if __name__ == '__main__':
    main()
