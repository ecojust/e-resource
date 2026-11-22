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
LEGACY_RAW_IDS = {'bund15': 'russo', 'bund18': 'bund18-chartered-bank'}


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
    assert lm['candidate_id'] == entry['candidate_id'] == web['candidate_id'] == model
    if 'candidateId' in raw:
        assert raw['candidateId'] == model
    else:
        assert raw['id'] == LEGACY_RAW_IDS[model]
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



def approved_roof_mast(meta):
    return (meta.get('task_id'),meta.get('id'),meta.get('revision')) == (
        'huangpu-bank-communications-roof-mast','bund14','roof-mast') and {
        k: v['sha256'] for k,v in meta['assets'].items()} == {'raw': '59518bcfcad1fe144b51d899e6b7baaece3fdabf27a3d30b493684d22fb01f6f', 'full': 'c799f449aba4503a9c4d73591705e3d4745aa226d18f6afbbc7f0b9f8c076927', 'lod': 'b8cd4071956a1ec73b7eefcbb5b404996bd07a94357dde874ebaed9d0ed0320a', 'native': 'ce43da60f357b347c74bd31a5dcdf24dddd69fff36d2a9e4c566844891405791'}

def checked_envelope(before,after,approved=False):
    if not approved:
        assert before == after, 'bounds_glb'
        return
    assert before['min'] == after['min']
    assert before['max'][0] == after['max'][0] and before['max'][2] == after['max'][2]
    assert abs(before['max'][1] - 33.4) < .00001
    assert after['max'][1] == 35.6766357421875

def check_raw_registration(before, after, model, roof=False):
    """Check original identity, map placement and any new canonical catalog alias."""
    for key in ('id', 'footprint', 'replaceExactBuildingIds', 'footprint_source', 'source_footprint',
                'groundPolygonLocalXZ', 'model_axis', 'anchor'):
        assert after.get(key) == before.get(key), key
    checked_envelope(before.get('bounds_glb'),after.get('bounds_glb'),roof)
    if 'candidateId' not in before and 'candidateId' in after:
        assert model in LEGACY_RAW_IDS and before['id'] == LEGACY_RAW_IDS[model]
        assert after['candidateId'] == model
    else:
        assert ('candidateId' in before) == ('candidateId' in after)
        assert after.get('candidateId') == before.get('candidateId')



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
    roof=approved_roof_mast(meta)
    old_target=one(old[0],ident)
    checked_envelope(old_target.get('bounds_glb'),current.get('bounds_glb'),roof)
    if roof:assert abs(old_target['height_m']-33.4)<.00001 and current['height_m']==meta['apex_m']==35.6766357421875
    else:assert old_target.get('height_m')==current.get('height_m')
    for key in ('lng','lat','bearing','walkStart','districtId'):
        assert current.get(key) == one(old[0],ident).get(key), key
    check_raw_registration(old[4], new[4], ident, roof)
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
