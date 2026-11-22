"""Generate an original brick material and map both street fronts in metres."""
from math import hypot
from pathlib import Path


def texture_uv(x,y,z):
    half=2.181363976878214
    if x < -half:
        along=-half-hypot(x+half,y)
    elif x > half:
        along=half+hypot(x-half,y)
    else:
        along=x
    return (along+9)/18,z/18


if __name__=='__main__':
    from PIL import Image, ImageDraw
    from random import Random

    pixels=1024
    rng=Random(238)
    image=Image.new('RGB',(pixels,pixels),(146,111,102))
    draw=ImageDraw.Draw(image)
    # Each four-pixel course represents about 70mm at full size.
    for course,y in enumerate(range(0,pixels,4)):
        offset=6*(course%2)
        for x in range(-offset,pixels,12):
            tone=rng.randrange(-10,11)
            color=(161+tone,89+tone,81+tone)
            draw.rectangle((x,y,x+10,y+2),fill=color)
            if rng.randrange(6)==0:
                draw.point((x+3,y+1),fill=(150+tone,81+tone,73+tone))
    image.save(Path(__file__).with_name('red-brick.png'),optimize=True)
