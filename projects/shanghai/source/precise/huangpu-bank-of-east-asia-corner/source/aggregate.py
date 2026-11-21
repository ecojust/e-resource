"""Original fine grey aggregate and vertically dressed stone, UVs in metres."""
from pathlib import Path

def texture_uv(x,y,z):
    return (x+.57*y)/.86,z/.86+.18*y

if __name__=='__main__':
    from random import Random
    from PIL import Image
    from math import sin,pi
    rng=Random(1926)
    image=Image.new('RGB',(128,128))
    pixels=[]
    for row in range(image.height):
        for col in range(image.width):
            grain=rng.gauss(0,3.8)+1.25*sin(2*pi*col/8)
            grain+=(-8 if rng.random()<.031 else 0)
            pixels.append(tuple(round(v+grain)for v in (155,149,141)))
    image.putdata(pixels)
    image.save(Path(__file__).with_name('aggregate.png'),optimize=True)
