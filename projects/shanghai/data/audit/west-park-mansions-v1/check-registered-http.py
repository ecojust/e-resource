"""Verify every signed file at the registered 234-entry site, using its actual module URLs."""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('snapshot', type=Path)
parser.add_argument('layer', type=Path)
parser.add_argument('url')
parser.add_argument('output', type=Path)
args = parser.parse_args()
snapshot = json.loads(args.snapshot.read_bytes())
layer = json.loads(args.layer.read_bytes())
assert layer['passed'] and snapshot['resulting_count'] == (layer['all_other_city_destinations']+1) == 234
assert len(snapshot['files']) == layer['total_signed_files']
assert layer['order'] == 197 and snapshot['files']['data/candidate-city-integrations.json'] == layer['new_catalog_sha256']
assert hashlib.sha256(args.snapshot.read_bytes()).hexdigest() == layer['production_receipt_sha256']
urls = {row['path']: row['actual_url'] for row in layer['files']}

def check(item):
    path, expected = item
    url = urljoin(args.url, urls.get(path, quote(path)))
    request = Request(url, headers={'Accept-Encoding': 'identity'})
    digest = hashlib.sha256()
    size = 0
    with urlopen(request, timeout=120) as response:
        assert response.status == 200, (path, response.status)
        for chunk in iter(lambda: response.read(262144), b''):
            size += len(chunk)
            digest.update(chunk)
    assert digest.hexdigest() == expected, (path, expected, digest.hexdigest())
    return size

started = datetime.now(timezone.utc).isoformat()
with ThreadPoolExecutor(max_workers=2) as pool:
    sizes = list(pool.map(check, sorted(snapshot['files'].items())))
record = {'passed':True,'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),
          'base_url':args.url,'city_count':snapshot['resulting_count'],'signed_http_files':len(sizes),
          'actual_bytes':sum(sizes),'catalog_sha256':layer['new_catalog_sha256'],
          'signed_file_table_sha256':layer['production_receipt_sha256'],
          'final_cache_key_receipt_sha256':hashlib.sha256(args.layer.read_bytes()).hexdigest(),
          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(record, ensure_ascii=False))
