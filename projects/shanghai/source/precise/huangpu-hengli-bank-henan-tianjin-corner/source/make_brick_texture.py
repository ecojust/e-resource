from pathlib import Path
from PIL import Image, ImageDraw
from random import Random
out=Path(__file__).with_name('brown-brick-bond.png')
# Original, deterministic English garden-wall-like stretcher bond based on the 2020 corner close-up. The bitmap covers 32 x 32 metres.
rng=Random(495);im=Image.new('RGB',(1536,2048),(126,119,104));d=ImageDraw.Draw(im)
for j in range(416):
 y=round(j*2048/416);b=round((j+1)*2048/416)-1
 for i in range(-1,130):
  x=round((i+(j%2)/2)*12);x1=x+11;v=rng.randrange(-8,9);c=(77+v,69+v,62+v)
  d.rectangle((x+1,y,x1,b-1),fill=c)
im.save(out,optimize=True)
