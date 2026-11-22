"""Check the signed raw predecessor and run the production city's actual vector and mesh clippers."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.request import urlopen

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
MODEL = 'jingan-eye-hospital-building-three-front'
CATALOG = 'data/candidate-city-integrations.json'
INPUTS = [CATALOG, 'src/map-scene.js', 'src/candidate-city-clipping.js', 'src/candidate-vector-clipping.js',
          'src/candidate-vector-geometry.js', 'src/candidate-overview-camera.js', 'vendor/polygon-clipping.umd.min.js',
          'vendor/maplibre-gl.js', 'vendor/three.module.js', 'vendor/three.core.js']


def read(file):
    return json.loads(file.read_bytes())


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def write(file, obj):
    file.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'production', 'comparison', 'vector', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--required-order', default=314, type=int)
    args = parser.parse_args()
    parent, production, comparison = map(read, (args.parent, args.production, args.comparison))
    order = args.required_order
    assert parent['order'] == comparison['order'] == order and comparison['passed']
    assert comparison['port'] == 31000 + order
    assert sha(args.production) == comparison['production_receipt_sha256']
    snapshot = Path(parent['snapshot'])
    assert sha(snapshot) == parent['sha256']
    raw_catalog = Path(parent['root']) / 'projects/shanghai' / CATALOG
    assert sha(raw_catalog) == parent['catalog_sha256'] == read(snapshot)['files'][CATALOG]
    raw_rows = read(raw_catalog)['models']
    if order == 314:
        assert raw_rows[-1]['id'] == 'jingan-gordon-road-station-south-front'
    assert MODEL not in {r['id'] for r in raw_rows}
    contract = AUDIT / 'final-placement-contract.json'
    footprint = PROJECT / 'source/precise' / MODEL / 'footprint-review.json'
    files = production['files']
    assert files[CATALOG] == comparison['catalog_sha256']
    paths = {r['path']: r['actual_url'] for r in comparison['files']}
    actual_hashes, vendor_git = {}, {}
    args.out.mkdir(parents=True, exist_ok=True)
    with contextlib.ExitStack() as stack:
        temp = Path(stack.enter_context(tempfile.TemporaryDirectory(dir=args.out)))
        runtime = temp / 'city'
        for key in INPUTS:
            endpoint = 'http://127.0.0.1:' + str(comparison['port']) + '/' + paths.get(key, key)
            with urlopen(endpoint, timeout=45) as response:
                content = response.read()
            actual_hashes[key] = hashlib.sha256(content).hexdigest()
            if key in files:
                assert actual_hashes[key] == files[key], key
            else:
                assert key.startswith('vendor/'), key
                ref = read(footprint)['baseline_commit'] + ':projects/shanghai/' + key
                git_bytes = subprocess.check_output(['git', '-C', str(PROJECT.parents[1]), 'show', ref])
                assert git_bytes == content, key
                vendor_git[key] = ref
            local = runtime / key
            local.parent.mkdir(exist_ok=True, parents=True)
            fd = stack.enter_context(os.fdopen(os.memfd_create('eye-hospital-runtime'), 'w+b'))
            fd.write(content)
            fd.flush()
            local.symlink_to('/proc/' + str(os.getpid()) + '/fd/' + str(fd.fileno()))
        catalog = runtime / CATALOG
        rows = read(catalog)['models']
        assert [r['id'] for r in raw_rows] == [r['id'] for r in rows]
        assert files['src/candidate-overview-camera.js'] == read(AUDIT/'overview-sightlines.json')['camera_module_sha256']
        env = dict(os.environ, SHANGHAI_PROJECT_ROOT=str(runtime), MODEL_VERIFIED_CONTRACT=str(contract),
                   REQUIRE_TRUE_314='1' if order == 314 else '0', NODE_OPTIONS='--preserve-symlinks')
        prefix = 'verified-' + str(order) if order == 314 else 'early'
        vec, mask = (temp/(prefix+'-'+name+'.json') for name in ('vector','clip-table'))
        case = temp/('map-case.json' if order == 314 else 'early-map-case.json')
        subprocess.run(['node', AUDIT/'check-vector.mjs', args.vector, vec, catalog], env=env, check=True)
        subprocess.run(['node', AUDIT/'check-clip-table.mjs', catalog, contract, footprint, mask], env=env, check=True)
        subprocess.run([sys.executable, '-B', AUDIT/'bind-map-case.py', '--parent', args.parent, '--catalog', catalog,
                        '--catalog-sha256', files[CATALOG], '--required-order', str(order), '--out', case], check=True)
        row = read(case)
        measured = read(mask)
        row.update(addedTriangles=measured['added_triangles'], groupTriangles=measured['current_group_triangles'])
        write(case, row)
        receipt = temp/(prefix+'-placement.json')
        write(receipt, dict(id=MODEL, order=315, parent_order=order, passed=True, physical_url_port=comparison['port'],
                            raw_receipt_sha256=sha(args.parent), raw_catalog_sha256=sha(raw_catalog),
                            raw_snapshot_sha256=sha(snapshot), production_sha256=sha(args.production),
                            comparison_sha256=sha(args.comparison), http_sha256=actual_hashes, immutable_vendor_sources=vendor_git,
                            contract_sha256=sha(contract), files={f.name:sha(f) for f in (vec, mask, case)}))
        for file in (vec, mask, case, receipt):
            dst = args.out/file.name
            if order == 314 and dst.exists():
                assert sha(dst)==sha(file)
            else:
                file.replace(dst)


if __name__ == '__main__':
    main()
