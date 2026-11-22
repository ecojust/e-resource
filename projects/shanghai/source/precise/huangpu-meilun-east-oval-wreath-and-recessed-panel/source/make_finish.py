"""Generate the light weathered stone based on the photographed facade."""
from pathlib import Path
from PIL import Image
import random
def write():
    generator=random.Random(525)
    colors=[]
    for _ in range(384*384):
        value=generator.gauss(0,3)
        colors.append(tuple(max(0,min(255,round(v+value))) for v in (133,130,120)))
    tile=Image.new('RGB',(384,384))
    tile.putdata(colors)
    tile.save(Path(__file__).with_name('finish.png'),optimize=True)
if __name__=='__main__':write()
