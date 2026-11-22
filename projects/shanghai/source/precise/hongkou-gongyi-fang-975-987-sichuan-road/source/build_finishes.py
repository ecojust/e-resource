"""Make two repeatable, original surfaces in a 1.282 m square texture cell."""
from pathlib import Path
import numpy as np
from PIL import Image

SIZE = 384
HERE = Path(__file__).parent


def create():
    rng = np.random.default_rng(975)
    y, x = np.indices((360, 360))
    course = y // 20
    shifted = (x + 36 * (course % 2)) % 360
    brick = shifted // 72
    tone = rng.normal(0, 6, (18, 5))[course, brick]
    grain = rng.normal(0, 3., x.shape)
    clay = np.array([169, 103, 77]) + (tone + grain)[..., None] * [1., .80, .72]
    seam = np.minimum(y % 20, 19 - y % 20) < 1
    seam |= np.minimum(shifted % 72, 71 - shifted % 72) < 1
    clay[seam] = np.array([153, 137, 117]) + grain[seam, None]
    Image.fromarray(np.clip(clay, 0, 255).astype('uint8')).save(HERE / 'restored-brick.png', optimize=True)
    y, x = np.indices((SIZE, SIZE))
    tile_row = y // 64
    column = (x + 24 * (tile_row % 2)) % SIZE
    grain = rng.normal(0, 3., x.shape)
    undulation = 7 * np.cos(2 * np.pi * column / 48)
    shade = undulation + grain - 18 * np.exp(-((y % 64) / 3.4) ** 2)
    tile = np.array([142, 90, 67]) + shade[..., None] * [1., .76, .65]
    Image.fromarray(np.clip(tile, 0, 255).astype('uint8')).save(HERE / 'clay-tile.png', optimize=True)


if __name__ == '__main__':
    create()
