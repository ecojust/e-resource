from pathlib import Path
from PIL import Image, ImageDraw
from random import Random
out=Path(__file__).with_name('arnhold-red-brick.png')
# Original, deterministic staggered red masonry matching the documented exposed brick at the street corner. The bitmap covers 32 x 32 metres.
rng=Random(320);im=Image.new('RGB',(1536,2048),(132,102,91));d=ImageDraw.Draw(im)
for j in range(416):
 y=round(j*2048/416);b=round((j+1)*2048/416)-1
 for i in range(-1,130):
  x=round((i+(j%2)/2)*12);x1=x+11;v=rng.randrange(-8,9);c=(152+v,88+v,77+v)
  d.rectangle((x+1,y,x1,b-1),fill=c)
im.save(out,optimize=True)
