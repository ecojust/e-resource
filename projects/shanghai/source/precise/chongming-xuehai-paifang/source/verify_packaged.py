"""Check final distributed bytes and decoded meshopt geometry. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

import numpy as np
import trimesh

ID = 'chongming-xuehai-paifang'


def gltf(path):
    data = path.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20 + length])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', required=True, type=Path)
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--gltfpack', required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.assets / 'manifest.json').read_text())
    geometry = json.loads((args.audit / 'geometry.json').read_text())
    native = json.loads((args.audit / 'native.json').read_text())
    browser = json.loads((args.audit / 'browser.json').read_text())
    assert manifest['id'] == ID
    assert browser['full']['modelId'] == browser['lod']['modelId'] == ID
    assert not browser['errors']
    report = {'id': ID, 'assets': {}, 'native_raw_and_geometry_hashes_match': True,
              'browser_counts_and_identity_match': True, 'all_asset_files_under_100MB': True}
    with tempfile.TemporaryDirectory(prefix='west-paifang-decode-') as temp:
        for kind, entry in manifest['assets'].items():
            path = args.assets / entry['file']
            data = path.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            assert sha == entry['sha256'] and len(data) == entry['bytes']
            assert len(data) < 100_000_000
            result = {'sha256': sha, 'bytes': len(data), 'manifest_matches': True}
            if kind == 'native':
                assert sha == native['sha256']
                assert native['source_raw_sha256'] == geometry['raw']['sha256'] == manifest['assets']['raw']['sha256']
                report['assets'][kind] = result
                continue
            doc = gltf(path)
            assert doc['extras']['name'] == '崇明学宫西牌坊（题名面待核）'
            assert 'blank' in doc['extras']['inscriptions']
            assert not doc.get('images')
            decoded = path
            if kind != 'raw':
                decoded = Path(temp) / (kind + '.glb')
                subprocess.run([str(args.gltfpack.resolve()), '-i', str(path), '-o',
                                str(decoded), '-noq', '-vnf', '-km', '-ke'], check=True)
            scene = trimesh.load(decoded, force='scene', process=False)
            meshes = list(scene.geometry.values())
            triangles = sum(len(m.faces) for m in meshes)
            assert triangles == entry['triangles']
            assert all(np.isfinite(m.vertices).all() and np.min(m.area_faces) > 1e-12
                       and m.is_winding_consistent for m in meshes)
            assert np.allclose(scene.bounds, geometry['raw']['bounds_glb'], atol=1e-5)
            if kind in ('full', 'lod'):
                assert browser[kind]['triangles'] == triangles
            result.update({'triangles_after_decode': triangles, 'finite_vertices': True,
                           'zero_degenerate_faces': True, 'consistent_winding': True,
                           'model_bounds_match_source': True, 'west_identity_and_blank_plaque_extras': True,
                           'embedded_images': 0})
            report['assets'][kind] = result
    (args.audit / 'packaged.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
