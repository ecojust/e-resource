"""Compare selected public HTTP files with an exact local Git commit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

MODEL = 'huangpu-great-world'
PROJECT = 'projects/shanghai/'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('commit')
    parser.add_argument('--repo', type=Path, default=Path('/workspace/e-resource'))
    parser.add_argument('--ref', help='HTTP ref; default is the immutable commit')
    parser.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    def git(*parts):
        return subprocess.check_output(['git', *parts], cwd=args.repo)
    commit = git('rev-parse', args.commit + '^{commit}').decode().strip()
    ref = args.ref or commit
    prefix = PROJECT + 'assets/models/candidates/' + MODEL + '/'
    manifest = json.loads(git('show', commit + ':' + prefix + 'manifest.json'))
    files = ['README.md'] + [PROJECT + p for p in [
        'README.md', 'CURRENT_STATE.md', 'index.html', 'landmarks.html',
        'data/candidate-city-integrations.json', 'data/model-todo/queue.json',
        'src/app.js', 'src/map-scene.js', 'src/candidate-city-integrations.js', 'src/candidate-city-clipping.js',
        'src/great-world.js', 'great-world.html',
        'source/precise/' + MODEL + '/README.md',
    ]] + [prefix + 'manifest.json']
    if not args.metadata_only:
        files += [prefix + asset['file'] for asset in manifest['assets'].values()]
    def check(path):
        expected = git('show', commit + ':' + path)
        query = '?v=great-world-v1' if path in [PROJECT + 'data/candidate-city-integrations.json', PROJECT + 'src/app.js', PROJECT + 'src/map-scene.js', PROJECT + 'src/candidate-city-integrations.js', PROJECT + 'src/candidate-city-clipping.js'] else ''
        url = 'https://raw.githack.com/ecojust/e-resource/' + ref + '/' + path + query
        request = urllib.request.Request(url, headers={'User-Agent': 'Shanghai-model-publication-check/1.0'})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                actual, status, final_url = response.read(), response.status, response.url
            return {'path': path, 'url': url, 'final_url': final_url, 'status': status,
                    'bytes': len(actual), 'sha256': hashlib.sha256(actual).hexdigest(),
                    'expected_sha256': hashlib.sha256(expected).hexdigest(),
                    'matches_commit': status == 200 and actual == expected}
        except Exception as error:
            return {'path': path, 'url': url, 'matches_commit': False, 'error': str(error)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(check, files))
    report = {'schema': 'great-world-publication-v1', 'commit': commit, 'http_ref': ref,
              'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Actual HTTP bytes compared with this Git commit; browser rendering is verified separately.',
              'checked_files': len(records), 'passed': all(r['matches_commit'] for r in records),
              'direct_view': 'https://raw.githack.com/ecojust/e-resource/' + ref + '/' + PROJECT + 'index.html#landmark=' + MODEL + '&mode=overview',
              'records': records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'checked_files': len(records), 'passed': report['passed'], 'failed': [r['path'] for r in records if not r['matches_commit']]}))
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
