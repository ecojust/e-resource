"""Original running-bond colours and a continuous distance coordinate around the corner."""
import math
from pathlib import Path

RADIUS = 1.38
TURN = math.radians(89.02736888496747)
TANGENT = RADIUS * math.tan(TURN / 2)
CENTER = (-TANGENT, RADIUS)
SOUTH_LENGTH = 7.26
EAST_LENGTH = 6.90
EAST_TANGENT = (CENTER[0] + RADIUS * math.sin(TURN), CENTER[1] - RADIUS * math.cos(TURN))
EAST_AXIS = (math.cos(TURN), math.sin(TURN))


def texture_uv(x, y, z):
    phi = math.atan2(y - CENTER[1], x - CENTER[0]) + math.pi / 2
    if x < CENTER[0]:
        along = SOUTH_LENGTH + x - CENTER[0]
    elif phi <= TURN:
        along = SOUTH_LENGTH + RADIUS * max(0., phi)
    else:
        along = SOUTH_LENGTH + RADIUS * TURN + (x - EAST_TANGENT[0]) * EAST_AXIS[0] + (y - EAST_TANGENT[1]) * EAST_AXIS[1]
    return (along + 1) / 19, (z + .3) / 19


if __name__ == '__main__':
    from PIL import Image, ImageDraw
    from random import Random
    sources = [
        ('grey-brick.png', (130, 124, 126), (82, 80, 85)),
        ('red-brick.png', (155, 117, 113), (160, 93, 89)),
    ]
    for number, (file, mortar, brick) in enumerate(sources):
        rng = Random(253 + number)
        canvas = Image.new('RGB', (1024, 1024), mortar)
        draw = ImageDraw.Draw(canvas)
        for course, y in enumerate(range(0, 1024, 4)):
            for x in range(-6 * (course % 2), 1024, 12):
                shade = rng.randint(-10, 10)
                tint = tuple(channel + shade for channel in brick)
                draw.rectangle((x, y, x + 10, y + 2), fill=tint)
                if rng.randrange(4) == 0:
                    draw.point((x + rng.randrange(10), y + 1), fill=tuple(v - 9 for v in tint))
        canvas.save(Path(__file__).with_name(file), optimize=True)
