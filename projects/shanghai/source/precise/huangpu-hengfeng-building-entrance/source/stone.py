"""A repeatable original mineral-grain texture for the worn grey facing."""
from pathlib import Path
from math import cos, pi, sin
from random import Random

def wall_uv(x,y,z):
    return ((x+.65*y)/1.92, -z/1.92)

def generate(path):
    from PIL import Image
    rng=Random(450454)
    image=Image.new('RGB',(128,128))
    for y in range(128):
        for x in range(128):
            grain=rng.gauss(0,3)
            fleck=2.2*sin(2*pi*x/128)*cos(4*pi*y/128)+sin(6*pi*(x+y)/128)
            neutral=round(164+grain+fleck)
            image.putpixel((x,y),(neutral+2,neutral+1,neutral-5))
    image.save(path,optimize=True)
if __name__=='__main__':
    generate(Path(__file__).with_name('ashlar-grain.png'))
