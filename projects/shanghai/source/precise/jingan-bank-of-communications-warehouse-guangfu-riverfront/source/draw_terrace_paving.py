"""Generate the original paving atlas of the Guangfu Road river terrace."""
from pathlib import Path
from PIL import Image, ImageDraw
def draw(path):
    # 72 by 32 metres of uninterrupted texture in the plan coordinate basis.
    # A source photo shows rectangular courses; individual slab size is approximate.
    scale=32
    im=Image.new('RGB',(72*scale,32*scale),(132,134,134))
    d=ImageDraw.Draw(im)
    w,h=25,14
    for row,y in enumerate(range(-h,im.height,h)):
        offset=-(row%2)*(w//2)
        for col,x in enumerate(range(offset-w,im.width,w)):
            tint=(row*7+col*3+row*col%7)%9-4
            c=tuple(v+tint for v in (157,159,157))
            d.rectangle((x+1,y+1,x+w-1,y+h-1),fill=c)
    im.resize((1152,512),Image.Resampling.LANCZOS).save(path,optimize=True)
if __name__=='__main__':
    draw(Path(__file__).with_name('roof-terrace-paving.png'))
