"""Count actual exterior faces at affected Willow Court roof, slab, passage and wall joints."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

PROJECT = Path(__file__).resolve().parents[3]
reader = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
load_triangles = runpy.run_path(str(reader))['load_triangles']
samples = [
    ('south wall beside ground plate', [3.31, -7.1, .132]),
    ('west front corner', [-7.75, -7.1, 2.15]),
    ('east front corner', [7.75, -7.1, 3.02]),
    ('east drive return near front', [7.82, -7.01, 2.08]),
    ('west recessed return', [-7.82, -7.02, 2.08]),
    ('south wall below central roof', [-4.3, -7.1, 38.28]),
    ('upper corner from south', [-7.74, -7.1, 37.22]),
    ('upper corner from east', [7.82, -7.03, 37.22]),
    ('central roof outer wall', [7.82, -2.67, 38.3]),
    ('outer east wall below terrace', [12.18, -.34, 35.16]),
    ('outer end of drive soffit', [12.18, -4.42, 4.348]),
    ('rear plinth at west wing', [-10.21, 7.13, .154]),
    ('front upper crown step', [.12, -7.35, 39.27]),
]


def measure(path):
    triangles, material_ids, names, asset = load_triangles(path)
    first = triangles[:, 1] - triangles[:, 0]
    second = triangles[:, 2] - triangles[:, 0]
    normal = np.cross(first, second)
    squared = np.einsum('ij,ij->i', normal, normal)
    length = np.sqrt(squared)
    rows = []
    for label, point in samples:
        offset = np.array(point) - triangles[:, 0]
        plane = np.einsum('ij,ij->i', offset, normal) / length
        u = np.einsum('ij,ij->i', np.cross(offset, second), normal) / squared
        v = np.einsum('ij,ij->i', np.cross(first, offset), normal) / squared
        mask = (abs(plane) < .00002) & (u > -.00001) & (v > -.00001) & (u + v < 1.00001)
        hits = [{'material': names[material_ids[i]], 'normal': (normal[i] / length[i]).round(4).tolist()}
                for i in np.flatnonzero(mask)]
        rows.append({'label': label, 'local_xyz_m': point, 'exterior_faces': hits})
    return {'asset': asset, 'measurements': rows}


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('model', type=Path, help='Uncompressed or decoded GLB, in the model local coordinates')
    cli.add_argument('report', type=Path)
    cli.add_argument('--expected-faces', type=int, default=1)
    args = cli.parse_args()
    report = measure(args.model)
    assert all(len(s['exterior_faces']) == args.expected_faces for s in report['measurements']), report
    report['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['expected_faces'] = args.expected_faces
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
