"""Draw a repeatable grey stretcher bond using the colours of the public photograph."""
from pathlib import Path
WIDTH_M, HEIGHT_M = 1.92, .96

def uv(x,y,z):
    return ((x+.68*y)/WIDTH_M, -z/HEIGHT_M)

if __name__ == '__main__':
    from random import Random
    from PIL import Image
    rng=Random(1930)
    image=Image.new('RGB',(256,128));pix=image.load()
    brick_tones={(r,c):rng.randrange(-13,14) for r in range(8) for c in range(8)}
    for y in range(128):
        course=y//16
        for x in range(256):
            offset=(x+(16 if course%2 else 0))%256
            if y%16<=1 or offset%32<=1:
                shade=rng.randrange(-4,5);base=(158,155,150)
            else:
                shade=brick_tones[(course,offset//32)]+rng.randrange(-7,8);base=(105,108,106)
            pix[x,y]=tuple(v+shade for v in base)
    image.save(Path(__file__).with_name('grey-brick.png'),optimize=True)
