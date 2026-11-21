"""Draw a repeatable grey mineral-grain surface based on the documented washed finish."""
from pathlib import Path
from random import Random
from PIL import Image
def generate(destination):
    rng=Random(233)
    pixels=[]
    for _ in range(320*320):
        grain=rng.gauss(0,6.0)
        if rng.random()<.16:grain-=rng.uniform(7,24)
        elif rng.random()<.13:grain+=rng.uniform(4,14)
        pixels.append(tuple(max(0,min(255,round(v+grain)))for v in (239,237,234)))
    im=Image.new('RGB',(320,320));im.putdata(pixels);im.save(destination)
if __name__=='__main__':generate(Path(__file__).with_name('mineral-aggregate.png'))
