"""Check metre-space triangle contacts for the Hunan Road courtyard and its original city meshes."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile

import numpy as np

OLD_TILES = {
    'far.glb': '669911d0fde4c6be1d62b3c3a21f7d2590a2ca7c9ace7d6af6122a19590383ba',
    'near/0_1-s0-s1.glb.gz': 'ba5c9fb9a9ebb5b33ac4f14311df86879d6647046f19ec95f5e5082e7d7aa074',
    'near/1_1-s0-s0.glb.gz': '73d5bfe45dc1f5250dad67fabc6318378b4efd76e61e6eff1555532f488f1317',
}
TOL = 2e-6


def digest(data):
    return hashlib.sha256(data).hexdigest()


def primitives(path, city):
    raw = path.read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + length])
    binary = memoryview(raw)[28 + length:]

    def accessor(index):
        row = doc['accessors'][index]
        view = doc['bufferViews'][row['bufferView']]
        widths = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}
        types = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
        dtype = np.dtype(types[row['componentType']])
        width = widths[row['type']]
        start = view.get('byteOffset', 0) + row.get('byteOffset', 0)
        return np.ndarray((row['count'], width), dtype, binary, start,
                          (view.get('byteStride', width * dtype.itemsize), dtype.itemsize))

    for node in doc['nodes']:
        assert not set(node).intersection({'translation', 'rotation', 'scale', 'matrix', 'children'})
        inst = node.get('extensions', {}).get('EXT_mesh_gpu_instancing')
        for prim in doc['meshes'][node['mesh']]['primitives']:
            attr = prim['attributes']
            material = doc['materials'][prim['material']]['name']
            idx = accessor(prim['indices']).reshape(-1, 3)
            tris = accessor(attr['POSITION'])[idx].astype(np.float64)
            if inst:
                assert city and '_FEATURE_ID_0' not in attr
                data = inst['attributes']
                trans = accessor(data['TRANSLATION'])
                scale = accessor(data['SCALE'])
                x, y, z, w = accessor(data['ROTATION']).astype(np.float64).T
                f = 2 / (x*x + y*y + z*z + w*w)
                rot = np.stack([1-f*(y*y+z*z), f*(x*y-z*w), f*(x*z+y*w),
                                f*(x*y+z*w), 1-f*(x*x+z*z), f*(y*z-x*w),
                                f*(x*z-y*w), f*(y*z+x*w), 1-f*(x*x+y*y)], axis=1).reshape(-1, 3, 3)
                tris = (np.einsum('iab,itvb->itva', rot, tris[None] * scale[:, None, None, :])
                        + trans[:, None, None, :]).reshape(-1, 3, 3)
            if city and '_FEATURE_ID_0' in attr:
                ids = accessor(attr['_FEATURE_ID_0'])[idx[:, 0]].ravel()
                tris = tris[np.isin(ids, [369, 716, 1629])]
            if len(tris):
                yield material, tris


def city_local(tris, ready, survey):
    lon, lat = survey['origin_wgs']
    az = math.radians(survey['x_azimuth_deg'])
    r = 6378137 * math.cos(math.radians(ready['origin_latitude']))
    merc = math.asinh(math.tan(math.radians(ready['origin_latitude'])))
    e = (ready['origin_longitude'] + np.degrees(tris[:, :, 0] / r) - lon) * 111320 * math.cos(math.radians(lat))
    n = (np.degrees(np.arctan(np.sinh(merc - tris[:, :, 2] / r))) - lat) * 110860
    return np.stack([e*math.sin(az)+n*math.cos(az), -e*math.cos(az)+n*math.sin(az), tris[:, :, 1]], axis=-1)


def separating_axis_hits(old, new):
    a = np.roll(old, -1, axis=0) - old
    b = np.roll(new, -1, axis=1) - new
    na, nb = np.cross(a[0], a[1]), np.cross(b[:, 0], b[:, 1])
    axes = [na, nb] + [np.cross(v, b[:, j]) for v in a for j in range(3)]
    # The last six axes resolve coplanar triangles.
    axes += [np.cross(na, v) for v in a] + [np.cross(nb, b[:, j]) for j in range(3)]
    hits = np.ones(len(new), dtype=bool)
    for axis in axes:
        ax = np.broadcast_to(axis, (len(new), 3))
        eps = np.linalg.norm(ax, axis=1) * TOL
        op = old @ ax.T
        npj = np.einsum('ij,ikj->ik', ax, new)
        hits &= (op.max(0) >= npj.min(1)-eps) & (npj.max(1) >= op.min(0)-eps)
    return hits


def compare(old, new):
    count = candidates = 0
    for mat, tris in new:
        lower, upper = tris.min(1), tris.max(1)
        for _, other in old:
            mask = ((other.max(1) >= lower.min(0)-TOL) & (other.min(1) <= upper.max(0)+TOL)).all(1)
            for triangle in other[mask]:
                nearby = ((upper >= triangle.min(0)-TOL) & (lower <= triangle.max(0)+TOL)).all(1)
                if nearby.any():
                    candidates += int(nearby.sum())
                    count += int(separating_axis_hits(triangle, tris[nearby]).sum())
    return dict(pairs_tested=candidates, surface_contacts=count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('macro', 'survey', 'decoder', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--mesh', type=Path, action='append', required=True,
                        help='Uncompressed source GLB or meshopt-decoded delivered GLB, in house-local coordinates.')
    args = parser.parse_args()
    ready = json.loads((args.macro/'READY.json').read_bytes())
    survey = json.loads(args.survey.read_bytes())
    models = {}
    for path in args.mesh:
        mats = [(mat, tri[:, :, [0, 2, 1]] * [1, -1, 1]) for mat, tri in primitives(path, city=False)]
        models[path.name] = (digest(path.read_bytes()), mats)
    results = []
    with tempfile.TemporaryDirectory() as folder:
        work = Path(folder)
        for tile, required in OLD_TILES.items():
            data = (args.macro/tile).read_bytes()
            assert digest(data) == required, tile
            packed, decoded = work/'original.glb', work/'decoded.glb'
            packed.write_bytes(gzip.decompress(data) if tile.endswith('.gz') else data)
            subprocess.run(['node', Path(__file__).with_name('decode_city_mesh.mjs'), packed, decoded, args.decoder], check=True)
            old = [(mat, city_local(tris, ready, survey)) for mat, tris in primitives(decoded, city=True)]
            for name, (sha, new) in models.items():
                results.append(dict(original_tile=tile, original_sha256=required, model=name, model_sha256=sha, **compare(old, new)))
    args.output.write_text(json.dumps(dict(tolerance_m=TOL, comparisons=results), indent=2)+'\n')


if __name__ == '__main__':
    main()
