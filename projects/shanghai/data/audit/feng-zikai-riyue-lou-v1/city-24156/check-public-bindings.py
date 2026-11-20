"""Verify both city deployments, the actual paged shader modules, and the underlying city meshes."""
import argparse
import hashlib
import subprocess
import json
from pathlib import Path
from urllib.request import urlopen

def check(options):
    out = {}
    model = 'huangpu-feng-zikai-riyue-lou'
    for number in (155, 156):
        base = f'http://127.0.0.1:{24000 + number}/'
        site = options.materialized / f'stage{number}/projects/shanghai'
        path = options.receipts / f'{number}-production.json'
        snapshot = json.loads(path.read_bytes())
        comparison = json.loads((options.receipts / f'{number}-comparison.json').read_bytes())
        all_http = json.loads((options.receipts / f'{number}-all-http.json').read_bytes())
        assert all_http['passed'] and comparison['passed']
        assert all_http['production_receipt_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
        lookup = {r['path']: r['actual_url'] for r in comparison['files']}
        def payload(file):
            url = base + lookup.get(file, file)
            with urlopen(url, timeout=80) as response:
                assert response.status == 200
                return url, response.read()
        files = []
        def verify(file, digest=None, size=None, oid=None):
            url, content = payload(file)
            signature = hashlib.sha256(content).hexdigest()
            assert signature == (digest or snapshot['files'][file]), file
            if size is not None:
                assert len(content) == size, file
            if oid is not None:
                header = b'blob ' + str(len(content)).encode() + bytes([0])
                assert hashlib.sha1(header + content).hexdigest() == oid, file
            files.append({'file': file, 'url': url, 'bytes': len(content), 'sha256': signature, 'git_blob': oid})
            return content
        catalog = json.loads(verify('data/candidate-city-integrations.json'))
        for file in ['index.html', 'landmarks.html', 'src/app.js', 'src/map-scene.js', 'src/candidate-city-clipping.js',
                     'src/candidate-city-integrations.js', 'src/building-beacons.js', 'src/candidate-source-sections.js',
                     'tools/check-sourced-candidate-runtime.mjs']:
            verify(file)
        review_path = 'source/precise/' + model + '/footprint-review.json'
        review = json.loads((options.materialized / 'stage156/projects/shanghai' / review_path).read_bytes())
        for row in review['frozen_bindings']:
            file = row['repository_path'].removeprefix('projects/shanghai/')
            oid = subprocess.check_output(['git', '-C', str(Path(__file__).resolve().parents[6]), '--no-lazy-fetch', 'ls-tree', '--format=%(objectname)', review['baseline_commit'], '--', row['repository_path']], text=True).strip()
            assert len(oid) == 40
            verify(file, row['sha256'], row['bytes'], oid)
        registered = [row for row in catalog['models'] if row['id'] == model]
        assert len(registered) == int(number == 156)
        if registered:
            geometry = json.loads((Path(__file__).resolve().parent.parent / "placement-geometry.json").read_bytes())
            verify(review_path, geometry["source_sha256"])
            row = registered[0]
            manifest = json.loads(verify(row['candidate_manifest']))
            for item in manifest['assets'].values():
                file = (Path(row['candidate_manifest']).parent / item['file']).as_posix()
                verify(file, item['sha256'], item['bytes'])
            for file in ['feng-zikai-riyue-lou.html', 'data/audit/feng-zikai-riyue-lou-v1/final-placement-contract.json']:
                verify(file)
        out[str(number)] = {'base': base, 'entries': catalog['resulting_city_count'], 'signed_inputs': all_http['file_count'],
                            'signed_http_bytes': all_http['bytes'], 'production_sha256': all_http['production_receipt_sha256'],
                            'catalog_sha256': all_http['catalog_sha256'], 'signed_all_http_sha256': hashlib.sha256((options.receipts / f'{number}-all-http.json').read_bytes()).hexdigest(),
                            'actual_files': files}
    options.output.write_text(json.dumps({'passed': True, 'sites': out}, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('materialized', type=Path)
    parser.add_argument('receipts', type=Path)
    parser.add_argument('output', type=Path)
    check(parser.parse_args())
