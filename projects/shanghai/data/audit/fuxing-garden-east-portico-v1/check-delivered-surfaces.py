"""Independently decode the timber shutters, porch supports, west cheek oculus and recessed leaves."""
import argparse
import hashlib
import json
from os import environ
from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PROJECT = Path(environ.get('SHANGHAI_PROJECT', PROJECT))
TOOLS = PROJECT
ID = 'huangpu-fuxing-garden-north-house-east-portico'
sys.path.insert(0, str(PROJECT / 'source/precise' / ID / 'source'))
sys.path.insert(0, str(PROJECT / 'tools'))




def triangles(file):
    data = file.read_bytes()
    n = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + n])
    binary = memoryview(data)[28 + n:]

    def values(index):
        acc = doc['accessors'][index]
        view = doc['bufferViews'][acc['bufferView']]
        kind = {5121:'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[acc['componentType']]
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
    import os, contextlib
    with contextlib.ExitStack() as stack:
        for role in ('raw', 'full', 'lod'):
            item = manifest['assets'][role]
            actual = (args.assets or args.manifest.parent) / item['file']
            assert actual.stat().st_size == item['bytes']
            with actual.open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256']
            decoded = actual
            if role != 'raw':
                fd = os.memfd_create('fuxing-portico-' + role)
                stack.callback(os.close,fd)
                decoded = Path('/proc') / str(os.getpid()) / 'fd' / str(fd)
                subprocess.run(['node', TOOLS / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',
                                actual, decoded, TOOLS / 'vendor/meshopt_decoder.module.js'], check=True)
            coords, materials = triangles(decoded)
            assert len(coords) == len(materials) == item['triangles']
            wanted=json.loads((HERE/'source-rays.json').read_bytes())[role]['rays']
            checked=[]
            for q in wanted:
                origin=np.array(q['origin']);d=np.array(q['direction']);e1=coords[:,1]-coords[:,0];e2=coords[:,2]-coords[:,0]
                h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);good=np.abs(det)>1e-9
                inv=np.divide(1.,det,out=np.zeros_like(det),where=good);shift=origin-coords[:,0]
                u=inv*np.einsum('ij,ij->i',shift,h);cross=np.cross(shift,e1);vv=inv*(cross@d)
                dist=inv*np.einsum('ij,ij->i',e2,cross);ids=np.where(good&(u>=-1e-7)&(vv>=-1e-7)&(u+vv<=1.0000001)&(dist>.0001))[0]
                assert len(ids),q['label']
                chosen=ids[np.argmin(dist[ids])];pos=origin+dist[chosen]*d
                assert materials[chosen] in q['expected'] and np.linalg.norm(pos-np.array(q['hit'][1]))<.018,(q,materials[chosen],pos)
                checked.append(dict(label=q['label'],material=str(materials[chosen]),hit=pos.tolist(),triangle=int(chosen)))
            assert len(checked)==20
            report={'passed':True,'triangles':len(coords),'rays':checked}
            results[role] = {'sha256': item['sha256'], **report}
    verified = {'id': ID, 'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                'passed': True, 'total_checks': sum(len(r['rays']) for r in results.values()), 'variants': results}
    args.out.write_text(json.dumps(verified, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
