"""Original, deterministic ochre plaster with tiny lime grains. The photographs supply no pixels."""
from pathlib import Path
ATLAS=Path(__file__).with_name('courtyard-ochre.png')
def plaster_uv(x,y,z):
    return max(0,min(1,(.67*x+.41*y+8.4)/16.8)),max(0,min(1,z/11.6))
def generate():
    import random
    from PIL import Image
    rng=random.Random(13211912)
    tones=[(203+p,183+p,147+p) for p in (-23,-14,-10,-7,-5,-3,-2,0,1,3,5,8,12)]
    im=Image.new('P',(256,288))
    im.putpalette([v for t in tones for v in t]+[0]*(768-3*len(tones)))
    im.putdata(rng.choices(range(len(tones)),(1,2,3,4,5,6,9,12,8,8,5,3,2),k=256*288))
    im.save(ATLAS,optimize=True,bits=4)
if __name__=='__main__':
    generate()
