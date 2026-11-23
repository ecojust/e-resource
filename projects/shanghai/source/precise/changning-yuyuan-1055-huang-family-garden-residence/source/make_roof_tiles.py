"""Draw the original repeatable four-course red clay roof finish."""
from math import cos, sin, pi
from pathlib import Path
from PIL import Image

def make_texture(target):
    im = Image.new("RGB", (144, 144))
    pixels = im.load()
    for y in range(144):
        row = y // 36
        v = (y % 36) / 36
        for x in range(144):
            s = x / 36 + (row % 2) * .10
            u = s % 1
            col = int(s) % 4
            wave = .60*cos(2*pi*u) + .4*cos(4*pi*u+.2)
            firing = 5*sin(pi*col/2+.7*row) + 3*cos(pi*row/2)
            variation = 2*sin(2*pi*(17*x+29*y)/144) + 1.7*cos(2*pi*(9*x-15*y)/144)
            tone = firing + variation + 9.5*wave + (-26 if v>.92 else 6.5 if v<.08 else 0)
            pixels[x,y] = tuple(max(0,min(255,round(base+gain*tone))) for base,gain in ((160,1),(113,.80),(99,.72)))
    im.save(target,optimize=True)

if __name__ == "__main__":
    make_texture(Path(__file__).with_name("huang-roof-tiles.png"))
