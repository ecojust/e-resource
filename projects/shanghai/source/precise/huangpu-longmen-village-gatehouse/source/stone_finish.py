"""Original speckled granite finish with a bounded UV chart shared by glTF and Blender."""
from pathlib import Path

def texture_uv(x,y,z):
    return (x+.46*y+4.0)/11.0,(z+.10*y+.15)/16.0

if __name__=='__main__':
    from PIL import Image
    from random import Random
    rng=Random(1331935)
    image=Image.new('P',(192,320))
    levels=[(round(150+i*.94),round(145+i*.94),round(137+i*.92)) for i in range(-28,29)]
    image.putpalette([channel for colour in levels for channel in colour])
    grain=[]
    for row in range(image.height):
        for col in range(image.width):
            v=rng.gauss(0,5.3)
            if rng.random()<.037:v-=rng.uniform(6,15)
            grain.append(28+min(28,max(-28,round(v))))
    image.putdata(grain)
    image.save(Path(__file__).with_name('stone-grain.png'),optimize=True)
