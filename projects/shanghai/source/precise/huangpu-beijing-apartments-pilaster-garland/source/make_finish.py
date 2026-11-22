"""Procedural red stretcher brick using the colour and narrow bedding observed on the street face."""
from pathlib import Path
from PIL import Image,ImageDraw
import random
def write():
    rng=random.Random(505);width,height=540,735
    im=Image.new('RGB',(width,height),(137,111,97));draw=ImageDraw.Draw(im)
    for row,y in enumerate(range(0,height,8)):
        for x in range((-15 if row%2 else 0)-30,width,30):
            change=rng.uniform(-8,8);rgb=tuple(round(v+change)for v in (150,90,76))
            draw.rectangle((x+1,y+1,x+29,y+7),fill=rgb)
            for _ in range(14):
                rise=rng.randint(-5,5);p=(x+rng.randint(1,29),y+rng.randint(1,7))
                draw.point(p,fill=tuple(c+rise for c in rgb))
    im.save(Path(__file__).with_name('finish.png'),optimize=True)
if __name__=='__main__':write()
