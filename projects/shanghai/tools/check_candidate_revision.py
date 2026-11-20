"""Check a geometry revision against the last published scene and the archived original delivery."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task')
    parser.add_argument('baseline')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', args.baseline+'^{commit}'], cwd=REPO, text=True).strip()

    def old(path):
        return json.loads(subprocess.check_output(['git', 'show', f'{commit}:projects/shanghai/{path}'], cwd=REPO))

    def read(path):
        return json.loads((PROJECT / path).read_bytes())

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def one(rows, ident):
        row, = [row for row in rows if row['id'] == ident]
        return row

    job = one(read('data/model-todo/queue.json')['production_queue'], args.task)
    model_id = job['refines_existing_model']
    manifest_path = REPO / job['manifest']
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest['id'] == model_id and manifest['viewer_page'] == Path(job['preview_source']).name
    assert job['preview'].endswith('#landmark='+model_id+'&mode=overview')
    inventory_path = 'data/global-models/candidate-inventory.json'
    inventory = read(inventory_path)
    assert inventory == old(inventory_path)
    original = one(inventory['records'], model_id)
    assert digest(PROJECT/original['manifest']) == original['manifest_sha256']
    prior_rows = {}
    allowed = {
        'data/candidate-city-integrations.json': ('models', {
            'assets','bounds_glb','candidate_manifest','model','lod_model','web_bytes','web_sha256','lod_bytes',
            'lod_sha256','triangles','lod_triangles','model_scope','model_geometry_sha256'}),
        'data/global-models/additional-placement.json': ('records', {
            'revised_delivery','model_manifest_sha256','model_geometry_sha256','model_scope'}),
        'data/model-viewers.json': (None, {'description','manifest'}),
    }
    for path, (key,fields) in allowed.items():
        previous, current = old(path), read(path)
        before, after = (previous[key],current[key]) if key else (previous,current)
        assert [r['id'] for r in before] == [r['id'] for r in after], path
        assert [r for r in before if r['id'] != model_id] == [r for r in after if r['id'] != model_id], path
        a,b = one(before,model_id),one(after,model_id)
        changed = {k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
        assert changed and changed <= fields, (path,changed-fields)
        prior_rows[path] = len(before)-1
    city = read('data/candidate-city-integrations.json')
    model = one(city['models'],model_id)
    assert model['candidate_manifest'] == manifest_path.relative_to(PROJECT).as_posix()
    placements=read('data/global-models/additional-placement.json')
    row=one(placements['records'],model_id)
    contract=placements['source_contracts'][-1]
    proof=PROJECT/contract['file']
    assert read(contract['file'])==row and proof.stat().st_size==contract['bytes'] and digest(proof)==contract['sha256']
    new_binding=row['revised_delivery']
    assert new_binding['original_manifest_sha256']==original['manifest_sha256']
    assert digest(manifest_path)==new_binding['sha256']==row['model_manifest_sha256']
    assert row['bounds_glb']==one(old('data/global-models/additional-placement.json')['records'],model_id)['bounds_glb']
    for role,asset in manifest['assets'].items():
        path=manifest_path.parent/asset['file']
        assert path.stat().st_size==asset['bytes'] and digest(path)==asset['sha256']
        key='web' if role=='full' else role
        assert path.relative_to(PROJECT).as_posix()!=original['assets'][key]['file']
        if key in model['assets']:
            selected=model['assets'][key]
            assert selected['file']==path.relative_to(PROJECT).as_posix() and selected['sha256']==asset['sha256']
    assert read('data/landmarks.json')==old('data/landmarks.json')
    directory=read('data/landmarks.json')+city['models']
    assert len({r['id'] for r in directory})==len(directory)==city['resulting_city_count']==old('data/candidate-city-integrations.json')['resulting_city_count']
    district=sum(r['districtId']==model['districtId'] for r in directory)
    for doc in (REPO/'README.md',PROJECT/'README.md'):
        section=doc.read_text().split(f"### {job['district']}（{district}处）",1)[1].split('\n### ',1)[0]
        assert section.count(f"[查看网页]({job['preview']})")==1
    result=dict(model=model_id,task=args.task,passed=True,baseline_commit=commit,
                checked_at_utc=datetime.now(timezone.utc).isoformat(),other_records_preserved=prior_rows,
                navigation_entries=len(directory),district=job['district'],district_entries=district,
                manifest_sha256=digest(manifest_path),placement_sha256=digest(proof),checker_sha256=digest(Path(__file__)))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
