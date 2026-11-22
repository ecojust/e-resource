"""Original repeatable close-grain granite. UVs use metres in the author's frame."""
from pathlib import Path

def texture_uv(x, y, z):
    return ((x+.73*y)/.83, z/.83+.27*y)

if __name__ == '__main__':
    from random import Random
    from PIL import Image
    rng = Random(1921)
    pixels = []
    for _ in range(128*128):
        grain = rng.gauss(0,3.2)
        mineral = rng.random()
        if mineral < .035:
            grain -= 8
        elif mineral > .976:
            grain += 10
        pixels.append(tuple(round(base+grain) for base in (160,148,134)))
    image = Image.new('RGB',(128,128))
    image.putdata(pixels)
    image.save(Path(__file__).with_name('granite.png'), optimize=True)
