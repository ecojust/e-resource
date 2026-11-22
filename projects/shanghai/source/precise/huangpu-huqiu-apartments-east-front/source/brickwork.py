"""Create red running-bond bricks and wrap their courses around the recessed street front."""
import json
import math
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
EDGES = json.loads((SOURCE/'frontage-registration.json').read_bytes())['visible_edges_local_m']
SEGMENTS = []
length = 0
for a, b in zip(EDGES, EDGES[1:]):
    dx, dy = b[0]-a[0], b[1]-a[1]
    span = math.hypot(dx, dy)
    SEGMENTS.append((a, dx/span, dy/span, span, length))
    length += span


def texture_uv(x, y, z):
    nearest = None
    for a, tx, ty, span, start in SEGMENTS:
        along = min(span, max(0, (x-a[0])*tx+(y-a[1])*ty))
        distance = (x-a[0]-along*tx)**2+(y-a[1]-along*ty)**2
        if nearest is None or distance < nearest[0]:
            nearest = (distance, start+along)
    return nearest[1]/17.92, z/17.92


if __name__ == '__main__':
    from PIL import Image, ImageDraw
    from random import Random
    rng = Random(251)
    image = Image.new('RGB', (1024, 1024), (128, 107, 106))
    draw = ImageDraw.Draw(image)
    for course, y in enumerate(range(0, 1024, 4)):
        for x in range(-7*(course % 2), 1024, 14):
            tone = rng.randrange(-15, 15)
            color = (154+tone, 76+tone, 77+tone)
            draw.rectangle((x,y,x+12,y+2), fill=color)
            if rng.choice((False,True)):
                draw.point((x+rng.randrange(12),y+1), fill=(143+tone,74+tone,72+tone))
    image.save(SOURCE/'huqiu-red-brick.png', optimize=True)
