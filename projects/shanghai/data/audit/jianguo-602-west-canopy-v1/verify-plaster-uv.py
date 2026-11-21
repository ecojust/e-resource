"""Decode and measure the directional mineral finish on the west entrance wall and its returns."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy

import numpy as np

AUDIT = Path(__file__).resolve().parent.parent
MODEL = AUDIT.parents[1] / 'source/precise/xuhui-jianguo-602-west-canopy/source'
read_mesh = runpy.run_path(AUDIT / 'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
read_textures = runpy.run_path(AUDIT / 'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']


def inspect(mesh):
    triangles, material_ids, names, _ = read_mesh(mesh)
    textures, embedded, coordinates, _ = read_textures(mesh, material_ids)
    plaster = names.index('Pale ochre cement render')
    assert embedded[plaster]['embedded_sha256'] == hashlib.sha256((MODEL / 'ochre-dragged-render.png').read_bytes()).hexdigest()
    sampler = textures[plaster][1]
    assert sampler.get('wrapS', 10497) == sampler.get('wrapT', 10497) == 10497
    selected = material_ids == plaster
    faces = triangles[selected]
    normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    components = np.abs(normals)
    axes = (components >= components.max(axis=1, keepdims=True) * (1 - 1e-5)).argmax(axis=1)
    assert len(faces) >= 40 and set(axes) == {0, 1, 2}
    x, y, z = faces.transpose(2, 0, 1)
    u = np.where(axes[:, None] == 0, y, x) / .36
    v = np.where(axes[:, None] == 2, y, z) / .36
    expected = np.stack((u, 1 - v), axis=-1)
    error = float(np.abs(coordinates[selected] - expected).max())
    assert error < .0001, error
    return dict(triangles=len(faces), period_m=[.36, .36], max_uv_error=error,
                embedded_texture_sha256=embedded[plaster]['embedded_sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for role in ('raw', 'full', 'lod', 'output'):
        parser.add_argument(role, type=Path)
    args = parser.parse_args()
    reports = {role: inspect(getattr(args, role)) for role in ('raw', 'full', 'lod')}
    args.output.write_text(json.dumps(reports, indent=2) + '\n')
