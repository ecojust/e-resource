"""Reproduce the courtyard clipping measurements using the signed city inputs."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.request import urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
parser.add_argument('--source', type=Path, help='Local checkout containing the signed JavaScript modules')
args = parser.parse_args()
here = Path(__file__).absolute().parent
audit = here.parent
project = audit.parents[2]
signed = json.loads((here / 'signed-inputs.json').read_bytes())


def checked(body, digest):
    assert hashlib.sha256(body).hexdigest() == digest, digest
    return body


def load_json(path):
    return json.loads(path.read_bytes())


def write_at(root, name, body):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


catalogs = []
for order in ('314', '315'):
    record = signed['orders'][order]
    body = checked(gzip.decompress((here / record['catalog']).read_bytes()), record['catalog_sha256'])
    catalogs.append(json.loads(body))
    if order == '314':
        previous_bytes = body
previous, current = catalogs
assert previous['models'] == current['models'][:-1]
assert previous['resulting_city_count'] == 349 and current['resulting_city_count'] == 350
model = current['models'][-1]
contract_path = audit / 'final-placement-contract.json'
contract = load_json(contract_path)
assert model['id'] == signed['model_id'] == contract['id']
assert model['owner'] == {'macro_id': '14-13719-6694', 'feature_local_id': 712}
for key, value in contract.items():
    assert model[key] == value, key

with tempfile.TemporaryDirectory() as folder:
    working = Path(folder)
    site = working / 'city'
    write_at(site, 'package.json', b'{"type":"module"}')
    for key, record in signed['modules'].items():
        local = (args.source or project) / key
        if local.is_file() and hashlib.sha256(local.read_bytes()).hexdigest() == record['sha256']:
            source = local.read_bytes()
        elif record.get('archive'):
            source = gzip.decompress((here / record['archive']).read_bytes())
        else:
            with urlopen(record['url'], timeout=90) as response:
                source = response.read()
        write_at(site, key, checked(source, record['sha256']))
    catalog = write_at(site, 'data/candidate-city-integrations.json', previous_bytes)
    vector = write_at(working, 'decoded-tile.json', checked(
        gzip.decompress((here / 'decoded-tile.json.gz').read_bytes()), signed['vector']['decoded_sha256']))
    footprint = here / 'footprint.json'
    env = dict(os.environ, SHANGHAI_PROJECT_ROOT=str(site), MODEL_VERIFIED_CONTRACT=str(contract_path),
               MODEL_VERIFIED_FOOTPRINT=str(footprint), REQUIRE_TRUE_314='1')
    results = {}
    for name, command in (
        ('vector', [here / 'check-vector.mjs', vector, working / 'vector.json', catalog]),
        ('clip-table', [audit / 'check-clip-table.mjs', catalog, contract_path, footprint, working / 'clip-table.json']),
    ):
        subprocess.run(['node', *command], env=env, check=True)
        new = (working / (name + '.json')).read_bytes()
        expected = (here / ('verified-314-' + name + '.json')).read_bytes()
        assert new == expected, name
        results[name] = json.loads(new)
    report = dict(model_id=model['id'], previous_city=349, current_city=350,
                  unchanged_prior_rows=len(previous['models']), owner=model['owner'], results=results)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
