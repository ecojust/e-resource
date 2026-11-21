"""Draw the river elevation masonry field from measured brick proportions."""
from pathlib import Path
from random import Random
from PIL import Image, ImageDraw
def render(path):
    width,height=1536,1536
    rng=Random(190622)
    image=Image.new('RGB',(width,height),(150,106,88))
    draw=ImageDraw.Draw(image)
    for row in range(354):
        top,bottom=round(row*height/354),round((row+1)*height/354)-1
        start=-7 if row%2 else 0
        # The distant photograph does not establish a continuous bond over the full wall.
        # Use a half-length offset for the exposed stretchers, with limited tonal variation.
        for x in range(start,width,13):
            shade=rng.randrange(-8,9)
            draw.rectangle((x+1,top+1,x+12,bottom),fill=(165+shade,80+shade,56+shade))
    image.save(path,optimize=True)
if __name__=='__main__':render(Path(__file__).with_name('swire-river-brick.png'))
