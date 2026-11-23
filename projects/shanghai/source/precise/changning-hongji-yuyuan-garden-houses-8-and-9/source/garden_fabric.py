"""Original materials and dimensioned masonry details of the two lawn houses."""
from pathlib import Path

import numpy as np
from PIL import Image

SRC = Path(__file__).parent
BRICK = 'Hongji 8 | red facing brick'
RENDER = 'Hongji 9 | pebbled render'
CREAM = 'Hongji houses | off-white rendered wall'
PLINTH = 'Hongji houses | grey cement plinth'
STONE = 'Hongji 9 | warm stone portico'
LEDGE = 'Hongji 9 | dressed stone edge'
JOINT = 'Hongji 9 | aged terrace border'
METAL = 'Hongji houses | dark metalwork'
GLASS = 'Hongji 9 | shaded glazed light'
WOOD = 'Hongji 9 | painted entrance timber'
BRASS = 'Hongji houses | weathered brass'
BRONZE = 'Hongji 8 | rust coloured metal lettering'
BOARD = 'Hongji houses | dark number plaque'
TREAD = 'Hongji houses | entrance stone'
GRASS = 'Hongji garden | cut lawn'
PAVING = 'Hongji garden | stone path'
EARTH = 'Hongji garden | soil'
FOLIAGE = 'Hongji garden | low hedge'
FOLIAGE_DARK = 'Hongji garden | shaded leaves'


def paint(rgb, roughness=.84, metallic=0.):
    return {'color': [(v / 255.) ** 2.2 for v in rgb],
            'roughness': roughness, 'metallic': metallic}


PALETTE = {
    BRICK: {'color': [1, 1, 1], 'roughness': .89,
            'texture': str(SRC / 'hongji-facing-brick.png')},
    RENDER: {'color': [1, 1, 1], 'roughness': .97,
             'texture': str(SRC / 'hongji-pebbled-render.png')},
    CREAM: paint((212, 206, 183)), PLINTH: paint((134, 136, 125)),
    STONE: paint((183, 169, 141)), LEDGE: paint((207, 197, 168)),
    JOINT: paint((145, 132, 111)), METAL: paint((63, 65, 60), .56, .22),
    GLASS: paint((66, 78, 80), .25, .11), WOOD: paint((212, 196, 155), .69),
    BRASS: paint((178, 145, 77), .50, .44), BRONZE: paint((140, 91, 72), .69, .20),
    BOARD: paint((92, 72, 65), .79), TREAD: paint((140, 136, 124)),
    GRASS: paint((115, 133, 77)), PAVING: paint((151, 148, 137)),
    EARTH: paint((105, 94, 68)), FOLIAGE: paint((88, 108, 61)),
    FOLIAGE_DARK: paint((65, 85, 53)),
}


def block(b, x0, x1, y0, y1, z0, z1, material, label):
    size = (x1 - x0, y1 - y0, z1 - z0)
    if min(size) <= 0:
        raise ValueError(f'Nonpositive dimensions for {label}: {size}')
    b.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), size, material, label=label)


def face(b, shape, front, back, material, label):
    for polygon in getattr(shape, 'geoms', [shape]):
        if polygon.geom_type == 'Polygon' and polygon.area > 1e-8:
            b.prism(polygon, -back, -front, lambda x, z, d: (x, -d, z), material, label)


def make_textures():
    size = 432
    iy, ix = np.indices((size, size))
    rng = np.random.default_rng(11070089)
    # Six staggered brick lengths and eighteen courses. The wider sixth
    # mortar bed is separately visible across the 2016 and 2023 facades.
    course = iy // 24
    along = (ix + 36 * (course % 2)) % size
    brick = along // 72
    blackened = rng.choice([0, 0, 0, 0, -12, -21], (18, 6))[course, brick]
    noise = rng.normal(0, 4.3, (size, size))
    reflectance = np.array([154., 83., 60.]) + blackened[:, :, None]
    reflectance += (noise + rng.normal(0., 11., (18, 6))[course, brick])[:, :, None]
    end = np.minimum(along % 72, 72 - along % 72)
    bed = np.minimum(iy % 24, 24 - iy % 24)
    mortar = np.maximum(np.clip((2.0 - end) / 1.6, 0, 1),
                        np.clip((2.1 + (course % 6 == 0) * 1.1 - bed) / 1.6, 0, 1))
    joint = np.array([200., 186., 161.]) + noise[:, :, None] * .43
    rgb = reflectance * (1 - mortar[:, :, None]) + joint * mortar[:, :, None]
    Image.fromarray(np.uint8(np.clip(rgb, 0, 255))).save(SRC / 'hongji-facing-brick.png', optimize=True)
    # The stippled aggregate is drawn separately. A single nearby cast shadow
    # per grain gives the dry pebble-dash a coarse surface under grazing light.
    fine = rng.normal(0., 6.0, (size, size))
    aggregate = rng.random((size, size)) > .81
    lumps = aggregate + .46 * np.roll(aggregate, 1, axis=1)
    pits = np.roll(lumps, 1, axis=0)
    tone = fine + 11. * lumps - 18. * pits
    rgb = np.array([184., 180., 163.]) + tone[:, :, None]
    Image.fromarray(np.uint8(np.clip(rgb, 0, 255))).save(SRC / 'hongji-pebbled-render.png', optimize=True)


if __name__ == '__main__':
    make_textures()
