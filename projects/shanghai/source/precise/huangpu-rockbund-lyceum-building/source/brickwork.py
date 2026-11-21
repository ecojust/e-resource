"""Create mottled ochre running-bond bricks and wrap their courses around the recessed street front."""
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
EDGES = json.loads((SOURCE/'frontage-registration.json').read_bytes())['visible_edges_local_m']
SOUTH_END = EDGES[0][0]
TEXTURE_REPEAT_M = 17.92


def texture_uv(x, y, z):
    # Street wall and right-angle returns share one horizontal brick course.
    # Keeping the inward coordinate gives the side walls their full brick lengths.
    return (x-SOUTH_END+y)/TEXTURE_REPEAT_M, z/TEXTURE_REPEAT_M


if __name__ == '__main__':
    from PIL import Image, ImageDraw
    from random import Random
    rng = Random(252)
    image = Image.new('RGB', (1024, 1024), (158, 144, 126))
    draw = ImageDraw.Draw(image)
    for course, y in enumerate(range(0, 1024, 4)):
        for x in range(-7*(course % 2), 1024, 14):
            tone = rng.randrange(-15, 15)
            color = (153+tone, 127+tone, 100+tone)
            draw.rectangle((x, y, x+12, y+2), fill=color)
            if rng.choice((False, True)):
                draw.point((x+rng.randrange(12), y+1), fill=(139+tone, 112+tone, 91+tone))
    image.save(SOURCE/'lyceum-ochre-brick.png', optimize=True)
