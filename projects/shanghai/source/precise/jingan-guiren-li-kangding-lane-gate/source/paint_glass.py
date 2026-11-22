"""Paint an original seamless neutral glass surface for the Guiren Li window panes."""
from math import cos, pi
from pathlib import Path
import sys
from PIL import Image

def paint(path):
    im=Image.new('RGB',(48,48))
    for y in range(im.height):
        for x in range(im.width):
            u,v=x/im.width,y/im.height
            value=round(248+2*cos(2*pi*(u+v))+.9*cos(2*pi*(u-2*v))+.7*cos(2*pi*v))
            im.putpixel((x,y),(value-1,value,value+1))
    im.save(path,optimize=True)

if __name__=='__main__':
    paint(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('guiren-window-glass.png'))
