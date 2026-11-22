"""Paint a seamless neutral low-contrast glaze map. No reference pixels are copied."""
from math import cos, pi
from pathlib import Path
from PIL import Image
import sys

im = Image.new('RGB', (64,64))
for y in range(64):
    for x in range(64):
        u, v = x/64., y/64.
        value = round(249.5 + 2.4*cos(2*pi*(u-.5)) + 2*cos(2*pi*(v-.13)) + .9*cos(2*pi*(u+v)))
        im.putpixel((x,y), (value-1,value,value))
im.save(Path(sys.argv[1]), optimize=True)
