"""Measure serialized UV derivatives and intercepts on the folded masonry, plus both PNG bindings."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'source'))
from brick_finishes import RED, YELLOW, SOLDIER, REPEAT_METRES
from four_window_bays import BAYS

previous = HERE.parents[1] / 'xuhui-yanqing-121-brick-front/measurements/check_brick_uv.py'
loader = importlib.util.spec_from_file_location('serial_brick_reader', previous)
reader = importlib.util.module_from_spec(loader)
loader.loader.exec_module(reader)


def sample_at(xyz, normals, uv, point, normal):
    selected = np.where(normals @ normal > .99998)[0]
    p = xyz[selected]
    a, b, q = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0], point - p[:, 0]
    axb = np.cross(a, b)
    det = np.einsum('ij,ij->i', axb, axb)
    close = np.abs(np.einsum('ij,ij->i', normals[selected], q)) < .00002
    s = np.einsum('ij,ij->i', np.cross(q, b), axb) / det
    t = np.einsum('ij,ij->i', np.cross(a, q), axb) / det
    good = close & (s > -.00005) & (t > -.00005) & (s+t < 1.00005)
    indices = np.flatnonzero(good)
    if not len(indices):
        raise ValueError(f'No masonry facet at {point.tolist()} facing {normal.tolist()}')
    i = indices[0]
    return np.array([1 - s[i] - t[i], s[i], t[i]]) @ uv[selected[i]]


def binding(doc, blob, info, expected):
    tex = doc['textures'][info['index']]
    image = doc['images'][tex['source']]
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    digest = hashlib.sha256(blob[start:start + view['byteLength']]).hexdigest()
    sampler = doc.get('samplers', [{}])[tex.get('sampler', 0)]
    wraps = [sampler.get(k, 10497) for k in ('wrapS', 'wrapT')]
    return dict(sha256=digest, equals_authored=digest == expected, repeat=wraps == [10497, 10497],
                texcoord=int(info.get('texCoord', 0)), normal_strength=float(info.get('scale', 1.)))


def audit(path, control, scale):
    doc, blob, digest = reader.glb(path)
    controls = json.loads(control.read_text())['original_pngs']
    parts, result = {}, {}
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            m = doc['materials'][p['material']]
            name = m['name']
            if name not in REPEAT_METRES:
                continue
            c = controls[name]
            base = binding(doc, blob, m['pbrMetallicRoughness']['baseColorTexture'], c['base_sha256'])
            relief = binding(doc, blob, m['normalTexture'], c['normal_sha256'])
            ids = reader.read_accessor(doc, blob, p['indices']).reshape(-1, 3)
            attrs = p['attributes']
            positions = reader.read_accessor(doc, blob, attrs['POSITION']).astype(float)
            xyz = (positions[:, [0, 2, 1]] * [1, -1, 1] / scale)[ids]
            uv = reader.read_accessor(doc, blob, attrs[f'TEXCOORD_{base["texcoord"]}']).astype(float)[ids]
            edges = xyz[:, 1:] - xyz[:, :1]
            n = np.cross(edges[:, 0], edges[:, 1])
            n /= np.linalg.norm(n, axis=1)[:, None]
            tangents = np.column_stack([-n[:, 1], n[:, 0], np.zeros(len(n))])
            vertical = np.abs(n[:, 2]) <= .9
            tangents[vertical] /= np.linalg.norm(tangents[vertical], axis=1)[:, None]
            up = np.cross(n, tangents)
            tangents[~vertical], up[~vertical] = [1, 0, 0], [0, 1, 0]
            expected = np.stack([np.einsum('tvi,ti->tv', edges, axis) for axis in (tangents, up)], axis=-1)
            delta = (uv[:, 1:] - uv[:, :1]) * c['repeat_U_Z']
            uv_det = np.linalg.det(delta)
            maxerr = np.abs(expected - delta).max(axis=(1, 2))
            result[name] = dict(base=base, normal=relief, triangles=len(ids), repeat_U_Z=c['repeat_U_Z'],
                                max_edge_error_study_m=float(maxerr.max()), p99_edge_error_study_m=float(np.percentile(maxerr, 99)),
                                collapsed_uv_triangles=int(np.count_nonzero(np.abs(uv_det) < 1e-12)))
            parts[name] = xyz, n, uv
    corner_samples = []
    for i, (left, fl, fr, right, depth) in enumerate(BAYS, 1):
        for side, x, tangent in [('left', fl, (fl-left, -depth-.015)), ('right', fr, (right-fr, depth+.015))]:
            tangent = np.array(tangent)
            tangent /= np.linalg.norm(tangent)
            normal = np.r_[tangent[1], -tangent[0], 0.]
            for name, z in ((SOLDIER, 6.30), (SOLDIER, 7.23), (SOLDIER, 9.75), (RED, 12.89)):
                point = np.array([x, -depth, z])
                main_uv = sample_at(*parts[name], point, np.array([0., -1., 0.]))
                side_uv = sample_at(*parts[name], point, normal)
                delta = main_uv - side_uv
                mismatch = np.abs(delta - np.rint(delta))
                corner_samples.append(dict(bay=i, corner=side, z=z, material=name,
                                           phase_error_U_V_cycles=mismatch.round(8).tolist()))
    maxphase = np.max([r['phase_error_U_V_cycles'] for r in corner_samples], axis=0)
    good = all(r['base']['equals_authored'] and r['normal']['equals_authored'] and r['base']['repeat']
               and r['normal']['repeat'] and r['base']['texcoord'] == r['normal']['texcoord']
               and r['normal']['normal_strength'] == 1. and not r['collapsed_uv_triangles']
               and r['max_edge_error_study_m'] < .00012 for r in result.values())
    return dict(file=path.name, sha256=digest, authored_coordinate_scale=np.asarray(scale).tolist(),
                materials=result, corner_samples=corner_samples, max_corner_phase_error_U_V_cycles=maxphase.tolist(),
                passed=bool(good and set(result)==set(REPEAT_METRES) and max(maxphase) < .0001))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--control', type=Path, default=HERE / 'brick-finish-photo-control.json')
    parser.add_argument('--scale', type=float, nargs=3, default=[.9465478513722255, .9465478513722255, 1.009918699186992])
    args = parser.parse_args()
    report = audit(args.mesh, args.control, np.array(args.scale))
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(report['passed'], report['sha256'], report['max_corner_phase_error_U_V_cycles'])
