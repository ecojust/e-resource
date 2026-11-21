"""Generate the repeatable original aggregate colour tile. The image is made without photographic input."""
from pathlib import Path
from random import Random
from PIL import Image,ImageDraw


def generate():
    n=320
    rng=Random(5171926)
    image=Image.new('RGB',(n,n));pixels=[]
    for _ in range(n*n):
        q=rng.gauss(0,8)
        pixels.append(tuple(round(max(0,min(255,c+q))) for c in (150,148,137)))
    image.putdata(pixels);pen=ImageDraw.Draw(image)
    # Each colour cluster straddling an edge has a matching cluster at the opposite edge.
    tones=[(119,119,111),(113,111,106),(172,168,151),(183,181,166),(144,144,135),(157,153,140)]
    for _ in range(12600):
        x,y=rng.randrange(n),rng.randrange(n);size=rng.choices([1,2,3],[4,5,1])[0]
        tone=rng.choice(tones);slant=rng.choice([-1,0,1])
        for dx in ((0,-n) if x+size+1>=n else (0,n) if x<1 else (0,)):
            for dy in ((0,-n) if y+size>=n else (0,)):
                a,b=x+dx,y+dy
                pen.polygon([(a,b),(a+size,b),(a+size+slant,b+max(1,size-1)),(a+slant,b+size)],fill=tone)
                if size>1:pen.point((a,b),fill=tuple(min(255,v+12)for v in tone))
    image.save(Path(__file__).with_name('pebble-dash.png'),optimize=True)


if __name__=='__main__':
    generate()
