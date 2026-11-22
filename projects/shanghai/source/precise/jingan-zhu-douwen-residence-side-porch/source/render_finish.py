"""Original grained tan finish for the photographs' visible painted side wall."""
from pathlib import Path
ATLAS=Path(__file__).with_name('garden-render.png')
def stone_uv(x,y,z):return max(0,min(1,(x+.25*y+10)/16)),max(0,min(1,z/10.1))
def generate():
    import random
    from PIL import Image
    rng=random.Random(490282146);im=Image.new('P',(288,224))
    variations=[-16,-11,-8,-5,-3,-1,0,2,4,6,9,12]
    im.putpalette([v+d for d in variations for v in (178,164,143)]+[0]*(768-3*len(variations)))
    im.putdata(rng.choices(range(len(variations)),[1,3,5,7,9,13,17,13,9,6,4,2],k=im.width*im.height))
    im.save(ATLAS,bits=4,optimize=True)
if __name__=='__main__':generate()
