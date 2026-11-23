"""Compare independently read photo pixels with the first material visible in three meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
LOAD = runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']


def first_surface(triangles, indices, materials, station):
    origin = np.array(station['C'])
    transform = np.array(station['R']).T @ np.linalg.inv(station['K'])
    edge_a = triangles[:, 1] - triangles[:, 0]
    edge_b = triangles[:, 2] - triangles[:, 0]
    start = origin - triangles[:, 0]
    cross = np.cross(start, edge_a)
    numerator = np.einsum('ij,ij->i', edge_b, cross)

    def cast(x, y):
        ray = transform @ [x, y, 1]
        h = np.cross(ray, edge_b)
        determinant = np.einsum('ij,ij->i', edge_a, h)
        valid = abs(determinant) > 1e-9
        inverse = np.divide(1., determinant, out=np.zeros_like(determinant), where=valid)
        a = inverse * np.einsum('ij,ij->i', start, h)
        b = inverse * (cross @ ray)
        depth = numerator * inverse
        depth[~valid | (a < 0) | (b < 0) | (a+b > 1) | (depth <= 0)] = np.inf
        i = depth.argmin()
        return materials[indices[i]] if np.isfinite(depth[i]) else 'sky'

    return cast


def check(mesh, cameras, points):
    triangles, indices, materials, _ = LOAD(mesh)
    rays = {key:first_surface(triangles, indices, materials, v) for key,v in cameras.items()}
    disk = sorted((np.hypot(x,y), x,y) for x in range(-6,7) for y in range(-6,7) if x*x + y*y <= 36)
    records = []
    for point in points:
        x, y = point['pixel']
        ray = rays[point['view']]
        surface = ray(x, y)
        nearest = None
        for distance, dx, dy in disk:
            candidate = ray(x+dx, y+dy) if distance else surface
            if any(name in candidate for name in point['expected'].split('|')):
                nearest = [dx, dy, round(distance,2), candidate]
                break
        records.append(dict(**point,first_material=surface,nearest=nearest))
    within = [r['nearest'] for r in records if r['nearest'] is not None]
    return dict(sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),count=len(records),
                direct=int(sum(n[2] == 0 for n in within)),within6=len(within),observations=records)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ('authored','decoded-near','decoded-far','output'):
        cli.add_argument(name, type=Path)
    args = vars(cli.parse_args())
    stations = json.loads((HERE/'registered-stations.json').read_bytes())
    points = json.loads((HERE/'surface-observations.json').read_bytes())
    result = {key:check(args[key], stations, points) for key in ('authored','decoded-near','decoded-far')}
    args['output'].write_text(json.dumps(result,indent=2) + '\n')
