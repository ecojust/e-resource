"""Handmade warm-and-dark running brick courses for the 2026 corner facade."""
from math import hypot
from pathlib import Path
from random import Random
from PIL import Image

def wall_uv(x,y,z):
    return (1 if x>=0 else -1)*hypot(x,y)/1.92,-z/.64

def generate(path):
    image=Image.new('RGB',(192,64));px=image.load();rng=Random(291588)
    shades={(col,row):rng.randrange(-15,15) for col in range(12) for row in range(8)}
    for y in range(64):
        row=y//8
        for x in range(192):
            offset=(x+(row%2)*8)%192;col=offset//16
            base=(130,113,100) if offset%16==0 or y%8==0 else ((123,87,74) if (col+row)%3 else (96,78,70))
            jitter=shades[col,row]+rng.randrange(-4,5)
            px[x,y]=tuple(c+jitter for c in base)
    image.save(path,optimize=True)

if __name__=='__main__':generate(Path(__file__).with_name('brick.png'))
