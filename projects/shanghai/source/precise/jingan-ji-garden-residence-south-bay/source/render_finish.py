"""Original, deterministic fine grey aggregate render. The photographs supply no pixels."""
from pathlib import Path
ATLAS=Path(__file__).with_name('street-aggregate.png')
def stone_uv(x,y,z):
    return max(0,min(1,(.81*x+.48*y+5)/12)),max(0,min(1,z/17.8))
def generate():
    import random
    from PIL import Image
    rng=random.Random(490437231)
    tones=[(210+p,207+p,197+p) for p in (-23,-14,-10,-7,-5,-3,-2,0,1,3,5,8,12)]
    im=Image.new('P',(384,320))
    im.putpalette([v for t in tones for v in t]+[0]*(768-3*len(tones)))
    im.putdata(rng.choices(range(len(tones)),(1,2,3,4,5,6,9,12,8,8,5,3,2),k=384*320))
    im.save(ATLAS,optimize=True,bits=4)
if __name__=='__main__':
    generate()
