"""Original washed-pebble wall and metric UVs on the Anfu Road residence."""
from pathlib import Path
import numpy as np

STONE = 'Dark washed pebble aggregate'
PERIOD = .48


def uv(x, y, z, axis):
    return (y if axis == 0 else x) / PERIOD, (y if axis == 2 else z) / PERIOD


def texture_coordinates(builder):
    for part in builder.parts:
        if part['material'] != STONE:
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
    rng = np.random.default_rng(42840368)
    seed = rng.normal(0, 1, (256, 256))
    from scipy.ndimage import gaussian_filter
    grains = gaussian_filter(seed, .92, mode='wrap')
    grains = (grains-grains.mean())/grains.std()
    fine = rng.normal(0, 3.7, (256, 256))
    relief = 2.2*np.cos(2*x-y) + 1.8*np.sin(y+3*x) + fine
    # Warm rounded flecks are embedded in a dark, cool aggregate matrix.
    pebble = np.clip(grains+.18,0,1.85)
    colour = np.array((104,106,96))+relief[...,None]+pebble[...,None]*np.array((21,18,14))
    Image.fromarray(np.clip(colour,0,255).astype('uint8')).save(
        Path(__file__).with_name('washed-pebbles.png'),optimize=True)



if __name__ == '__main__':
    create()
