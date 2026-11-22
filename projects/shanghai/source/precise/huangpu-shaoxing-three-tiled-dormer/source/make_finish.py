"""Generate the weathered red earthenware visible on the dormer roof."""
from pathlib import Path
from PIL import Image
import random
def write():
    generator=random.Random(549)
    colors=[]
    for _ in range(384*384):
        value=generator.gauss(0,5)
        colors.append(tuple(max(0,min(255,round(v+value))) for v in (120,79,65)))
    tile=Image.new('RGB',(384,384))
    tile.putdata(colors)
    tile.save(Path(__file__).with_name('finish.png'),optimize=True)
if __name__=='__main__':write()
