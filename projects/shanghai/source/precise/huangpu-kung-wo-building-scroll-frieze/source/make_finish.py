from pathlib import Path
from PIL import Image
import random
from math import sin
rng=random.Random(501)
w,h=384,256
im=Image.new('RGB',(w,h));pix=im.load()
for y in range(h):
 for x in range(w):
  noise=rng.randrange(-5,6) + round(1.8*sin(.052*x+.021*y))
  pix[x,y]=tuple(c+noise for c in (216,211,198))
im.save(Path(__file__).with_name('finish.png'),optimize=True)
