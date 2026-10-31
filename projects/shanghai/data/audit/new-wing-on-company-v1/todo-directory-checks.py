"""Read-only TODO/directory checks; writes only the adjacent JSON report.

Run from any directory with Python 3. No browser, network or generator writes.
Sparse tracked inputs are read from HEAD without materializing them.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[5]
BASELINE = 'b1d8a4b9926367c68f87e25dfdcda4c22e2c199c'
PROJECT = 'projects/shanghai/'
DONE = {'candidate_delivered', 'accepted'}
HIDDEN = {f'sh-historic-b1-{n:03}' for n in (1, 2, 3, 5, 6, 7, 13)}
BINDINGS = {}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def read(path):
    local = ROOT / path
    raw = local.read_bytes() if local.exists() else git('show', 'HEAD:' + path)
    BINDINGS[path] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                      'read_from': 'worktree' if local.exists() else 'HEAD (sparse)'}
    return raw


def data(path):
    return json.loads(read(PROJECT + path))


def urls(text):
    return [u.strip('<>') for u in re.findall(r'\]\(([^)\s]+)', text)
            + re.findall(r'^\[[^\]]+\]:\s*(\S+)', text, re.M)]


def heritage_rows(text):
    return {line.split('|')[1].strip(): line for line in text.splitlines()
            if line.startswith('| sh-historic-')}


def road_block(text):
    return text.split('### 道路资料搜集 TODO\n', 1)[1].split(
        '### 官方专题道路清单补充 TODO', 1)[0]


def main():
    queue = data('data/model-todo/queue.json')
    original = data('data/model-todo/discovered-buildings.json')['records']
    named = data('data/model-todo/named-map-leads.json')['records']
    roads = data('data/model-todo/discovered-streets.json')['roads']
    scope = data('data/model-todo/completed-model-scope-review.json')['records']
    base = data('data/landmarks.json')
    candidates = data('data/candidate-city-integrations.json')['models']
    precise = data('data/precise-buildings-v6.json')['landmarks']
    viewers = data('data/model-viewers.json')
    districts = {str(r['id']): r['name'] for r in data('data/districts.json')['districts']}
    read(PROJECT + 'tools/build_model_todo.py')
    read(PROJECT + 'tools/sync_readme_districts.py')
    read(PROJECT + 'data/model-todo/candidate-publication-times.json')
    read(str(Path(__file__).relative_to(ROOT)))

    jobs = {j['id']: j for j in queue['production_queue']}
    done_jobs = {i for i, j in jobs.items() if j['status'] in DONE}
    delivered = done_jobs | ({r['id'] for r in base + candidates} - set(jobs))
    assert len(done_jobs) == 25
    assert len(queue['existing_models']) == 46
    assert all(r['id'] in delivered for r in queue['existing_models'])
    assert jobs['huangpu-new-wing-on-company']['status'] == 'candidate_delivered'
    assert (len(original), len(named), len(roads)) == (1058, 1036, 1038)
    assert (len(base), len(candidates)) == (40, 31)

    root_text = read('README.md').decode()
    baseline_text = git('show', BASELINE + ':README.md').decode()
    production = root_text.split('### 按顺序执行的模型\n', 1)[1].split('\n### ', 1)[0]
    active_orders = [int(m) for m in re.findall(r'^\| (\d+) \|', production, re.M)]
    assert active_orders == sorted(j['order'] for j in jobs.values() if j['status'] not in DONE)
    assert not set(active_orders) & {jobs[i]['order'] for i in done_jobs}
    assert '### 尚待完成的已有模型事项' not in root_text
    assert '已交付的25项制作任务与已登记的46项模型库存' in root_text

    rows = heritage_rows(root_text)
    old_rows = heritage_rows(baseline_text)
    assert len(rows) == 1051
    assert list(rows) == [i for i in old_rows if i not in HIDDEN]
    assert set(rows) == {r['id'] for r in original} - HIDDEN
    reviewed_ids = {entry['heritage_id'] for entry in scope}
    remaining = {}
    for entry in scope:
        assert all(model['id'] in delivered for model in entry['completed_models'])
        tasks = [t for t in entry['remaining_tasks'] if t.get('completed_by_model_id') not in delivered]
        if not tasks:
            assert entry['heritage_id'] in HIDDEN
        else:
            title = '；'.join(t['title'] for t in tasks)
            assert rows[entry['heritage_id']].split('|')[2].strip() == title
            remaining[entry['heritage_id']] = [t['id'] for t in tasks]
    assert remaining['sh-historic-b1-014'] == ['wing-on-cross-street-bridges']
    assert all(rows[i] == old_rows[i] for i in rows if i not in reviewed_ids)

    source_models = {}
    associations = [(m['id'], m.get('source_feature_ids', {})) for m in candidates]
    associations += [(m['id'], {'building': m.get('building_ids', []),
                                'building_part': m.get('building_part_ids', [])}) for m in precise]
    for model_id, layers in associations:
        if model_id in delivered:
            for layer, ids in layers.items():
                for source_id in ids:
                    source_models.setdefault((layer, source_id), set()).add(model_id)
    matched = [r for r in named if (r['source_layer'], r['id']) in source_models]
    pending = [r for r in named if (r['source_layer'], r['id']) not in source_models]
    assert (len(matched), len(pending)) == (16, 1020)
    named_section = root_text.split('### 既有地图中的具名建筑待查线索', 1)[1].split('</details>', 1)[0]
    shown_named = re.findall(r'^\| ([0-9a-f-]{36}) \|', named_section, re.M)
    assert shown_named == [r['id'] for r in pending]
    assert '（剩余1020条／已关联16条）' in named_section
    assert source_models[('building', '5d94b317-649b-4e66-8805-639274d488c7')] == {'huangpu-old-wing-on-company'}
    assert source_models[('building', '708d0e95-d551-414d-a3be-897a9fe2fb6b')] == {'huangpu-new-wing-on-company'}
    # Removing only the new model's delivered state restores exactly one lead.
    previous = {key for key, ids in source_models.items() if ids - {'huangpu-new-wing-on-company'}}
    assert sum((r['source_layer'], r['id']) in previous for r in named) == 15

    preserved = []
    for rel in ('discovered-buildings.json', 'named-map-leads.json', 'discovered-streets.json',
                'heritage-first20-model-reconciliation.json', 'heritage-next20-model-reconciliation.json',
                'official-road-reconciliation.json', 'STREETS.md'):
        path = PROJECT + 'data/model-todo/' + rel
        assert read(path) == git('show', BASELINE + ':' + path), path
        preserved.append(path)
    assert road_block(root_text) == road_block(baseline_text)
    assert len(re.findall(r'^\| .* \| 查资料 \|$', road_block(root_text), re.M)) == 1038
    changed_old_audits = git('diff', '--name-only', BASELINE, '--', PROJECT + 'data/audit',
                            ':!projects/shanghai/data/audit/new-wing-on-company-v1').decode().splitlines()
    assert not changed_old_audits, changed_old_audits

    expected = {r['id']: districts[str(r['districtId'])] for r in base + candidates}
    new_ids = {r['id'] for r in candidates}
    district_counts = dict(Counter(expected.values()))
    standalone = {r['individual_page'] for r in candidates}
    standalone.update(r['page'] for r in viewers if r['kind'] == 'candidate')
    assert len(expected) == 71 and len(district_counts) == 16 and district_counts['黄浦区'] == 23
    directory_reports = []
    for path in ('README.md', PROJECT + 'README.md'):
        text = read(path).decode()
        assert 'model-walk' not in text
        direct = []
        for url in urls(text):
            parsed = urlsplit(url)
            page = parsed.path.rsplit('/', 1)[-1]
            assert page not in standalone | {'surfaces.html'}, (path, url)
            local_project = not parsed.netloc or (parsed.netloc in {'raw.githack.com', 'rawcdn.githack.com'}
                                                  and '/projects/shanghai/' in parsed.path)
            if local_project and page.endswith('.html'):
                assert page in {'index.html', 'landmarks.html'}, (path, url)
            if local_project and page == 'index.html':
                assert parsed.netloc == 'raw.githack.com'
                assert parsed.path == '/ecojust/e-resource/master/projects/shanghai/index.html', url
                params = parse_qs(parsed.fragment)
                if 'landmark' in params:
                    ident = params['landmark'][0]
                    assert ident in expected
                    assert params['mode'] == ['overview' if ident in new_ids else 'walk'], url
                    direct.append(ident)
        assert set(direct) == set(expected)
        section = text.split('## 按区查看主要建筑\n', 1)[1].split('\n## ', 1)[0]
        listed = {}; declared = {}; district = None
        for line in section.splitlines():
            heading = re.fullmatch(r'### (.+?)（(\d+)处）', line)
            if heading:
                district = heading[1]
                assert district not in declared
                declared[district] = int(heading[2])
            if line.startswith('| ') and '#landmark=' in line:
                ids = re.findall(r'#landmark=([^&]+)&mode=', line)
                assert len(ids) == 1 and ids[0] not in listed
                assert '[查看网页]' in line and '[单体]' not in line
                listed[ids[0]] = district
        assert listed == expected and declared == district_counts
        assert '71处建筑与构件模型入口（40处既有＋31处新增接入）' in section
        assert '原40处保留室外漫游' in section and '新增31处按资料近似定位' in section
        assert '灯牌在视野内常显，密集时显示编号' in section
        directory_reports.append({'path': path, 'unique_model_ids': len(listed), 'district_counts': declared,
                                  'direct_link_occurrences': len(direct), 'walk_model_ids': 40,
                                  'overview_model_ids': 31, 'all_model_views_use_current_main_map': True})
    assert BINDINGS['README.md']['bytes'] < 500000

    report = {
        'schema': 'new-wing-on-todo-directory-checks-v1', 'passed': True,
        'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'baseline_commit': BASELINE,
        'scope': 'Read-only structured-input and full-README checks. No WebGL, rendering, asset geometry, '
                 'publication-date accuracy or HTTP delivery claims. Bindings identify the exact checked bytes.',
        'completed_production_jobs_hidden': 25, 'completed_existing_inventory_hidden': 46,
        'remaining_production_orders': active_orders, 'completed_main_building_rows_hidden': sorted(HIDDEN),
        'active_heritage_rows': len(rows), 'specific_remaining_scope_tasks': remaining,
        'named_source_records': len(named), 'named_source_associations_hidden': len(matched),
        'named_source_rows_remaining': len(pending), 'named_matches': [
            {'source_layer': r['source_layer'], 'id': r['id'],
             'models': sorted(source_models[(r['source_layer'], r['id'])])} for r in matched],
        'named_before_new_wing_on_delivery': {'associated': 15, 'remaining': 1021},
        'named_after_new_wing_on_delivery': {'associated': 16, 'remaining': 1020},
        'source_files_identical_to_baseline': preserved, 'road_rows_identical_to_baseline': 1038,
        'old_tracked_audit_diff_against_baseline': changed_old_audits,
        'readme_directories': directory_reports, 'input_bindings': BINDINGS,
    }
    output = Path(__file__).with_suffix('.json')
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'report': str(output.relative_to(ROOT)),
                      'heritage_rows': len(rows), 'named_rows': len(pending),
                      'models': len(expected), 'districts': len(district_counts)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
