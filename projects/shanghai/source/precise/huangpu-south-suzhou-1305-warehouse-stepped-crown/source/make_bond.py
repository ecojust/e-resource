"""Draw an original running-bond texture at the measured façade scale."""
from pathlib import Path
import random
from PIL import Image,ImageDraw
rng=random.Random(1305);size=(768,400);out=Image.new('RGB',size,(151,137,115));d=ImageDraw.Draw(out)
for row in range(76):
    y=round(row*5.4);yn=round((row+1)*5.4)
    for col in range(-1,48):
        x=round((col+.5*(row%2))*16.4);right=round((col+1+.5*(row%2))*16.4)
        tone=rng.randrange(-9,10);color=tuple(c+tone for c in (192,163,122))
        d.rectangle((x+1,y,right-1,yn-2),fill=color)
        d.line((x+1,yn-2,right-1,yn-2),fill=tuple(c-7 for c in color))
out.save(Path(__file__).with_name('brick-bond.png'),optimize=True)
