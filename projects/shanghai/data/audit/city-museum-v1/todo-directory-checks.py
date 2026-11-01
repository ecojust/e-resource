#!/usr/bin/env python3
"""Verify museum scope, preserved history, asset totals, and every README model link."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import posixpath
import re
import subprocess
from urllib.parse import parse_qs, urlsplit

BASELINE = '93e3cb2d0ddeba1a7db7d435bf66c2f61492326e'
PREFIX = 'projects/shanghai/'
ID = 'yangpu-former-shanghai-city-museum'
NEXT_ID = 'yangpu-china-aviation-association-building'
AUDIT_PREFIX = PREFIX + 'data/audit/city-museum-v1/'
MAIN_UUID = 'cdc86c9b-dee5-4342-a7ee-e962fa0d030e'
GATE_UUID = 'd54de774-0952-43c1-98a0-c9cbeaf207b1'
REMAINING_IDS = ['city-museum-east-rear-hall-details', 'city-museum-court-structures-and-scope']
REMAINING_TITLES = ['旧市博物馆东中后厅范围、年代与外观细化', '旧市博物馆院内小源510/1262与保护范围调查']
OLD_ASSET_BYTES = 684749128
NAVIGATION_PREFIX = PREFIX + 'data/audit/readme-navigation-v1/'
NAVIGATION_FILES = {
    NAVIGATION_PREFIX + 'report.json': '65c7cbcac92d92c48fbfeb1fb648a10f637be0847cf4d14be12b81b40ae63569',
    NAVIGATION_PREFIX + 'README.md': 'a2d934338d4f7048f00caba65f7c973a29206e7f84bafa18b4c496671064e006',
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def locate_root():
    for parent in Path(__file__).resolve().parents:
        if (parent / '.git').exists():
            return parent
    return Path('/workspace/e-resource')


def verify_readme_navigation_exception(root, git, ids, legacy_ids, bindings):
    """Accept only Root's exact reviewed64-file baseline replay and two audit files."""
    for path, expected_sha in NAVIGATION_FILES.items():
        raw = (root / path).read_bytes()
        require(digest(raw) == expected_sha, 'Navigation exception evidence changed: ' + path)
        bindings.append({'path': path, 'bytes': len(raw), 'sha256': digest(raw)})
    report = json.loads((root / (NAVIGATION_PREFIX + 'report.json')).read_bytes())
    require(report['schema'] == 'readme-navigation-v1' and report['baseline_commit'] == BASELINE,
            'Wrong navigation exception baseline or schema')
    require(report['status'] == 'static-validation-passed' and report['files_changed'] == len(report['files']) == 64,
            'Navigation exception must retain exactly the reviewed64 files')
    changed_paths = set()
    navigation_count = source_count = 0
    base_url = 'https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html'
    for row in report['files']:
        path = row['path']
        require(path not in changed_paths and Path(path).name == 'README.md'
                and (path.startswith(PREFIX + 'data/audit/') or path.startswith(PREFIX + 'source/')),
                'Duplicate or out-of-scope navigation exception path: ' + path)
        require(not path.startswith(AUDIT_PREFIX) and not path.startswith(NAVIGATION_PREFIX),
                'Navigation exception is only for existing baseline README files')
        changed_paths.add(path)
        baseline_raw = git('show', BASELINE + ':' + path)
        require(digest(baseline_raw) == row['before_sha256'], 'Navigation beforeSHA differs from baseline: ' + path)
        replay = baseline_raw.decode()
        require(bool(row['replacement_operations']), 'Navigation exception has no exact replacement operations')
        for operation in row['replacement_operations']:
            before_text = operation['before_text']
            after_text = operation['after_text']
            require(operation['kind'] == 'exact-navigation-line-replacement' and before_text
                    and before_text != after_text and replay.count(before_text) == 1,
                    'Navigation replacement is not the uniquely reviewed line: ' + path)
            require(replay[:replay.index(before_text)].count('\n') + 1 == operation['line'],
                    'Navigation replacement line differs from reviewed position: ' + path)
            replay = replay.replace(before_text, after_text, 1)
        replay_raw = replay.encode()
        current = (root / path).read_bytes()
        require(digest(replay_raw) == row['after_sha256'] and current == replay_raw,
                'Current README is not exactly the reviewed baseline replay: ' + path)
        for change in row['changes']:
            require(change['after_url'] in replay, 'A reviewed resulting link is missing: ' + path)
            if change['kind'] == 'broken-relative-source-reference':
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), change['after_url']))
                require(resolved.startswith(PREFIX + 'source/') and resolved.endswith('/README.md'),
                        'Source-reference correction leaves the reviewed source documentation')
                git('cat-file', '-e', BASELINE + ':' + resolved)
                source_count += 1
            elif change['kind'] == 'surface':
                require(change['model_id'] is None and change['after_url'] == base_url + '#mode=overview',
                        'Wrong global surface-view URL')
                navigation_count += 1
            else:
                model_id = change['model_id']
                require(model_id in ids, 'Navigation correction points to an unknown model')
                mode = 'walk' if model_id in legacy_ids else 'overview'
                require(change['after_url'] == base_url + '#landmark=' + model_id + '&mode=' + mode,
                        'Navigation correction differs from the canonical registered destination')
                navigation_count += 1
    require(navigation_count == report['navigation_links_changed'] == 71
            and source_count == report['source_reference_links_changed'] == 4
            and len(report['wording_adjustments']) == 6,
            'Navigation/source/context correction counts differ from the reviewed report')
    for row in report['preserved_immutable_links']:
        file = root / row['path']
        current = (file.read_bytes() if file.exists() else git('show', 'HEAD:' + row['path'])).decode()
        baseline = git('show', BASELINE + ':' + row['path']).decode()
        require(current.count(row['url']) == baseline.count(row['url']) > 0,
                'An immutable historical URL changed: ' + row['path'])
    summary = {'report': NAVIGATION_PREFIX + 'report.json',
               'report_sha256': NAVIGATION_FILES[NAVIGATION_PREFIX + 'report.json'],
               'readme_sha256': NAVIGATION_FILES[NAVIGATION_PREFIX + 'README.md'],
               'baseline_replayed_files': len(changed_paths), 'historical_audit_readmes': sum(
                   path.startswith(PREFIX + 'data/audit/') for path in changed_paths),
               'canonical_navigation_links': navigation_count, 'source_reference_links': source_count,
               'short_context_adjustments': len(report['wording_adjustments']),
               'exact_current_bytes_equal_replay': True, 'immutable_historical_links_preserved': True}
    return changed_paths, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=locate_root())
    parser.add_argument('--output', type=Path, default=Path(__file__).with_suffix('.json'))
    args = parser.parse_args()
    root = args.repo.resolve()
    bindings = []

    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=root)

    def read(path):
        file = root / path
        return file.read_bytes() if file.exists() else git('show', 'HEAD:' + path)

    def document(path):
        raw = read(path)
        bindings.append({'path': path, 'bytes': len(raw), 'sha256': digest(raw)})
        return json.loads(raw)

    def prior(path):
        return json.loads(git('show', BASELINE + ':' + path))

    queue_path = PREFIX + 'data/model-todo/queue.json'
    queue = document(queue_path)
    old_queue = prior(queue_path)
    delivered = [r for r in queue['production_queue'] if r['status'] in ('candidate_delivered', 'accepted')]
    pending = [r for r in queue['production_queue'] if r['status'] not in ('candidate_delivered', 'accepted')]
    require(len(delivered) == 35 and len(queue['existing_models']) == 46, 'Expected35delivered +46existing')
    require(queue['existing_models'] == old_queue['existing_models'], 'Existing queue models changed')
    require(queue['production_queue'][:-2] == old_queue['production_queue'][:-1], 'Earlier34 production jobs changed')
    require(len(queue['production_queue']) == 36 and len(pending) == 1, 'Expected exactly one active production item')
    require(pending[0]['id'] == NEXT_ID and pending[0]['order'] == 36
            and pending[0]['heritage_record_id'] == 'sh-historic-b4-177'
            and pending[0]['status'] == 'identity_review', 'Wrong next production item')
    museum_job = next(r for r in delivered if r['id'] == ID)
    require(museum_job['heritage_record_id'] == 'sh-historic-b2-012', 'Wrong museum heritage identity')
    require(museum_job['preview'] == 'https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=' + ID + '&mode=overview',
            'Museum production link does not point to the global viewer')

    catalog_path = PREFIX + 'data/candidate-city-integrations.json'
    catalog = document(catalog_path)
    old_catalog = prior(catalog_path)
    legacy_path = PREFIX + 'data/landmarks.json'
    legacy = document(legacy_path)
    require(read(legacy_path) == git('show', BASELINE + ':' + legacy_path), 'Legacy40 catalog changed')
    require(len(legacy) == 40 and len(catalog['models']) == 41, 'Expected40legacy +41candidate')
    require(catalog['models'][:-1] == old_catalog['models'], 'Earlier40 candidate records changed')
    museum = catalog['models'][-1]
    require(museum['id'] == ID and museum['individual_page'] == 'city-museum.html', 'Wrong appended model')
    ids = [r['id'] for r in legacy + catalog['models']]
    require(len(ids) == len(set(ids)) == 81, 'Duplicate or missing global model ID')
    ids = set(ids)
    require({r['id'] for r in queue['existing_models']} <= ids, 'Existing model absent from main viewer')
    require(museum['source_feature_ids'] == {'building': [MAIN_UUID], 'building_part': []}, 'Wrong main museum source')
    require(museum['site_replacement']['source_feature_ids'] == {'building': [GATE_UUID], 'building_part': []}, 'Wrong overlapping gate source')
    require(museum['owner'] == {'macro_id': '14-13722-6690', 'feature_local_id': 1860}, 'Wrong main source owner')
    require(museum['site_replacement']['owner'] == {'macro_id': '14-13722-6690', 'feature_local_id': 1931}, 'Wrong gate source owner')
    require(museum['navigation']['listed'] is False, 'Museum interior walk is not delivered')

    manifest_path = PREFIX + 'assets/models/candidates/' + ID + '/manifest.json'
    manifest = document(manifest_path)
    require(manifest['id'] == ID and set(manifest['assets']) == {'raw', 'native', 'full', 'lod'}, 'Invalid museum four-asset manifest')
    new_asset_bytes = 0
    for role, asset in manifest['assets'].items():
        require(Path(asset['file']).name == asset['file'], 'Unexpected manifest asset path')
        path = str(Path(manifest_path).parent / asset['file'])
        raw = read(path)
        require(len(raw) == asset['bytes'] and digest(raw) == asset['sha256'], 'Asset differs from manifest: ' + role)
        new_asset_bytes += len(raw)
        bindings.append({'path': path, 'bytes': len(raw), 'sha256': digest(raw)})
    inventory_path = PREFIX + 'data/global-models/candidate-inventory.json'
    inventory = document(inventory_path)
    old_inventory = prior(inventory_path)
    require(inventory['records'][:-1] == old_inventory['records'], 'Earlier42 inventory records changed')
    require(inventory['records'][-1]['id'] == ID, 'Museum must be the appended inventory entry')
    require(inventory['candidate_manifest_count'] == len(inventory['records']) == 43, 'Expected43 manifests')
    require(inventory['new_city_model_count'] == 41 and inventory['resulting_city_count'] == 81, 'Wrong inventory model totals')
    require(old_inventory['verification']['files'] == 168 and old_inventory['verification']['bytes'] == OLD_ASSET_BYTES,
            'Unexpected baseline asset accounting')
    require(inventory['verification']['files'] == 172
            and inventory['verification']['bytes'] == OLD_ASSET_BYTES + new_asset_bytes, 'Wrong final asset accounting')
    require(inventory['records'][-1]['manifest_sha256'] == digest(read(manifest_path)), 'Inventory manifest binding is stale')
    for role, asset in manifest['assets'].items():
        actual = inventory['records'][-1]['assets']['web' if role == 'full' else role]
        require(actual['bytes'] == asset['bytes'] and actual['sha256'] == asset['sha256'], 'Inventory asset binding is stale')
    for role in ['web', 'lod']:
        require(museum['assets'][role] == inventory['records'][-1]['assets'][role], 'Catalog asset binding is stale')

    scope_path = PREFIX + 'data/model-todo/completed-model-scope-review.json'
    scopes = document(scope_path)
    old_scopes = prior(scope_path)
    require(len(scopes['records']) == len(old_scopes['records']) + 1
            and scopes['records'][:-1] == old_scopes['records'], 'An earlier completed scope record changed')
    require({k: v for k, v in scopes.items() if k not in ['reviewed_on', 'records']}
            == {k: v for k, v in old_scopes.items() if k not in ['reviewed_on', 'records']}, 'Scope-review policy or raw-source binding changed')
    scope = scopes['records'][-1]
    require(scope['heritage_id'] == 'sh-historic-b2-012' and scope['source_name'] == '旧市博物馆', 'Wrong appended heritage scope')
    require([r['id'] for r in scope['completed_models']] == [ID], 'Wrong model in completed scope')
    require([r['id'] for r in scope['remaining_tasks']] == REMAINING_IDS
            and [r['title'] for r in scope['remaining_tasks']] == REMAINING_TITLES, 'Museum must keep exactly the two specific investigations')
    require(all(r['todo'] and not r.get('completed_by_model_id') for r in scope['remaining_tasks']), 'Museum investigations were retired')
    require('简化估计体量' in scope['completed_models'][0]['scope'] and '细部未核' in scope['completed_models'][0]['scope'], 'Rear-hall uncertainty is missing')
    require('510/1262' in scope['exclusions'] and '不关闭整条b2-012' in scope['exclusions'], 'Independent courts or active heritage scope lost')
    completed_ids = {r['id'] for r in delivered}
    hidden = [r for r in scopes['records'] if not [t for t in r['remaining_tasks']
              if t.get('completed_by_model_id') not in completed_ids]]
    require(len(hidden) == 10 and scope not in hidden, 'Whole museum heritage entry must remain active')

    heritage = document(PREFIX + 'data/model-todo/discovered-buildings.json')['records']
    named = document(PREFIX + 'data/model-todo/named-map-leads.json')['records']
    roads = document(PREFIX + 'data/model-todo/discovered-streets.json')['roads']
    require((len(heritage), len(named), len(roads)) == (1058, 1036, 1038), 'Original discovery counts changed')
    require(len(heritage) - len(hidden) == 1048, 'Unexpected active heritage count')
    require(next(r for r in heritage if r['id'] == scope['heritage_id'])['name'] == scope['source_name'], 'Museum heritage source name differs')
    require(not {MAIN_UUID, GATE_UUID} & {r['id'] for r in named}, 'Museum sources unexpectedly exist in frozen named snapshot')
    # Match the builder's identity semantics: top-level source_feature_ids plus
    # precise overrides. Site replacement is checked above as replacement scope.
    associations = {(layer, source) for row in catalog['models']
                    for layer, sources in row['source_feature_ids'].items() for source in sources}
    precise = document(PREFIX + 'data/precise-buildings-v6.json')['landmarks']
    for row in precise:
        if row['id'] in ids:
            associations.update(('building', s) for s in row.get('building_ids', []))
            associations.update(('building_part', s) for s in row.get('building_part_ids', []))
    associated = [r for r in named if (r['source_layer'], r['id']) in associations]
    require(len(associated) == 19 and len(named) - len(associated) == 1017, 'Named-source identity counts changed')

    raw_unchanged = []
    for suffix in ['discovered-buildings.json', 'named-map-leads.json', 'discovered-streets.json', 'STREETS.md']:
        path = PREFIX + 'data/model-todo/' + suffix
        require(read(path) == git('show', BASELINE + ':' + path), 'Original discovery changed: ' + path)
        raw_unchanged.append(path)
    audit_changes = git('diff', '--name-only', BASELINE, '--', PREFIX + 'data/audit').decode().splitlines()
    audit_untracked = git('ls-files', '--others', '--exclude-standard', '--', PREFIX + 'data/audit').decode().splitlines()
    navigation_paths, navigation_summary = verify_readme_navigation_exception(
        root, git, ids, {row['id'] for row in legacy}, bindings)
    require(all(path.startswith(AUDIT_PREFIX) or path in navigation_paths or path in NAVIGATION_FILES
                for path in audit_changes + audit_untracked),
            'An audit changed outside museum delivery and the exact reviewed navigation exception')
    require({path for path in audit_changes + audit_untracked if path.startswith(NAVIGATION_PREFIX)}
            == set(NAVIGATION_FILES), 'The navigation audit must contain exactly the two reviewed files')

    viewer_path = PREFIX + 'data/model-viewers.json'
    viewers = document(viewer_path)
    require([r for r in viewers if r['id'] != ID] == prior(viewer_path), 'An old auxiliary viewer entry changed')
    museum_viewers = [r for r in viewers if r['id'] == ID]
    require(len(museum_viewers) == 1 and museum_viewers[0]['page'] == 'city-museum.html'
            and museum_viewers[0]['model_walk'] is False, 'Wrong museum auxiliary viewer entry')
    placements_path = PREFIX + 'data/global-models/additional-placement.json'
    placements = document(placements_path)
    old_placements = prior(placements_path)
    require(placements['records'][:-1] == old_placements['records']
            and placements['source_contracts'][:-1] == old_placements['source_contracts'], 'An old placement or source contract changed')
    footprint_path = AUDIT_PREFIX + 'footprint-review.json'
    footprint = document(footprint_path)
    require(placements['records'][-1] == footprint['proposed_placement_contract'], 'Final placement differs from public footprint review')
    require(placements['records'][-1]['id'] == ID
            and footprint['runtime_validation']['final_model_geometry_verified'] is True, 'Final footprint gate did not pass')
    require(placements['source_contracts'][-1] == {
        'file': 'data/audit/city-museum-v1/footprint-review.json', 'bytes': len(read(footprint_path)),
        'sha256': digest(read(footprint_path)), 'record': 'proposed_placement_contract'}, 'Footprint source binding is stale')

    directories = []
    for path in ['README.md', PREFIX + 'README.md']:
        raw = read(path)
        text = raw.decode()
        if path == 'README.md':
            require(len(raw) < 500000, 'Root README exceeds500000bytes')
            todo = text.split('<!-- model-todo:start -->')[1].split('<!-- model-todo:end -->')[0]
            active = todo.split('### 按顺序执行的模型')[1].split('### 按区列出的未完成建筑与构件 TODO')[0]
            require(len(re.findall(r'^\| \d+ \|', active, re.M)) == 1 and '| 36 |' in active,
                    'Root README must show only order36 in active production')
            require('剩余1017条／已关联19条' in todo, 'Root README named-source counts are stale')
            require(len(re.findall(r'^\| sh-historic-', todo, re.M)) == 1048, 'Wrong active heritage row count')
            museum_rows = re.findall(r'^\| sh-historic-b2-012 \|.*$', todo, re.M)
            require(len(museum_rows) == 1 and all(title in museum_rows[0] for title in REMAINING_TITLES),
                    'Museum active heritage row must list the two remaining investigations')
        section = text.split('## 按区查看主要建筑\n')[1].split('\n## ')[0]
        groups = re.findall(r'^### (.+?)（(\d+)处）', section, re.M)
        rows = re.findall(r'\[查看网页\]\((https://[^)]+#landmark=([^&]+)&mode=(walk|overview))\)', section)
        require(len(groups) == 16 and sum(int(n) for _, n in groups) == 81, 'Wrong district count or total')
        require(dict(groups)['黄浦区'] == '28' and dict(groups)['杨浦区'] == '6', 'Wrong Huangpu/Yangpu totals')
        require(len(rows) == 81 and {r[1] for r in rows} == ids, 'District directory IDs differ from global viewer catalog')
        require(Counter(r[2] for r in rows) == {'walk': 40, 'overview': 41}, 'Wrong walk/overview link totals')
        all_view_links = re.findall(r'\[查看网页\]\(([^)]+)\)', text)
        require(bool(all_view_links), 'No README view links found')
        checked_model_links = 0
        for url in all_view_links:
            parsed = urlsplit(url)
            require(parsed.scheme == 'https' and parsed.netloc == 'raw.githack.com'
                    and parsed.path == '/ecojust/e-resource/master/projects/shanghai/index.html',
                    'README view link bypasses the global index: ' + url)
            if parsed.fragment:
                values = parse_qs(parsed.fragment)
                if 'landmark' in values:
                    require(len(values['landmark']) == 1 and values['landmark'][0] in ids, 'README links to an unregistered model')
                    expected_mode = 'walk' if values['landmark'][0] in {r['id'] for r in legacy} else 'overview'
                    require(values.get('mode') == [expected_mode], 'README mode differs from model navigation')
                    checked_model_links += 1
        directories.append({'path': path, 'bytes': len(raw), 'sha256': digest(raw), 'models': 81,
                            'districts': 16, 'huangpu': 28, 'yangpu': 6,
                            'all_view_links_to_global_index': len(all_view_links), 'checked_model_links': checked_model_links})
    require(read(PREFIX + 'index.html').count(b'id="landmark-count">81</span>') == 1, 'Static index destination count is stale')
    report = {
        'schema': 'city-museum-todo-directory-checks-v1', 'passed': True, 'baseline_commit': BASELINE,
        'completed_production_jobs': 35, 'existing_models_omitted_from_active_todo': 46,
        'active_production_id': NEXT_ID, 'heritage_active_rows': 1048,
        'heritage_completed_main_buildings_omitted': 10, 'named_identity_associations': 19, 'named_active_rows': 1017,
        'global_models': 81, 'legacy_models': 40, 'candidate_models': 41,
        'candidate_manifests': 43, 'asset_files': 172, 'asset_bytes': OLD_ASSET_BYTES + new_asset_bytes,
        'museum_remaining_task_ids': REMAINING_IDS, 'all_prior_completed_scope_records_unchanged': True,
        'old_40_candidate_records_unchanged': True, 'old_42_inventory_records_unchanged': True,
        'historical_audit_data_unchanged': True,
        'historical_audits_unchanged_except_exact_navigation_readmes': True,
        'readme_navigation_exception': navigation_summary, 'raw_data_unchanged': raw_unchanged,
        'directories': directories, 'bindings': bindings,
        'scope': 'Main1860 current footprint and overlapping gate1931 are registered. West facade, wings and gate are detailed; the eastern central rear hall remains a simplified estimated volume with extent, age and details unverified. Small court sources510/1262 remain independent. Exactly two new heritage investigations remain active, and every earlier scope record remains unchanged.'}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'models': 81, 'heritage_active': 1048, 'named_active': 1017,
                      'active_production_id': NEXT_ID}))


if __name__ == '__main__':
    main()
