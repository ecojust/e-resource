"""Generate the original repeating glints on the postal supply office window glass."""
from math import cos, pi, sin
from pathlib import Path
from PIL import Image


def paint(path):
    size = 64
    tile = Image.new('RGB', (size, size))
    for y in range(size):
        for x in range(size):
            u, v = x / size, y / size
            reflection = (3.4 * cos(2 * pi * v) + 1.6 * sin(2 * pi * (2*u+v))
                          + 0.7 * cos(2 * pi * (u-3*v)))
            level = round(246 + reflection)
            tile.putpixel((x, y), (level-1, level, level+1))
    tile.save(path, optimize=True)


if __name__ == '__main__':
    paint(Path(__file__).with_name('postal-window-glass.png'))
