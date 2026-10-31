"""Compare published immutable HTTP bytes with the exact model commit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[5]
PROJECT = 'projects/shanghai/'
MODEL = 'huangpu-daxin-company'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('commit')
    parser.add_argument('--out', type=Path, default=Path(__file__).with_name('publication.json'))
    args = parser.parse_args()
    commit = subprocess.check_output(['git', 'rev-parse', args.commit + '^{commit}'], cwd=ROOT, text=True).strip()
    prefix = PROJECT + 'assets/models/candidates/' + MODEL + '/'
    manifest = json.loads(subprocess.check_output(['git', 'show', commit + ':' + prefix + 'manifest.json'], cwd=ROOT))
    paths = ['README.md'] + [PROJECT + path for path in [
        'README.md', 'index.html', 'landmarks.html', 'data/candidate-city-integrations.json',
        'src/building-beacons.js', 'src/daxin-company.js', 'daxin-company.html',
        'source/precise/' + MODEL + '/README.md',
    ]] + [prefix + 'manifest.json'] + [prefix + asset['file'] for asset in manifest['assets'].values()]
    def check(path):
        expected = subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)
        url = 'https://raw.githack.com/ecojust/e-resource/' + commit + '/' + path
        last_error = None
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'Shanghai-model-publication-check/1.0'})
                with urllib.request.urlopen(request, timeout=90) as response:
                    actual, status, final_url = response.read(), response.status, response.url
                assert status == 200 and actual == expected, 'Published content differs from commit: ' + path
                return {'path': path, 'url': url, 'final_url': final_url, 'status': status,
                        'bytes': len(actual), 'sha256': hashlib.sha256(actual).hexdigest(), 'matches_commit': True}
            except Exception as error:
                last_error = error
                if attempt < 2:
                    time.sleep(2)
        raise last_error
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(check, paths))
    report = {'schema': 'daxin-publication-v1', 'commit': commit,
              'scope': 'Actual public HTTP bytes compared with immutable commit; this does not replace the local browser rendering check.',
              'direct_view': 'https://raw.githack.com/ecojust/e-resource/' + commit + '/' + PROJECT + 'index.html#landmark=' + MODEL + '&mode=overview',
              'checked_files': len(records), 'passed': True, 'records': records}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'commit': commit, 'checked_files': len(records), 'passed': True}))


if __name__ == '__main__':
    main()
