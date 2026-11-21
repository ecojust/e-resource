"""Generate an original running-bond atlas for the brown ceramic street wall."""
from pathlib import Path
from random import Random

SIZE = 1024
SPAN = 20.48


def uv(x, y, z):
    return ((x + SPAN / 2) / SPAN, 1 - (z + .05) / SPAN)


def blender_uv(x, y, z):
    u, v = uv(x, y, z)
    return u, 1-v


def write_atlas(path):
    from PIL import Image, ImageDraw
    random = Random(473)
    image = Image.new('RGB', (SIZE, SIZE), (164, 154, 139))
    draw = ImageDraw.Draw(image)
    colors = [(79, 65, 57), (85, 67, 55), (89, 68, 55), (98, 77, 62), (103, 81, 68),
              (90, 78, 68), (110, 89, 76), (118, 96, 82)]
    for row in range(256):
        bottom = SIZE - row * 4 - 1
        for left in range(-6 * (row % 2), SIZE, 12):
            color = random.choice(colors)
            draw.rectangle((left, bottom-2, left+10, bottom), fill=color)
            if random.random() < .4:
                draw.point((left + random.randrange(11), bottom-random.randrange(3)),
                           fill=tuple(c+12 for c in color))
    image.save(path, optimize=True)


if __name__ == '__main__':
    write_atlas(Path(__file__).with_name('brown-firebrick.png'))
