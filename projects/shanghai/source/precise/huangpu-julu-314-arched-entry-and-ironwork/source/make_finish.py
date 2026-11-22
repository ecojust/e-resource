"""Generate the light grey render of the numbered gate piers."""
from pathlib import Path
from PIL import Image
import random
def write():
    generator=random.Random(553)
    colors=bytearray()
    for _ in range(384*384):
        value=generator.gauss(0,3)
        colors.extend(max(0,min(255,round(v+value))) for v in (168,164,151))
    tile=Image.frombytes('RGB',(384,384),bytes(colors))
    tile.save(Path(__file__).with_name('finish.png'),optimize=True)
if __name__=='__main__':write()
