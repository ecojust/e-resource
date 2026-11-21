"""Verify one appended candidate against the immediately preceding city catalog."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('model')
    p.add_argument('baseline')
    p.add_argument('output', type=Path)
    args = p.parse_args()
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', args.baseline + '^{commit}'], cwd=REPO, text=True).strip()
    def read(path):
        return json.loads((PROJECT / path).read_bytes())
    def previous(path):
        return json.loads(subprocess.check_output(['git', 'show', f'{commit}:projects/shanghai/{path}'], cwd=REPO))
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    def selected(rows):
        row, = [r for r in rows if r['id'] == args.model]
        return row
    preserved = {}
    for path, key in [('data/candidate-city-integrations.json', 'models'), ('data/global-models/candidate-inventory.json', 'records'),
                      ('data/global-models/additional-placement.json', 'records'), ('data/model-viewers.json', None)]:
        old, new = previous(path), read(path)
        if key:
            old, new = old[key], new[key]
        assert [r for r in new if r['id'] != args.model] == old, path
        selected(new)
        preserved[path] = len(old)
    assert previous('data/landmarks.json') == read('data/landmarks.json')
    town = read('data/candidate-city-integrations.json')
    model = selected(town['models'])
    inventory = read('data/global-models/candidate-inventory.json')
    entry = selected(inventory['records'])
    manifest = PROJECT / entry['manifest']
    assert digest(manifest) == entry['manifest_sha256']
    assets = json.loads(manifest.read_bytes())['assets']
    for variant, asset in assets.items():
        path = manifest.parent / asset['file']
        key = 'web' if variant == 'full' else variant
        assert path == PROJECT / entry['assets'][key]['file']
        assert 0 < path.stat().st_size == asset['bytes'] < 100_000_000
        assert asset['sha256'] == entry['assets'][key]['sha256'] == digest(path)
        if key in model['assets']:
            assert model['assets'][key] == entry['assets'][key]
    placements = read('data/global-models/additional-placement.json')
    row = selected(placements['records'])
    binding = placements['source_contracts'][-1]
    proof = PROJECT / binding['file']
    assert proof.stat().st_size == binding['bytes'] and digest(proof) == binding['sha256']
    proposed = json.loads(proof.read_bytes())
    assert row == (proposed[binding['record']] if 'record' in binding else proposed)
    before, after = previous('data/model-todo/queue.json'), read('data/model-todo/queue.json')
    job = selected(after['production_queue'])
    assert before['existing_models'] == after['existing_models']
    for prior in before['production_queue']:
        if prior['order'] == job['order']:
            continue
        actual, = [r for r in after['production_queue'] if r['id'] == prior['id']]
        if prior['order'] == job['order'] + 1 and prior['status'] == 'todo' and actual['status'] == 'in_progress':
            assert actual == {**prior, 'status': 'in_progress'}
        else:
            assert actual == prior
    assert job['status'] in ('accepted', 'candidate_delivered')
    overview = job.get('city_integration', {}).get('preview', job['preview'])
    assert overview.endswith('#landmark=' + args.model + '&mode=overview')
    mode = 'walk' if row.get('bridge_walk') and row.get('navigation', {}).get('listed') else 'overview'
    assert job['preview'] == overview.removesuffix('overview') + mode
    if mode == 'walk':
        assert row.get('bridge_walk') == model.get('bridge_walk') and row.get('bridge_walk')
        assert job['city_integration']['walk_enabled'] and model['navigation'] == row['navigation']
        view = selected(read('data/model-viewers.json'))
        assert view['model_walk']
        directory_page = (PROJECT / 'landmarks.html').read_text()
        for suffix in ('walk', 'overview'):
            assert f'href="index.html#landmark={args.model}&amp;mode={suffix}"' in directory_page
    assert (REPO / job['manifest']).resolve() == manifest and (REPO / job['preview_source']).is_file()
    directory = read('data/landmarks.json') + town['models']
    assert len({r['id'] for r in directory}) == len(directory) == town['resulting_city_count']
    district_total = sum(r['districtId'] == model['districtId'] for r in directory)
    for doc in (REPO / 'README.md', PROJECT / 'README.md'):
        district_rows = doc.read_text().split(f"### {job['district']}（{district_total}处）", 1)[1].split('\n### ', 1)[0]
        assert district_rows.count(f"[查看网页]({overview})") == 1
        if mode == 'walk':
            assert district_rows.count(f"[漫游]({job['preview']})") == 1
    scope, = [r for r in read('data/model-todo/completed-model-scope-review.json')['records'] if r['heritage_id'] == job['heritage_record_id']]
    assert selected(scope['completed_models'])['scope'] == job['scope']
    assert scope['remaining_tasks']
    result = dict(model=args.model, checked_at_utc=datetime.now(timezone.utc).isoformat(), passed=True,
                  baseline_commit=commit, existing_rows_preserved=preserved, navigation_entries=len(directory),
                  district=job['district'], district_entries=district_total, inventory_files=inventory['verification']['files'],
                  manifest_sha256=digest(manifest), placement_sha256=digest(proof), checker_sha256=digest(Path(__file__)))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
