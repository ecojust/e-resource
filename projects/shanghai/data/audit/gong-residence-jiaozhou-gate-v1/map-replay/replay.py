"""Replay the Gong garden gate against the frozen city before its model was added."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
PROJECT = AUDIT.parents[2]
BUILDING = 'jingan-gong-residence-jiaozhou-gate'
CATALOG = 'data/candidate-city-integrations.json'
read = lambda file: json.loads(file.read_bytes())

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    proof = read(HERE/'verified-317-placement.json')
    pins = proof['http_sha256']
    contract = AUDIT/'final-placement-contract.json'
    site = PROJECT/'source/precise'/BUILDING/'footprint-review.json'
    assert sha(contract.read_bytes()) == proof['contract_sha256']
    assert read(contract)['id'] == BUILDING and read(site)['frozen_macro'] == '14-13718-6694'
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        (root/'package.json').write_text('{"type":"module"}\n')
        for name, expected in pins.items():
            local = PROJECT/name
            archived = HERE/(expected+'.gz')
            if local.is_file() and sha(local.read_bytes()) == expected:
                body = local.read_bytes()
            elif archived.is_file():
                body = gzip.decompress(archived.read_bytes())
            else:
                commit, rel = proof['immutable_vendor_sources'][name].split(':', 1)
                with urlopen(f'https://raw.githubusercontent.com/ecojust/e-resource/{commit}/{rel}', timeout=60) as res:
                    body = res.read()
            assert sha(body) == expected, name
            output = root/name
            output.parent.mkdir(exist_ok=True, parents=True)
            output.write_bytes(body)
        vector = root/'vector.json'
        subprocess.run([sys.executable, AUDIT/'prepare-vector.py', '--tile', HERE/'14-13718-6694.pbf', '--out', vector], check=True)
        checks = {
            'verified-317-vector.json': [AUDIT/'check-vector.mjs', vector, root/'result.json', root/CATALOG],
            'verified-317-clip-table.json': [AUDIT/'check-clip-table.mjs', root/CATALOG, contract, site, root/'result.json'],
        }
        env = {**os.environ, 'SHANGHAI_PROJECT_ROOT': str(root), 'MODEL_VERIFIED_CONTRACT': str(contract)}
        for name, args in checks.items():
            subprocess.run(['node', *args], env=env, check=True)
            assert (root/'result.json').read_bytes() == (HERE/name).read_bytes()
            assert sha((root/'result.json').read_bytes()) == proof['files'][name]
        print('Verified both vector and city-mesh reports for Jiaozhou Road 522.')

if __name__ == '__main__':
    main()
