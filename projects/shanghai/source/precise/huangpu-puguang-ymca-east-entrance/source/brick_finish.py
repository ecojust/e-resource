"""Generate the original running-bond texture for the 2023 exposed-brick facade."""
from pathlib import Path
import random

TEXTURE = Path(__file__).with_name('east-wall-bricks.png')

def texture_uv(x, y, z):
    return max(0,min(1,(x+10)/20)), max(0,min(1,z/15.2))

def draw_texture():
    from PIL import Image, ImageDraw
    rng=random.Random(19071004)
    width,height=880,680
    image=Image.new('RGB',(width,height),(151,117,90))
    draw=ImageDraw.Draw(image)
    for i in range(196):
        y0=round(i*height/195)
        y1=round((i+1)*height/195)-1
        for j in range(-1,85):
            x0=round(j*width/83+(i%2)*width/166)
            x1=round((j+1)*width/83+(i%2)*width/166)-1
            tone=rng.randrange(-14,15)
            colour=(166+tone,99+tone,75+tone)
            draw.rectangle((x0,y0,x1-1,y1-1),fill=colour)
            if y1>y0+1:
                draw.point((x0+3,y1-1),fill=(156+tone,92+tone,70+tone))
    image.save(TEXTURE,optimize=True)

if __name__=='__main__':
    draw_texture()
