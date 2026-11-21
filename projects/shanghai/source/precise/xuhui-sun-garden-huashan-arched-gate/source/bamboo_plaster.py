"""Draw original bamboo branch marks seen in the 831 street photograph."""
from pathlib import Path
from random import Random
from math import sin
from PIL import Image,ImageDraw
import numpy as np
WIDTH,HEIGHT=768,354

def pattern():
    random=Random(831)
    for row in range(7):
        for col in range(9):
            x=col*98+random.uniform(-35,25);y=row*58+random.uniform(-20,15)
            turn=random.choice([-1,1]);end=(x+turn*random.uniform(47,91),y+random.uniform(-18,17));mid=((x+end[0])/2,(y+end[1])/2-4)
            leaves=[]
            for ix in range(3,11):
                t=ix/12;xx=x+(end[0]-x)*t;yy=y+(end[1]-y)*t-4*sin(3.14*t);dx=turn*random.uniform(9,20);dy=random.choice([-1,1])*random.uniform(3,10);wx,wy=-dy*.082,dx*.082
                tips=[(xx,yy),(xx+dx*.40+wx,yy+dy*.40+wy),(xx+dx,yy+dy),(xx+dx*.42-wx,yy+dy*.42-wy)]
                leaves.append((tips,random.choice([(209,204,184),(219,214,197),(198,194,175)])))
            yield [(x,y),mid,end],leaves

def draw(path):
    im=Image.new('RGB',(WIDTH,HEIGHT),(244,239,224));d=ImageDraw.Draw(im)
    for stem,leaves in pattern():
        d.line(stem,fill=(204,198,178),width=1)
        for leaf,color in leaves:d.polygon(leaf,fill=color)
    a=np.asarray(im).astype('int16');gen=np.random.default_rng(831);a+=gen.normal(0,2.9,(HEIGHT,WIDTH,1)).astype('int16');Image.fromarray(np.clip(a,0,255).astype('uint8')).save(path)
if __name__=='__main__':draw(Path(__file__).with_name('bamboo-plaster.png'))
