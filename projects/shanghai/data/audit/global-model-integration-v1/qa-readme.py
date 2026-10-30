"""Independent checks of published README tables and pre-existing destinations."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
PROJECT = ROOT / 'projects/shanghai'
HERE = Path(__file__).resolve().parent
HEADING = '## 按区查看主要建筑\n'
base = json.loads((PROJECT / 'data/landmarks.json').read_text())
new = json.loads((PROJECT / 'data/candidate-city-integrations.json').read_text())['models']
districts = {str(item['id']): item['name'] for item in json.loads((PROJECT / 'data/districts.json').read_text())['districts']}
expected = {item['id']: districts[str(item['districtId'])] for item in base + new}
new_ids = {item['id'] for item in new}
expected_counts = Counter(expected.values())
assert len(expected_counts) == 16 and sum(expected_counts.values()) == len(expected) == 70
assert len(base) == 40 and len(new) == 30
inventory = json.loads((HERE / 'inventory.json').read_text())
revision = inventory['asset_baseline_commit']
manifest_ids = {item['id'] for item in inventory['records']}
assert len(manifest_ids) == 32 and manifest_ids <= set(expected)
assert {item['id'] for item in inventory['records'] if not item['already_in_city']} == new_ids
index_html = (PROJECT / 'index.html').read_text()
assert '<span id="landmark-count">70</span>' in index_html and '上海16区导航地图' in index_html
current_intro = (PROJECT / 'CURRENT_STATE.md').read_text().split('\n---\n', 1)[0]
assert '70处建筑与构件查看入口' in current_intro and '覆盖16区' in current_intro
assert '40处保留既有室外漫游' in current_intro and '30件此前独立展示的模型新增全局场景查看' in current_intro

directory_html = (PROJECT / 'landmarks.html').read_text()
directory_chips = {districts[code]: int(count) for code, count in re.findall(r'<h2 id="heading-district-(\d+)">[^<]+ <span>(\d+)</span></h2>', directory_html)}
assert directory_chips == expected_counts
beacon_contract_path = HERE / 'beacon-checks.json'
beacon_contract_binding = None
if beacon_contract_path.exists():
    beacon_contract_blob = beacon_contract_path.read_bytes()
    beacon_contract = json.loads(beacon_contract_blob)
    assert beacon_contract['passed'] > 0 and beacon_contract['catalogue_count'] == 70 and beacon_contract['district_count'] == 16
    assert {districts[code]: count for code, count in beacon_contract['district_counts'].items()} == expected_counts
    beacon_contract_binding = {'file': beacon_contract_path.relative_to(PROJECT).as_posix(), 'bytes': len(beacon_contract_blob), 'sha256': hashlib.sha256(beacon_contract_blob).hexdigest(), 'counts_match_readme': True, 'scope': 'Same catalogue counts and district totals; actual sprite rendering is checked separately.'}

reports = []
for relative in ['README.md', 'projects/shanghai/README.md']:
    file = ROOT / relative
    text = file.read_text()
    original = subprocess.check_output(['git', 'show', f'{revision}:{relative}'], cwd=ROOT).decode()
    old_section = original.split(HEADING, 1)[1].split('\n## ', 1)[0]
    old_rows = {re.search(r'#landmark=([^&]+)&mode=walk', line)[1]: line for line in old_section.splitlines() if line.startswith('| ') and '#landmark=' in line}
    section = text.split(HEADING, 1)[1].split('\n## ', 1)[0]
    assert section.count('| 主要建筑 |') == 16
    assert '| 独立候选（未配准） |' not in section
    assert '**汇总：16区，70处建筑与构件模型入口（40处既有＋30处新增接入）。**' in section
    assert '灯牌在视野内常显，密集时显示编号，点选查看名称。' in section
    assert '原40处保留室外漫游；新增30处按资料近似定位并提供全局查看' in section
    current_district, rows, declared_counts = None, {}, {}
    for line in section.splitlines():
        if line.startswith('### '):
            heading = re.fullmatch(r'### (.+?)（(\d+)处）', line)
            if heading:
                current_district = heading[1]
                assert current_district not in declared_counts
                declared_counts[current_district] = int(heading[2])
            else:
                current_district = None
        if line.startswith('| ') and '#landmark=' in line:
            matches = re.findall(r'#landmark=([^&]+)&mode=(walk|overview)', line)
            assert len(matches) == 1
            ident, mode = matches[0]
            assert ident not in rows and expected[ident] == current_district
            assert mode == ('overview' if ident in new_ids else 'walk')
            if ident in new_ids:
                assert '[单体](' in line
            else:
                assert old_rows[ident] == line, f'Original destination row changed: {ident}'
            rows[ident] = current_district
    assert rows == expected
    assert declared_counts == expected_counts == Counter(rows.values())
    assert sum(declared_counts.values()) == 70
    blob = file.read_bytes()
    if relative == 'README.md':
        assert len(blob) <= 500_000
        roads = json.loads((PROJECT / 'data/model-todo/discovered-streets.json').read_text())['roads']
        road_section = text.split('### 道路资料搜集 TODO\n', 1)[1].split('</details>', 1)[0]
        road_lines = [line for line in road_section.splitlines() if line.startswith('| ') and line.endswith('| 查资料 |')]
        assert len(road_lines) == len(roads) == 1038
        names = [item.get('name_simplified', item['name']).replace('|', '／').replace('\n', ' ').replace('\r', ' ') for item in roads]
        assert [line.split(' | ')[0][2:] for line in road_lines] == names
        assert '“查资料”指逐页读取、查沿街建筑／照片与文字、核对照片并拆为模型任务' in road_section
    reports.append({'file': relative, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest(), 'district_tables': 16, 'destinations': len(rows), 'new_overview_links': len(new_ids), 'preserved_old_walk_rows_exactly': len(old_rows), 'by_district': dict(Counter(rows.values())), 'visible_heading_counts': declared_counts, 'visible_heading_sum': sum(declared_counts.values()), 'readme_ids_equal_shared_beacon_catalogue': True})
report = {'schema': 'global-model-readme-checks-v1', 'passed': True, 'baseline_commit': revision, 'reports': reports, 'road_todo_preservation': {'records': 1038, 'all_names_and_order_preserved': True, 'repeated_task_replaced_by_equal_meaning_legend': True}, 'all_individual_candidate_assets_included': {'manifest_count': 32, 'all_ids_in_readme': True, 'already_integrated': 2, 'new_global_models': 30}, 'other_entry_text': {'index_count': 70, 'index_districts': 16, 'current_state_total': 70, 'existing_walk_preserved': 40, 'new_global_views': 30}, 'beacon_contract_check': beacon_contract_binding, 'directory_visible_chips': {'counts': directory_chips, 'sum': sum(directory_chips.values()), 'matches_readme': True}, 'beacon_catalogue': {'sources': ['data/landmarks.json', 'data/candidate-city-integrations.json'], 'ids': sorted(expected), 'count': len(expected), 'meaning': 'The same 40 + 30 records supplied by app.js to scene.setBuildingBeacons; live sprite visibility is audited separately.'}, 'scope': 'README table membership, visible district counts, shared beacon catalogue IDs, direct routes, preservation and byte bounds; not model accuracy, beacon rendering or CDN availability.'}
(HERE / 'readme.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': True, 'files': [(item['file'], item['bytes']) for item in reports]}, ensure_ascii=False))
