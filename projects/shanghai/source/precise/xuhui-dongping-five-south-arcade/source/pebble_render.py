"""Original grey pebble plaster and metric UVs for the courtyard arcade."""
from pathlib import Path
import numpy as np

RENDER = 'Grey pebble render'
PERIOD = .68


def uv(x, y, z, axis):
    return (y if axis == 0 else x) / PERIOD, (y if axis == 2 else z) / PERIOD


def assign_uvs(builder):
    for part in builder.parts:
        if part['material'] != RENDER:
            continue
        points, texcoords, triangles, lookup = [], [], [], {}
        for triangle in part['triangles']:
            a, b, c = (np.asarray(part['vertices'][i]) for i in triangle)
            axis = int(np.argmax(np.abs(np.cross(b-a, c-a))))
            face = []
            for i in triangle:
                key = (i, axis)
                if key not in lookup:
                    lookup[key] = len(points)
                    point = part['vertices'][i]
                    u, v = uv(*point, axis)
                    points.append(point)
                    texcoords.append((u, 1-v))
                face.append(lookup[key])
            triangles.append(tuple(face))
        part.update(vertices=points, texcoords=texcoords, triangles=triangles)


def create():
    from PIL import Image
    y, x = np.mgrid[:256, :256] * (2*np.pi/256)
    grain = np.random.default_rng(41505364).normal(0, 4.9, (256, 256))
    relief = 1.7*np.cos(3*x-y) + 1.5*np.sin(2*y+x) + .8*np.cos(7*x+7*y) + grain
    colour = np.array((173, 168, 150)) + relief[..., None]
    Image.fromarray(np.clip(colour, 0, 255).astype('uint8')).save(
        Path(__file__).with_name('pebble-render.png'), optimize=True)


if __name__ == '__main__':
    create()
