"""Seeded fine stucco and eighteen-course red brick pattern with a running bond."""
from pathlib import Path
import numpy as np
from PIL import Image
def make():
    here=Path(__file__).resolve().parent;rng=np.random.default_rng(629)
    field=rng.normal(0,2.4,(192,192,1))
    Image.fromarray(np.uint8(np.clip([216,208,188]+field,0,255))).save(here/'garden-stucco.png',optimize=True)
    width,height=384,396
    image=np.zeros((height,width,3),dtype=float)
    coarse=rng.integers(-10,11,(18,6))
    for y in range(height):
        row,cy=divmod(y,22)
        for x in range(width):
            col,cx=divmod((x+32*(row%2))%width,64)
            if cy<2 or cx<2: color=[139,119,99]
            else:color=np.array([135,72,49])+coarse[row,col]
            image[y,x]=color
    image+=rng.normal(0,3.9,(height,width,1))
    Image.fromarray(np.uint8(np.clip(image,0,255))).save(here/'garden-red-brick.png',optimize=True)
if __name__=='__main__':make()
