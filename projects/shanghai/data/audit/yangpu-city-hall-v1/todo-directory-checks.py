"""Verify the Yangpu City Hall delivery, bounded TODO retirement and all district links."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
PREFIX = 'projects/shanghai/'
BASELINE = 'c5eadbea297bb9d23d0658b2244d1e17034bbcb6'
ID = 'yangpu-former-shanghai-city-hall'


def read(path):
    file = ROOT / path
    return file.read_bytes() if file.exists() else subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=ROOT)


def main():
    bindings = []
    def document(path):
        raw = read(path)
        bindings.append({'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        return json.loads(raw)
    queue = document(PREFIX + 'data/model-todo/queue.json')
    catalog = document(PREFIX + 'data/candidate-city-integrations.json')
    legacy = document(PREFIX + 'data/landmarks.json')
    scopes = document(PREFIX + 'data/model-todo/completed-model-scope-review.json')
    heritage = document(PREFIX + 'data/model-todo/discovered-buildings.json')['records']
    named = document(PREFIX + 'data/model-todo/named-map-leads.json')['records']
    roads = document(PREFIX + 'data/model-todo/discovered-streets.json')['roads']
    delivered = [r for r in queue['production_queue'] if r['status'] in ('candidate_delivered', 'accepted')]
    pending = [r for r in queue['production_queue'] if r not in delivered]
    assert len(delivered) == 31 and len(queue['existing_models']) == 46
    assert [r['id'] for r in pending] == ['yangpu-jiangwan-stadium']
    assert len(heritage) == 1058 and len(named) == 1036 and len(roads) == 1038
    ids = {r['id'] for r in legacy + catalog['models']}
    assert len(legacy) == 40 and len(catalog['models']) == 37 and len(ids) == 77
    assert ID in ids and {r['id'] for r in queue['existing_models']} <= ids
    prior = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':' + PREFIX + 'data/candidate-city-integrations.json'], cwd=ROOT))
    assert catalog['models'][:-1] == prior['models'], 'Earlier 36 model records changed'
    assert catalog['models'][-1]['id'] == ID
    associations = {(layer, source) for row in catalog['models'] for layer, sources in row['source_feature_ids'].items() for source in sources}
    precise = document(PREFIX + 'data/precise-buildings-v6.json')['landmarks']
    for row in precise:
        if row['id'] in ids:
            associations.update(('building', source) for source in row.get('building_ids', []))
            associations.update(('building_part', source) for source in row.get('building_part_ids', []))
    associated = [r for r in named if (r['source_layer'], r['id']) in associations]
    assert len(associated) == 19
    assert ('building', '86e8b002-5e0e-4912-9807-086c2afeb27c') in associations
    assert any(r['id'] == '86e8b002-5e0e-4912-9807-086c2afeb27c' for r in named), 'This source is part of the named-source snapshot'
    completed_ids = {r['id'] for r in delivered}
    hidden = [r for r in scopes['records'] if not [t for t in r['remaining_tasks'] if t.get('completed_by_model_id') not in completed_ids]]
    assert len(hidden) == 10
    council = next(r for r in scopes['records'] if r['heritage_id'] == 'sh-historic-b1-019')
    assert [r['id'] for r in council['completed_models']] == ['huangpu-shanghai-municipal-council']
    hall = next(r for r in scopes['records'] if r['heritage_id'] == 'sh-historic-b1-020')
    assert [r['id'] for r in hall['completed_models']] == [ID] and not hall['remaining_tasks']
    assert not any(r['id'] == '3904106e-f668-46d4-a302-a13ccd00866a' for r in named)
    assert ('building', '3904106e-f668-46d4-a302-a13ccd00866a') in associations
    assert [r['id'] for r in council['remaining_tasks']] == ['municipal-council-west-junctions', 'municipal-council-courtyard-listed-scope']
    assert '接缝' in council['exclusions'] and '庭院' in council['exclusions']
    raw_unchanged = []
    for suffix in ['discovered-buildings.json', 'named-map-leads.json', 'discovered-streets.json', 'STREETS.md']:
        path = PREFIX + 'data/model-todo/' + suffix
        assert read(path) == subprocess.check_output(['git', 'show', BASELINE + ':' + path], cwd=ROOT), path
        raw_unchanged.append(path)
    old_audit_changes = subprocess.check_output(['git', 'diff', '--name-only', BASELINE, '--', PREFIX + 'data/audit'], cwd=ROOT, text=True).splitlines()
    assert all(path.startswith(PREFIX + 'data/audit/yangpu-city-hall-v1/') for path in old_audit_changes)
    directories = []
    for path in ['README.md', PREFIX + 'README.md']:
        raw = read(path); text = raw.decode()
        if path == 'README.md':
            assert len(raw) < 500000
            todo = text.split('<!-- model-todo:start -->')[1].split('<!-- model-todo:end -->')[0]
            active = todo.split('### 按顺序执行的模型')[1].split('### 按区列出的未完成建筑与构件 TODO')[0]
            assert len(re.findall(r'^\| \d+ \|', active, re.M)) == 1 and '| 32 |' in active
            assert '剩余1017条／已关联19条' in todo
            assert len(re.findall(r'^\| sh-historic-', todo, re.M)) == 1048
            assert '| sh-historic-b1-017 |' not in todo and '| sh-historic-b1-020 |' not in todo
            assert '| sh-historic-b1-018 |' in todo and '| sh-historic-b1-019 |' in todo
            assert '峻岭公寓前庭两片未核源区域' in todo and '峻岭公寓西侧低层住宅与名录范围' in todo
            assert '工部局西端接缝与保留带' in todo and '工部局庭院独立楼及名录范围' in todo
            assert '新新公司北侧旅馆、天井与南北连接' in todo
        section = text.split('## 按区查看主要建筑\n')[1].split('\n## ')[0]
        groups = re.findall(r'^### (.+?)（(\d+)处）', section, re.M)
        rows = re.findall(r'\[查看网页\]\((https://[^)]+#landmark=([^&]+)&mode=(walk|overview))\)', section)
        assert len(groups) == 16 and sum(int(n) for _, n in groups) == 77
        assert dict(groups)['黄浦区'] == '28' and dict(groups)['杨浦区'] == '2' and len(rows) == 77
        assert {row[1] for row in rows} == ids
        assert Counter(row[2] for row in rows) == {'walk': 40, 'overview': 37}
        assert all(url.startswith('https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#') for url, _, _ in rows)
        directories.append({'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'models': 77, 'districts': 16, 'huangpu': 28, 'yangpu': 2})
    report = {'schema': 'yangpu-city-hall-todo-directory-checks-v1', 'passed': True, 'baseline_commit': BASELINE,
              'completed_production_jobs': 31, 'existing_models_omitted_from_active_todo': 46,
              'active_production_id': pending[0]['id'], 'heritage_active_rows': 1048,
              'heritage_completed_main_buildings_omitted': 10, 'named_identity_associations': 19,
              'named_active_rows': 1017, 'council_exclusions': council['exclusions'],
              'old_36_model_records_unchanged': True, 'historical_audits_unchanged': True,
              'raw_data_unchanged': raw_unchanged, 'directories': directories, 'bindings': bindings,
              'scope': 'The Yangpu principal city hall exterior and its separately mapped approach stairbridge are delivered. Other campus buildings and interiors are excluded. The main building is omitted from duplicate heritage production tasks; earlier partial-building exclusions remain. The map source is not in the frozen 1036-name snapshot, so named associations stay19.'}
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'models': 77, 'heritage_active': 1048, 'named_active': 1017}))


if __name__ == '__main__':
    main()
