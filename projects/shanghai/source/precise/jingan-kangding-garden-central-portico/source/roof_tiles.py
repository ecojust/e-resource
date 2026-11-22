"""A repeatable unclipped ceramic roof texture made for the Kangding Garden model."""
from math import cos, tau
from pathlib import Path
from random import Random
from PIL import Image

def roof_uv(x,y,z):
    return x/1.08, -(y*.73+z*.60)/.87

def generate(path):
    rng=Random(19231925);n=120;colour=Image.new('RGB',(n,n));pix=colour.load()
    shifts=[[rng.randrange(-10,11) for c in range(6)]for r in range(3)]
    for y in range(n):
        for x in range(n):
            course=y//40;u=(x+10*(course%2))%n;tile=u//20
            shade=shifts[course][tile]+int(11*cos((u%20)*tau/20))+rng.randrange(-3,4)
            if y%40 in (0,1,2):shade-=31
            if u%20<2:shade-=14
            pix[x,y]=tuple(c+shade for c in (166,110,79))
    colour.save(path,optimize=True)
if __name__=='__main__':generate(Path(__file__).with_name('tiles.png'))
