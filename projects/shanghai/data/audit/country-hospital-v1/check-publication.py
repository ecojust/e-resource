"""Compare public Country Hospital pages, runtime modules and download bytes to a Git commit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT = 'projects/shanghai/'
MODEL = 'jingan-country-hospital'
BASE = 'https://raw.githack.com/ecojust/e-resource/'
TAG = '?v=country-hospital-v1'
FILES = [
    'README.md', 'CURRENT_STATE.md', 'index.html', 'landmarks.html', 'country-hospital.html',
    'src/app.js' + TAG, 'src/map-scene.js' + TAG, 'src/candidate-city-integrations.js' + TAG,
    'src/candidate-city-clipping.js' + TAG, 'src/building-beacons.js' + TAG,
    'src/candidate-source-sections.js', 'src/country-hospital.js', 'src/dacheng-hall.css',
    'data/candidate-city-integrations.json' + TAG, 'data/model-todo/queue.json', 'data/model-viewers.json',
    'data/global-models/additional-placement.json', 'data/restoration-progress/progress.json',
    'source/precise/' + MODEL + '/README.md', 'source/precise/' + MODEL + '/reference-review.json',
    'data/audit/country-hospital-v1/geometry-native.json',
    'data/audit/country-hospital-v1/jingan-country-hospital-garden-front-preview.png',
]


def now():
    return datetime.now(timezone.utc).isoformat()


def public_bytes(url):
    attempt = {'checked_at_utc': now()}
    request = Request(url, headers={'User-Agent': 'Shanghai-model-publication-check/1.0'})
    try:
        with urlopen(request, timeout=35) as response:
            size, digest = 0, hashlib.sha256()
            while chunk := response.read(131072):
                size += len(chunk)
                digest.update(chunk)
            attempt.update(status=response.status, final_url=response.url, bytes=size, sha256=digest.hexdigest())
    except HTTPError as error:
        attempt.update(status=error.code, final_url=error.url, error=str(error))
    except (URLError, TimeoutError, OSError) as error:
        attempt['error'] = str(error)
    return attempt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('commit')
    parser.add_argument('--ref', help='HTTP ref, defaults to immutable commit')
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[5])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--retry-delay', type=float, default=15)
    args = parser.parse_args()
    if args.attempts < 1 or args.retry_delay < 0:
        parser.error('attempts must be positive and delay nonnegative')
    def git(*parts):
        return subprocess.check_output(['git', *parts], cwd=args.repo)
    commit = git('rev-parse', '--verify', args.commit + '^{commit}').decode().strip()
    ref = args.ref or commit
    prefix = PROJECT + 'assets/models/candidates/' + MODEL + '/'
    manifest_path = prefix + 'manifest.json'
    manifest = json.loads(git('show', commit + ':' + manifest_path))
    assert manifest['model_id'] == MODEL
    assert set(manifest['assets']) == {'raw', 'full', 'lod', 'native'}
    assets = {prefix + a['file']: a for a in manifest['assets'].values()}
    paths = ['README.md', *(PROJECT + path for path in FILES), manifest_path, *assets]
    records = []
    for relative in paths:
        path = relative.split('?')[0]
        expected = git('show', commit + ':' + path)
        digest = hashlib.sha256(expected).hexdigest()
        if path in assets:
            assert (assets[path]['bytes'], assets[path]['sha256']) == (len(expected), digest)
        records.append({'path': path, 'url': BASE + ref + '/' + relative,
                        'expected_bytes': len(expected), 'expected_sha256': digest, 'attempts': []})
    pending = list(records)
    for i in range(args.attempts):
        if i:
            time.sleep(args.retry_delay)
        with ThreadPoolExecutor(max_workers=6) as pool:
            for row, attempt in zip(pending, pool.map(public_bytes, (r['url'] for r in pending))):
                attempt['matches_commit'] = (attempt.get('status') == 200
                                             and attempt.get('bytes') == row['expected_bytes']
                                             and attempt.get('sha256') == row['expected_sha256'])
                row['attempts'].append(attempt)
                row['matches_commit'] = attempt['matches_commit']
        pending = [r for r in pending if not r['matches_commit']]
        if not pending:
            break
    report = {'schema': 'country-hospital-publication-v1', 'model': MODEL, 'commit': commit, 'http_ref': ref,
              'checked_at_utc': now(), 'checked_files': len(records), 'passed': not pending,
              'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'direct_view': BASE + ref + '/' + PROJECT + 'index.html#landmark=' + MODEL + '&mode=overview',
              'scope': 'Actual HTTP content and download size/SHA256 compared with exact Git blobs. '
                       'Only failed URLs are retried, with their original query string. Browser QA is separate.',
              'records': records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'ref': ref, 'checked': len(records), 'passed': not pending,
                      'failed': [r['path'] for r in pending]}, ensure_ascii=False))
    raise SystemExit(1 if pending else 0)


if __name__ == '__main__':
    main()
