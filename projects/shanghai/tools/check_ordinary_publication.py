"""Check the publicly hosted files for an in-place revision of an ordinary architectural model."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess
from urllib.parse import urljoin, urlsplit

from public_scene_metadata import scene_metadata_urls

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
PREFIX = PROJECT.relative_to(REPO).as_posix()+'/'
BASE = 'https://raw.githack.com/ecojust/e-resource/'
fetch = runpy.run_path(str(PROJECT/'data/audit/country-hospital-v1/check-publication.py'))['public_bytes']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task')
    parser.add_argument('commit')
    parser.add_argument('--ref')
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    commit=subprocess.check_output(['git','rev-parse','--verify',args.commit+'^{commit}'],cwd=REPO,text=True).strip()
    ref=args.ref or commit

    def blob(name):
        return subprocess.check_output(['git','show',f'{commit}:{urlsplit(name).path}'],cwd=REPO)

    def data(name):
        return json.loads(blob(PREFIX+name))

    def one(records,ident):
        row,=[r for r in records if r['id']==ident]
        return row

    def check_bytes(binding):
        value=blob(PREFIX+binding['file'])
        assert len(value)==binding['bytes'] and hashlib.sha256(value).hexdigest()==binding['sha256'],binding['file']

    queue=data('data/model-todo/queue.json')
    job=one(queue['production_queue'],args.task)
    landmark=job['refines_existing_model']
    manifest=json.loads(blob(job['manifest']))
    assert re.fullmatch(r'[a-z0-9-]+',landmark) and manifest['id']==landmark
    assert re.fullmatch(r'[a-z0-9-]+',manifest['revision']) and manifest['url_base']=='project-root'
    assert job['manifest']==PREFIX+'source/precise/'+landmark+'/revisions/'+manifest['revision']+'/manifest.json'
    sources=Path(job['manifest']).parent.as_posix()+'/README.md'
    static=data('data/landmarks.json')
    model=one(static,landmark)
    register='data/precise-buildings-v6.json'
    top=data(register)
    ordinary=top['ordinary_catalog'];check_bytes(ordinary)
    pointer=data('data/precise-buildings/by-id/'+landmark+'.json')
    assert pointer['feature_local_id']==model['owner']['feature_local_id']
    entry=one(data(ordinary['file'])['macros'],pointer['macro_id']);check_bytes(entry)
    assert entry['file']==pointer['macro_index']
    shard=data(entry['file'])
    assert one(shard['models'],landmark)==model==data('data/precise-candidates/'+landmark+'.json')
    check_bytes(shard['replacement_registry'])
    files=['README.md',PREFIX+'README.md',PREFIX+'CURRENT_STATE.md',job['evidence'],job['manifest'],sources]
    files += [PREFIX+name for name in ('index.html','landmarks.html','data/landmarks.json','data/model-todo/queue.json',
                'data/candidate-city-integrations.json',register,ordinary['file'],entry['file'],shard['replacement_registry']['file'],
                'data/precise-candidates/'+landmark+'.json','data/precise-buildings/by-id/'+landmark+'.json')]
    assert set(manifest['assets'])=={'raw','full','lod','native'}
    for role,item in manifest['assets'].items():
        contract=model['assets']['web' if role=='full' else role]
        assert all(item[k]==contract[k] for k in ('file','bytes','sha256'))
        check_bytes(item)
        files.append(PREFIX+item['file'])
    entrypoint,=re.findall(r'<script type="module" src="([^"]+)"',blob(PREFIX+'index.html').decode())
    app=PREFIX+entrypoint
    files.append(app)

    def imported(origin,module):
        pattern=r"""from\s*['"](\./"""+re.escape(module)+r"""\.js(?:\?[^'"]*)?)['"]"""
        relative,=re.findall(pattern,blob(origin).decode())
        name=urljoin(origin,relative);files.append(name)
        return name

    scene=imported(app,'map-scene')
    adapter=imported(scene,'ordinary-scene-adapter')
    imported(adapter,'ordinary-building-catalog')
    imported(adapter,'ordinary-asset-verification')
    imported(app,'ordinary-building-catalog')
    imported(app,'candidate-city-integrations')
    imported(app,'candidate-overview-camera')
    files.extend(scene_metadata_urls(app, blob(app).decode(), PREFIX))
    for binding in (ordinary, entry, shard['replacement_registry']):
        files.append(PREFIX + binding['file'] + '?sha256=' + binding['sha256'])
    records=[]
    for name in dict.fromkeys(files):
        local=blob(name)
        records.append(dict(path=urlsplit(name).path,url=BASE+ref+'/'+name,expected_bytes=len(local),
                            expected_sha256=hashlib.sha256(local).hexdigest()))
    with ThreadPoolExecutor(max_workers=6) as pool:
        for record,actual in zip(records,pool.map(fetch,[r['url'] for r in records])):
            record['response']=actual
            record['matches_commit']=(actual.get('status'),actual.get('bytes'),actual.get('sha256'))==(200,record['expected_bytes'],record['expected_sha256'])
    passed=all(r['matches_commit'] for r in records)
    report=dict(model=args.task,landmark_id=landmark,commit=commit,http_ref=ref,passed=passed,checked_files=len(records),
                checked_at_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                direct_view=BASE+ref+'/'+PREFIX+'index.html#landmark='+landmark+'&mode=walk',records=records)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=passed,count=len(records),failed=[r['path'] for r in records if not r['matches_commit']])))
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
