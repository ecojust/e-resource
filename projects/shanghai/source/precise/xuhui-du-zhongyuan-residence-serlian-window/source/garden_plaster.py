"""Metric UV mapping and an original painted lime plaster finish for the garden elevation."""
from pathlib import Path
import numpy as np

STONE = 'Painted garden wall plaster'
PERIOD = .62


def uv(x, y, z, axis):
    return (y if axis == 0 else x) / PERIOD, (y if axis == 2 else z) / PERIOD


def assign_uvs(builder):
    for part in builder.parts:
        if part['material'] != STONE:
            continue
        verts, faces, coords = [], [], []
        corners = {}
        for triangle in part['triangles']:
            a, b, c = (np.array(part['vertices'][i]) for i in triangle)
            axis = int(np.argmax(np.abs(np.cross(b - a, c - a))))
            ring = []
            for i in triangle:
                key = i, axis
                if key not in corners:
                    xyz = part['vertices'][i]
                    u, v = uv(*xyz, axis)
                    corners[key] = len(verts)
                    verts.append(xyz)
                    coords.append((u, 1 - v))
                ring.append(corners[key])
            faces.append(tuple(ring))
        part.update(vertices=verts, triangles=faces, texcoords=coords)


def create():
    from PIL import Image
    rng = np.random.default_rng(1897356)
    y, x = np.mgrid[:256, :256] * 2 * np.pi / 256
    grains = rng.normal(0., 2.7, (256, 256))
    shade = 2.0 * np.sin(2*x + y) + 2.1 * np.cos(x - 3*y) + .8*np.cos(8*x+5*y) + grains
    image = np.array([206, 204, 177]) + shade[..., None]
    Image.fromarray(np.clip(image, 0, 255).astype(np.uint8)).save(Path(__file__).with_name('garden-plaster.png'), optimize=True)


if __name__ == '__main__':
    create()
