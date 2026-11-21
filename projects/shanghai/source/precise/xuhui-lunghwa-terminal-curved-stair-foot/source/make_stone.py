"""Make a softly banded, original stone base-color swatch."""
from math import sin,cos,exp
from pathlib import Path
from random import Random
from PIL import Image
rng=Random(1946)
im=Image.new('RGB',(256,256));out=[]
for j in range(256):
    for i in range(256):
        cloud=sin(i*.035+j*.052+1.35*sin(j*.063))+cos(i*.047-j*.018)
        meander=(i*.8+j+.93*sin(i*.048)*10+sin(j*.026)*8)%79
        vein=exp(-((meander-23)/2.3)**2)*5.3
        delta=2.8*cloud-vein+rng.uniform(-1.5,1.5)
        out.append(tuple(round(c+delta)for c in (222,203,174)))
im.putdata(out)
im.save(Path(__file__).with_name('pale-stone.png'))
