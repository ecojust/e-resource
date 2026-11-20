"""Check the public files and scene code used by an in-place Bund building revision."""
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

from check_bund_revision import PROJECT, REPO, PREFIX, assets_match, one, registry_paths

BASE = 'https://raw.githack.com/ecojust/e-resource/'
fetch = runpy.run_path(str(PROJECT/'data/audit/country-hospital-v1/check-publication.py'))['public_bytes']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task')
    parser.add_argument('commit')
    parser.add_argument('--ref')
    parser.add_argument('--output', required=True,type=Path)
    args = parser.parse_args()
    commit = subprocess.check_output(['git','rev-parse','--verify',args.commit+'^{commit}'],cwd=REPO,text=True).strip()
    def blob(path):
        return subprocess.check_output(['git','show',f'{commit}:{urlsplit(path).path}'],cwd=REPO)
    job = one(json.loads(blob(PREFIX+'data/model-todo/queue.json'))['production_queue'],args.task)
    ident = job['refines_existing_model']
    source = Path(job['manifest']).parent
    metadata = json.loads(blob(job['manifest']))
    assert metadata['id'] == ident and metadata['task_id'] == args.task
    assets_match(lambda path: blob(PREFIX+path),metadata,Path(job['manifest']).relative_to(PREFIX).as_posix())
    urls = ['README.md',job['manifest'],job['evidence'],str(source/'README.md')]
    files = [*registry_paths(ident),'README.md','CURRENT_STATE.md','index.html','landmarks.html',
             'data/model-todo/queue.json','data/candidate-city-integrations.json',
             *(a['file'] for a in metadata['assets'].values())]
    urls.extend(PREFIX+f for f in files)
    entrypoint, = re.findall(r'<script type="module" src="([^"]+)"',blob(PREFIX+'index.html').decode())
    app = PREFIX+entrypoint
    urls.append(app)
    def dependency(origin, name):
        pattern=r"""from\s*['"](\./"""+re.escape(name)+r"""\.js(?:\?[^'"]*)?)['"]"""
        relative,=re.findall(pattern,blob(origin).decode())
        url=urljoin(origin,relative)
        urls.append(url)
        return url
    scene = dependency(app, 'map-scene')
    for module in ('candidate-overview-camera','candidate-city-integrations','historical-view'):
        dependency(app,module)
    for module in ('building-beacons','candidate-city-clipping','ordinary-scene-adapter'):
        dependency(scene,module)
    urls.extend(scene_metadata_urls(app, blob(app).decode(), PREFIX))
    records = []
    ref = args.ref or commit
    for url in dict.fromkeys(urls):
        data = blob(url)
        records.append(dict(path=urlsplit(url).path,url=BASE+ref+'/'+url,expected_bytes=len(data),
                            expected_sha256=hashlib.sha256(data).hexdigest()))
    with ThreadPoolExecutor(max_workers=6) as pool:
        for record, result in zip(records,pool.map(fetch,[r['url'] for r in records])):
            record['response'] = result
            record['matches_commit'] = (result.get('status'),result.get('bytes'),result.get('sha256')) == (200,record['expected_bytes'],record['expected_sha256'])
    passed = all(r['matches_commit'] for r in records)
    report = dict(passed=passed,model=args.task,landmark_id=ident,commit=commit,http_ref=ref,checked_files=len(records),
                  checked_at_utc=datetime.now(timezone.utc).isoformat(),direct_view=BASE+ref+'/'+PREFIX+f'index.html#landmark={ident}&mode=walk',
                  verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),records=records)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
