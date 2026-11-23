"""Count foreground, colour variety and extents without a second full-frame RGB array."""
from PIL import Image
import json
import sys

with Image.open(sys.argv[1]) as image:
    image = image.convert('RGB')
    base = image.getpixel((1, 1))
    width, height = image.size
    left, top, right, bottom = width, height, -1, -1
    total = 0
    colours = set()
    for y in range(height - 14):
        for x, colour in enumerate(image.crop((0, y, width, y + 1)).getdata()):
            if max(abs(base[i] - colour[i]) for i in range(3)) <= 20:
                continue
            left, top = min(left, x), min(top, y)
            right, bottom = max(right, x), max(bottom, y)
            colours.add(colour)
            total += 1
    print(json.dumps({'foreground': total, 'colors': len(colours),
                      'width': max(0, right - left + 1), 'height': max(0, bottom - top + 1)}))
