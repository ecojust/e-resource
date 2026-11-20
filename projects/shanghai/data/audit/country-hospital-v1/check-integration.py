"""Verify the hospital increment against the last postal-office registry."""
from datetime import datetime, timezone
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', help='Git revision immediately preceding this model')
    args = parser.parse_args()
    audit = Path(__file__).resolve().parent
    project = audit.parents[2]
    repo = project.parents[1]
    model_id = 'jingan-country-hospital'

    def read(path):
        return json.loads((project / path).read_bytes())

    def old(path):
        relative = (project / path).relative_to(repo)
        return json.loads(subprocess.check_output(['git', 'show', f'{args.baseline}:{relative}'], cwd=repo))

    records = {}
    for file, key in [('data/candidate-city-integrations.json', 'models'),
                      ('data/global-models/candidate-inventory.json', 'records'),
                      ('data/global-models/additional-placement.json', 'records')]:
        previous = old(file)[key]
        current = read(file)[key]
        assert current[:-1] == previous, file
        assert current[-1]['id'] == model_id and len({r['id'] for r in current}) == len(current)
        records[file] = {'unchanged_records': len(previous), 'new_records': 1,
                         'sha256': sha256((project / file).read_bytes()).hexdigest()}
    legacy_file = 'data/landmarks.json'
    assert old(legacy_file) == read(legacy_file) and len(read(legacy_file)) == 40
    town = read('data/candidate-city-integrations.json')
    inventory = read('data/global-models/candidate-inventory.json')
    assert town['resulting_city_count'] == 85 and inventory['verification']['files'] == 188
    model = town['models'][-1]
    assert model['districtId'] == '310106' and model['partial_model'] and not model['navigation']['listed']
    assert sum(r['districtId'] == '310106' for r in read(legacy_file) + town['models']) == 2
    placements = read('data/global-models/additional-placement.json')
    binding = placements['source_contracts'][-1]
    evidence_path = project / binding['file']
    assert binding['sha256'] == sha256(evidence_path.read_bytes()).hexdigest()
    assert binding['bytes'] == evidence_path.stat().st_size
    proposed = read(binding['file'])[binding['record']]
    assert proposed == placements['records'][-1]
    assert model['source_section_caps'] == proposed['source_section_caps']
    inventory_entry = inventory['records'][-1]
    manifest_path = project / inventory_entry['manifest']
    manifest = json.loads(manifest_path.read_bytes())
    assert inventory_entry['manifest_sha256'] == sha256(manifest_path.read_bytes()).hexdigest()
    for role, asset in manifest['assets'].items():
        key = 'web' if role == 'full' else role
        path = manifest_path.parent / asset['file']
        assert path == project / inventory_entry['assets'][key]['file']
        actual = path.read_bytes()
        assert len(actual) == asset['bytes'] < 100_000_000 and sha256(actual).hexdigest() == asset['sha256']
        assert inventory_entry['assets'][key]['sha256'] == asset['sha256']
        if key in model['assets']:
            assert model['assets'][key] == inventory_entry['assets'][key]
    queue_file = 'data/model-todo/queue.json'
    before, after = old(queue_file), read(queue_file)
    assert after['existing_models'] == before['existing_models']
    jobs = after['production_queue']
    assert jobs[:38] == before['production_queue'][:38] and jobs[38]['id'] == model_id
    assert jobs[38]['status'] == 'candidate_delivered' and jobs[38]['preview'].endswith('#landmark=' + model_id + '&mode=overview')
    remaining = jobs[39]
    assert remaining['heritage_record_id'] == jobs[38]['heritage_record_id']
    assert remaining['order'] == 40 and remaining['status'] == 'reference_pending'
    scopes = read('data/model-todo/completed-model-scope-review.json')
    review, = [r for r in scopes['records'] if r['heritage_id'] == jobs[38]['heritage_record_id']]
    assert review['remaining_tasks'] and review['completed_models'][0]['id'] == model_id
    for path in (repo / 'README.md', project / 'README.md'):
        district = path.read_text().split('### 静安区（2处）', 1)[1].split('\n### ', 1)[0]
        direct = f"[查看网页]({jobs[38]['preview']})"
        row, = [line for line in district.splitlines() if direct in line]
        assert row.startswith('| ' + model['name'] + ' |')
    result = {'model_id': model_id, 'passed': True, 'baseline_commit': args.baseline,
              'scope': 'Local metadata increment, asset receipts, bounded model and active remaining work; browser and public HTTP checked separately.',
              'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'script_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'records': records, 'unchanged_legacy_models': 40, 'unchanged_preceding_jobs': 38,
              'destinations': 85, 'jingan_destinations': 2, 'asset_files': 188,
              'next_job': remaining['id'], 'manifest_sha256': inventory_entry['manifest_sha256']}
    (audit / 'catalog-preservation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
