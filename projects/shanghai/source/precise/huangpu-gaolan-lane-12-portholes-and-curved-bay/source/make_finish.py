"""Generate the ochre pebble-dashed finish visible in the 2018 street photograph."""
from pathlib import Path
from PIL import Image
import random
def write():
    generator=random.Random(509)
    colors=[]
    for _ in range(384*384):
        value=generator.gauss(0,7)
        colors.append(tuple(max(0,min(255,round(v+value))) for v in (166,161,139)))
    tile=Image.new('RGB',(384,384))
    tile.putdata(colors)
    tile.save(Path(__file__).with_name('finish.png'),optimize=True)
if __name__=='__main__':write()
