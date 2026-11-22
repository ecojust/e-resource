"""Procedural red brick with staggered mortar beds. Source photos remain external."""
from pathlib import Path
from PIL import Image
import random
rng=random.Random(493)
w,h=640,512
im=Image.new('RGB',(w,h));pix=im.load()
# Repeatable stretcher brick face, with small variations in red firing tone.
for y in range(h):
    course=y//8
    for x in range(w):
        brick=(x+10*(course%2))//20
        vertical=(x+10*(course%2))%20
        joint=y%8==0 or vertical==0
        tone=((brick*19+course*17)%13)-6
        noise=rng.randrange(-5,6)
        color=(143,121,107) if joint else (158+tone,89+tone//2,71+tone//2)
        pix[x,y]=tuple(v+noise for v in color)
im.save(Path(__file__).with_name('finish.png'),optimize=True)
