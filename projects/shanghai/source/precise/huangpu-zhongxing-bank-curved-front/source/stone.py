"""Original small-grain limestone appearance and continuous unwrapped corner coordinates."""
from math import atan2, cos, pi, sin
from pathlib import Path
from random import Random

def wall_uv(x,y,z):
    return 9.733486353059083*atan2(x,9.733486353059083-y)/2.2, -z/2.2

def generate(path):
    from PIL import Image
    grain=Random(41927284)
    out=Image.new('RGB',(128,128))
    for y in range(128):
        for x in range(128):
            drift=1.85*cos(2*pi*x/128)*sin(4*pi*y/128)
            v=round(187+grain.gauss(0,2.7)+drift)
            out.putpixel((x,y),(v+12,v+4,v-7))
    out.save(path,optimize=True)

if __name__=='__main__':
    generate(Path(__file__).with_name('limestone.png'))
