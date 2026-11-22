"""Independently decode the tower colonnade, arched entrance, star and pavilion windows."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
ID = 'jingan-sino-soviet-central-foyer'
sys.path.insert(0, str(PROJECT / 'source/precise' / ID / 'source'))
from check_surfaces import check_triangles


def triangles(file):
    data = file.read_bytes()
    n = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + n])
    binary = memoryview(data)[28 + n:]

    def values(index):
        acc = doc['accessors'][index]
        view = doc['bufferViews'][acc['bufferView']]
        kind = {5123: '<u2', 5125: '<u4', 5126: '<f4'}[acc['componentType']]
        width = {'SCALAR': 1, 'VEC3': 3}[acc['type']]
        offset = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
        size = np.dtype(kind).itemsize
        return np.ndarray((acc['count'], width), dtype=kind, buffer=binary, offset=offset,
                          strides=(view.get('byteStride', width * size), size))
    coords = []
    materials = []
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            pos = values(prim['attributes']['POSITION']).copy()
            ind = values(prim['indices']).reshape(-1, 3)
            coords.append(pos[ind][:, :, [0, 2, 1]] * [1, -1, 1])
            materials.extend(
                [doc['materials'][prim['material']]['name']] * len(ind))
    return np.concatenate(coords), np.array(materials)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--assets', type=Path, help='Optional separate directory for a preflight package')
    parser.add_argument('--out', type=Path, default=HERE / 'surface-checks.json')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_bytes())
    assert manifest['id'] == ID
    results = {}
    with TemporaryDirectory() as folder:
        for role in ('raw', 'full', 'lod'):
            item = manifest['assets'][role]
            actual = (args.assets or args.manifest.parent) / item['file']
            assert actual.stat().st_size == item['bytes']
            with actual.open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256']
            decoded = actual
            if role != 'raw':
                decoded = Path(folder) / (role + '.glb')
                subprocess.run(['node', PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',
                                actual, decoded, PROJECT / 'vendor/meshopt_decoder.module.js'], check=True)
            coords, materials = triangles(decoded)
            assert len(coords) == len(materials) == item['triangles']
            report = check_triangles(coords, materials, role == 'lod')
            assert len(report['rays']) >= 96
            results[role] = {'sha256': item['sha256'], **report}
    verified = {'id': ID, 'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                'passed': True, 'total_checks': sum(len(r['rays']) for r in results.values()), 'variants': results}
    args.out.write_text(json.dumps(verified, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
