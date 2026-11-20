"""Verify a refinement in the existing Bund landmark, LOD, and model directories."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
PREFIX = PROJECT.relative_to(REPO).as_posix() + '/'


def one(rows, ident):
    row, = [item for item in rows if item['id'] == ident]
    return row


def registry_paths(ident):
    return ['data/landmarks.json', 'data/bund/manifest.json', 'data/bund/lod-v4.json',
            f'data/bund/models/{ident}-web.json', f'data/bund/models/{ident}.json']


def assets_match(read, manifest, path):
    """Read live production files or committed objects using the same contracts."""
    model = manifest['id']
    assert manifest['url_base'] == 'project-root'
    documents = [json.loads(read(name)) for name in registry_paths(model)]
    landmarks, manifest_dir, lod_dir, web, raw = documents
    lm, entry, lod = one(landmarks, model), one(manifest_dir['buildings'], model), one(lod_dir['models'], model)
    assert all(row['asset_revision_manifest'] == path for row in (lm, entry, lod, web, raw))
    assert lm['candidate_id'] == entry['candidate_id'] == web['candidate_id'] == raw['candidateId'] == model
    roles = {'raw': ('editable_model','raw'), 'full': ('model','web'), 'lod': ('lod_model','lod'), 'native': ('native_model','native')}
    assert set(manifest['assets']) == set(roles)
    for role, (field, alias) in roles.items():
        asset = manifest['assets'][role]
        assert f'/revisions/{model}/{manifest["revision"]}/' in asset['file']
        for row in (lm, entry, web):
            assert (row[field], row[alias+'_sha256'], row[alias+'_bytes']) == (asset['file'], asset['sha256'], asset['bytes'])
        body = read(asset['file'])
        assert (len(body), hashlib.sha256(body).hexdigest()) == (asset['bytes'], asset['sha256'])
    assert (lod['model'],lod['sha256'],lod['triangles']) == (lm['lod_model'],lm['lod_sha256'],lm['lod_triangles'])
    assert (raw['model'],raw['native_model'],raw['triangles']) == (lm['editable_model'],lm['native_model'],lm['triangles'])
    return documents, lm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task')
    parser.add_argument('baseline')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    baseline = subprocess.check_output(['git','rev-parse','--verify',args.baseline+'^{commit}'],cwd=REPO,text=True).strip()
    def read(path):
        return (PROJECT / path).read_bytes()
    def prior(path):
        return json.loads(subprocess.check_output(['git','show',f'{baseline}:{PREFIX}{path}'],cwd=REPO))
    job = one(json.loads(read('data/model-todo/queue.json'))['production_queue'],args.task)
    ident = job['refines_existing_model']
    manifest = Path(job['manifest']).relative_to(PREFIX).as_posix()
    meta = json.loads(read(manifest))
    assert (meta['task_id'], meta['id']) == (args.task, ident)
    new, current = assets_match(read,meta,manifest)
    paths = registry_paths(ident)
    old = [prior(path) for path in paths]
    for before, after in [(old[0],new[0]),(old[1]['buildings'],new[1]['buildings']),(old[2]['models'],new[2]['models'])]:
        assert [r['id'] for r in before] == [r['id'] for r in after]
        assert [r for r in before if r['id'] != ident] == [r for r in after if r['id'] != ident]
    for key in ('lng','lat','bearing','walkStart','bounds_glb','height_m','districtId'):
        assert current.get(key) == one(old[0],ident).get(key), key
    for key in ('footprint','replaceExactBuildingIds'):
        assert new[4][key] == old[4][key]
    for path in ('data/candidate-city-integrations.json','data/global-models/additional-placement.json',
                 'data/global-models/candidate-inventory.json','data/precise-buildings-v6.json','data/model-viewers.json'):
        assert json.loads(read(path)) == prior(path), path
    catalog = json.loads(read('data/candidate-city-integrations.json'))
    rows = new[0]+catalog['models']
    assert len(rows) == len({r['id'] for r in rows}) == catalog['resulting_city_count']
    district_count = sum(r['districtId'] == current['districtId'] for r in rows)
    for doc in (REPO/'README.md', PROJECT/'README.md'):
        sector = doc.read_text().split(f"### {job['district']}（{district_count}处）",1)[1].split('\n### ',1)[0]
        assert sector.count(f"[查看网页]({job['preview']})") == 1
    report = dict(passed=True,model=ident,task=args.task,baseline_commit=baseline,
                  checked_at_utc=datetime.now(timezone.utc).isoformat(),district=job['district'],district_entries=district_count,
                  navigation_entries=len(rows),unchanged_city_rows=len(rows)-1,registry_files=paths,
                  manifest_sha256=hashlib.sha256(read(manifest)).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    main()
