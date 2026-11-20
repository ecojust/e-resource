"""Verify a released Shanghai model and its public links against a Git commit."""
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

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
PREFIX = PROJECT.relative_to(REPO).as_posix() + '/'
BASE = 'https://raw.githack.com/ecojust/e-resource/'
fetch = runpy.run_path(str(PROJECT / 'data/audit/country-hospital-v1/check-publication.py'))['public_bytes']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model')
    parser.add_argument('commit')
    parser.add_argument('--ref', help='Use master to inspect the changing branch cache')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', args.commit + '^{commit}'], cwd=REPO, text=True).strip()
    def blob(path):
        return subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=REPO)
    ref = args.ref or commit
    def path(url):
        return urlsplit(url).path
    manifest_path = PREFIX + 'assets/models/candidates/' + args.model + '/manifest.json'
    manifest = json.loads(blob(manifest_path))
    assert manifest['id'] == args.model and set(manifest['assets']) == {'raw', 'full', 'lod', 'native'}
    queue = json.loads(blob(PREFIX + 'data/model-todo/queue.json'))
    job, = [j for j in queue['production_queue'] if j['id'] == args.model]
    files = ['README.md', job['evidence'], PREFIX + 'README.md', PREFIX + 'CURRENT_STATE.md',
             PREFIX + 'landmarks.html', PREFIX + 'index.html', PREFIX + manifest['viewer_page'],
             PREFIX + 'data/model-todo/queue.json', PREFIX + 'data/model-viewers.json',
             PREFIX + 'data/global-models/additional-placement.json', manifest_path,
             PREFIX + 'source/precise/' + args.model + '/README.md', PREFIX + manifest['source_register']]
    viewer = PREFIX + manifest['viewer_page']
    viewer_html = blob(viewer).decode()
    local_modules = re.findall(r"""(?:from\s*['"]\./|<script type="module" src=")(src/[a-z0-9-]+\.js(?:\?[^'"]*)?)""", viewer_html)
    local_styles = re.findall(r'<link rel="stylesheet" href="(src/[^"]+)"', viewer_html)
    assert local_modules and local_styles, 'Standalone viewer must include its released script and stylesheet'
    files.extend(urljoin(viewer, relative) for relative in (*local_modules, *local_styles))
    entry, = re.findall(r'<script type="module" src="([^"]+)"', blob(PREFIX + 'index.html').decode())
    app = PREFIX + entry
    app_source = blob(path(app)).decode()
    files.append(app)
    def include_import(source_url, code, module):
        relative, = re.findall(r"""from\s*['"](\./""" + re.escape(module) + r"""\.js(?:\?[^'"]*)?)['"]""", code)
        url = urljoin(source_url, relative)
        files.append(url)
        return url
    include_import(app, app_source, 'candidate-overview-camera')
    scene = include_import(app, app_source, 'map-scene')
    catalog_module = include_import(app, app_source, 'candidate-city-integrations')
    scene_code = blob(path(scene)).decode()
    if './ordinary-scene-adapter.js' in scene_code:
        adapter = include_import(scene, scene_code, 'ordinary-scene-adapter')
        adapter_code = blob(path(adapter)).decode()
        include_import(adapter, adapter_code, 'ordinary-building-catalog')
        include_import(adapter, adapter_code, 'ordinary-asset-verification')
        include_import(app, app_source, 'ordinary-building-catalog')
    for name in ['candidate-city-clipping', 'building-beacons']:
        include_import(scene, scene_code, name)
    catalog_code = blob(path(catalog_module)).decode()
    include_import(catalog_module, catalog_code, 'candidate-source-sections')
    if './candidate-vector-geometry.js' in catalog_code:
        vector_module = include_import(scene, scene_code, 'candidate-vector-clipping')
        include_import(vector_module, blob(path(vector_module)).decode(), 'candidate-vector-geometry')
        include_import(catalog_module, catalog_code, 'candidate-vector-geometry')
    if './historical-view.js' in app_source:
        include_import(app, app_source, 'historical-view')
        include_import(catalog_module, catalog_code, 'historical-view')
        include_import(app, app_source, 'precise-registration-ui')
        stylesheet, = re.findall(r'<link rel="stylesheet" href="(src/historical-view\.css(?:\?[^"]*)?)"', blob(PREFIX + 'index.html').decode())
        files.append(PREFIX + stylesheet)
    query, = re.findall(r"candidate-city-integrations\.json'\?'(\?[^']+)'", app_source)
    files.append(PREFIX + 'data/candidate-city-integrations.json' + query)
    assets = {urljoin(manifest_path, a['file']): a for a in manifest['assets'].values()}
    records = []
    for file in dict.fromkeys([*files, *assets]):
        local = blob(path(file))
        size, digest = len(local), hashlib.sha256(local).hexdigest()
        if file in assets:
            assert (size, digest) == (assets[file]['bytes'], assets[file]['sha256'])
        records.append(dict(path=path(file), url=BASE + ref + '/' + file, expected_bytes=size, expected_sha256=digest))
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r, result in zip(records, pool.map(fetch, [r['url'] for r in records])):
            r['response'] = result
            r['matches_commit'] = (result.get('status'), result.get('bytes'), result.get('sha256')) == (200, r['expected_bytes'], r['expected_sha256'])
    passed = all(r['matches_commit'] for r in records)
    report = dict(model=args.model, commit=commit, http_ref=ref, checked_at_utc=datetime.now(timezone.utc).isoformat(),
                  checked_files=len(records), passed=passed, verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  direct_view=BASE + ref + '/' + PREFIX + 'index.html#landmark=' + args.model + '&mode=overview', records=records)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'count': len(records), 'failed': [r['path'] for r in records if not r['matches_commit']]}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
