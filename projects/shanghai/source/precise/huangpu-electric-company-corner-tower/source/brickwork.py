"""Generate the variegated ochre facing brick and wrap its courses around the corner."""
from math import hypot
from pathlib import Path


def texture_uv(x, y, z):
    half_chamfer = 3.795115
    if x < -half_chamfer:
        u = -half_chamfer - hypot(x + half_chamfer, y)
    elif x > half_chamfer:
        u = half_chamfer + hypot(x - half_chamfer, y)
    else:
        u = x
    return (u + 14) / 17.92, z / 17.92


if __name__ == '__main__':
    from PIL import Image, ImageDraw
    from random import Random

    rng = Random(246)
    image = Image.new('RGB', (1024, 1024), (165, 156, 144))
    draw = ImageDraw.Draw(image)
    for course, y in enumerate(range(0, 1024, 4)):
        for x in range(-7 * (course % 2), 1024, 14):
            tone = rng.randrange(-14, 14)
            colour = (175 + tone, 158 + tone, 141 + tone)
            draw.rectangle((x, y, x + 12, y + 2), fill=colour)
            draw.point((x + rng.randrange(11), y + 2), fill=(164 + tone, 147 + tone, 133 + tone))
    image.save(Path(__file__).with_name('ochre-brick.png'), optimize=True)
