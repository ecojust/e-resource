"""Original seamless sinusoidal variation in reflected light. No photographs are sampled."""
import math
from pathlib import Path
from PIL import Image

def save(path):
    n=96
    image=Image.new('RGB',(n,n))
    pixels=image.load()
    for y in range(n):
        for x in range(n):
            a,b=2*math.pi*x/n,2*math.pi*y/n
            v=round(237+5*math.sin(2*a+b)+4*math.sin(b)+2*math.sin(3*b-a))
            pixels[x,y]=(v,min(255,v+1),min(255,v+3))
    image.save(path,optimize=True)

if __name__=='__main__':
    save(Path(__file__).with_name('warehouse-window-glass.png'))
