"""Original repeatable grey-brick artwork, eight 260 mm stretchers by eight 72 mm courses."""
from pathlib import Path

def wall_uv(x,y,z):
    return ((x+.74*y)/2.08,-z/.576)

def generate(path):
    from PIL import Image
    from random import Random
    rng=Random(1888)
    tones=[[rng.randint(-8,8) for col in range(8)]for row in range(8)]
    image=Image.new('RGB',(384,128)); pixels=image.load()
    for y in range(128):
        row=y//16
        for x in range(384):
            offset=(x+(row%2)*24)%384
            joint=offset%48<2 or y%16<2
            value=(151 if joint else 96+tones[row][offset//48])+rng.randint(-4,4)
            pixels[x,y]=(value+1,value,value-2)
    image.save(path,optimize=True)

if __name__=='__main__':
    generate(Path(__file__).with_name('grey-bond.png'))
