"""The photographed grey wall has thin, regularly spaced horizontal joints and a speckled finish."""
from pathlib import Path
import numpy as np

STONE = 'Speckled grey facade finish'
PERIOD = .83


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
    rng = np.random.default_rng(613352)
    y, x = np.mgrid[:256, :256] * 2 * np.pi / 256
    grains = rng.normal(0., 4.1, (256, 256))
    shade = 1.6 * np.sin(x + 3 * y) + 2.5 * np.cos(2 * x - y) + grains
    image = np.array([166, 158, 151]) + shade[..., None]
    Image.fromarray(np.clip(image, 0, 255).astype(np.uint8)).save(Path(__file__).with_name('street-finish.png'), optimize=True)


if __name__ == '__main__':
    create()
