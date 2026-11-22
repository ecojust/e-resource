"""Check the street-facing material under each ray in the three delivered GLB variants."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
MODEL = 'huangpu-ningpo-commercial-bank-corner'
sys.path.insert(0, str(PROJECT / 'source/precise' / MODEL / 'source'))
from check_surfaces import check_triangles


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def measure(work, manifest_path):
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest['id'] == MODEL
    roles = {'raw': 'raw', 'web': 'full', 'lod': 'lod'}
    results = {}
    for info in json.loads((work / 'delivered-decode.json').read_bytes()):
        variant = info['variant']
        file = manifest['assets'][roles[variant]]
        actual = manifest_path.parent / file['file']
        assert digest(actual) == file['sha256'] == info['sha256']
        coordinates = np.fromfile(info['triangle_file'], np.float64).reshape(-1, 3, 3)
        materials = np.array(info['material_names'])[np.fromfile(info['triangle_material_ids_file'], np.uint16)]
        assert len(materials) == len(coordinates) == file['triangles']
        local = coordinates[:, :, [0, 2, 1]] * [1, -1, 1]
        report = check_triangles(local, materials, variant == 'lod')
        results[variant] = {'asset_sha256': file['sha256'], **report}
    assert set(results) == set(roles) and all(len(x['rays']) == 155 for x in results.values())
    return {'model': MODEL, 'manifest_sha256': digest(manifest_path), 'passed': True,
            'total_checks': sum(len(v['rays']) for v in results.values()), 'variants': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--out', type=Path, default=HERE / 'surface-checks.json')
    args = parser.parse_args()
    args.out.write_text(json.dumps(measure(args.work, args.manifest), ensure_ascii=False, indent=2) + '\n')
