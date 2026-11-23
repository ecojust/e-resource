"""Trace the audience photograph across the classroom joint and the central passage."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

HERE = Path(__file__).resolve().parent
HELPER = HERE.parents[3] / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
SAMPLES = {
    'above the inner return': [(271, 148), (289, 167)],
    'below the second rear window': [(253, 360), (276, 358)],
    'upper gallery doors and booth': [(400, 197), (552, 181), (744, 169)],
    'vestibule doors viewed through the gallery opening': [(520, 320), (553, 321), (596, 311)],
}


def inspect(mesh):
    reg = json.loads((HERE / 'auditorium-station.json').read_bytes())
    projection = np.array(reg['projection'])
    origin = np.array(reg['eye'])
    scene = runpy.run_path(str(HELPER))['SerialScene'](mesh)
    checks = []
    for zone, points in SAMPLES.items():
        for u, v in points:
            direction = np.linalg.solve(projection[:, :3], [u, v, 1.0])
            direction /= np.linalg.norm(direction)
            hit = scene.ray(origin, direction, 80.)
            material = hit['material'] if hit else None
            checks.append(dict(zone=zone, uv=[u, v], first_material=material,
                               conditioned_on='auditorium-station.json'))
    return dict(photo=reg['photo'], frame=reg['frame'], mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),
                samples=checks)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh', type=Path)
    cli.add_argument('out', type=Path)
    args = cli.parse_args()
    args.out.write_text(json.dumps(inspect(args.mesh), ensure_ascii=False, indent=2) + '\n')
