"""Original, deterministic cream roughcast aggregate. The photographs supply no pixels."""
from pathlib import Path
ATLAS=Path(__file__).with_name('garden-roughcast.png')
def plaster_uv(x,y,z):
    return max(0,min(1,(.74*x+.68*y+7)/17)),max(0,min(1,z/10.5))
def generate():
    import random
    from PIL import Image
    rng=random.Random(490439140)
    tones=[(224+p,217+p,193+p) for p in (-23,-14,-10,-7,-5,-3,-2,0,1,3,5,8,12)]
    im=Image.new('P',(640,480))
    im.putpalette([v for t in tones for v in t]+[0]*(768-3*len(tones)))
    im.putdata(rng.choices(range(len(tones)),(1,2,3,4,5,6,9,12,8,8,5,3,2),k=640*480))
    im.save(ATLAS,optimize=True,bits=4)
if __name__=='__main__':
    generate()
