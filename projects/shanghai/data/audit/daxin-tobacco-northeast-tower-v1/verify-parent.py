"""Bind the physical browser case and vector comparison to the actual signed 305 predecessor."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import subprocess
import sys

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'jingan-daxin-tobacco-northeast-tower'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument('--parent', required=True, type=Path)
    cli.add_argument('--vector', required=True, type=Path)
    cli.add_argument('--out', required=True, type=Path)
    args = cli.parse_args()
    parent = read(args.parent)
    assert parent['order'] == 305
    snapshot = Path(parent['snapshot'])
    assert digest(snapshot) == parent['sha256']
    city = Path(parent['root']) / 'projects/shanghai'
    catalog = city / 'data/candidate-city-integrations.json'
    assert digest(catalog) == parent['catalog_sha256'] == read(snapshot)['files']['data/candidate-city-integrations.json']
    rows = read(catalog)['models']
    assert rows[-1]['id'] == 'jingan-shi-liangcai-residence-carriage-porch'
    assert any(r['id'] == 'jingan-rong-residence-garden-tower' for r in rows)
    contract = AUDIT / 'final-placement-contract.json'
    review = PROJECT / 'source/precise' / ID / 'footprint-review.json'
    env = dict(os.environ, SHANGHAI_PROJECT_ROOT=str(city), MODEL_VERIFIED_CONTRACT=str(contract), REQUIRE_TRUE_305='1')
    args.out.mkdir(exist_ok=True, parents=True)
    with TemporaryDirectory(dir=args.out) as scratch:
        working = Path(scratch)
        vector = working / 'verified-305-vector.json'
        mask = working / 'verified-305-clip-table.json'
        case = working / 'map-case.json'
        subprocess.run(['node', AUDIT / 'check-vector.mjs', args.vector, vector, catalog], env=env, check=True)
        subprocess.run(['node', AUDIT / 'check-clip-table.mjs', catalog, contract, review, mask], env=env, check=True)
        subprocess.run([sys.executable, '-B', AUDIT / 'bind-map-case.py', '--parent', args.parent, '--out', case], check=True)
        case_doc = read(case)
        measured = read(mask)
        case_doc.update(addedTriangles=measured['added_triangles'], groupTriangles=measured['current_group_triangles'])
        case.write_text(json.dumps(case_doc, indent=2, ensure_ascii=False)+'\n')
        result = {'id': ID, 'order': 306, 'parent_order': 305, 'passed': True,
                  'parent_receipt_sha256': digest(args.parent), 'parent_catalog_sha256': digest(catalog),
                  'parent_snapshot_sha256': digest(snapshot), 'contract_sha256': digest(contract),
                  'files': {f.name: digest(f) for f in [vector, mask, case]}}
        receipt = working / 'verified-305-placement.json'
        receipt.write_text(json.dumps(result, indent=2)+'\n')
        for file in [vector, mask, case, receipt]:
            output = args.out / file.name
            if output.exists():
                assert digest(output) == digest(file), output
            else:
                file.replace(output)


if __name__ == '__main__':
    main()
