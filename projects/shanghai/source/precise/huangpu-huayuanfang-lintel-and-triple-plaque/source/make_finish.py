"""Generate the weathered grey paint and render on the Huayuanfang gateway."""
from pathlib import Path
from PIL import Image
import random
def write():
    generator=random.Random(557)
    colors=bytearray()
    for _ in range(384*384):
        value=generator.gauss(0,3)
        colors.extend(max(0,min(255,round(v+value))) for v in (160,159,149))
    tile=Image.frombytes('RGB',(384,384),bytes(colors))
    tile.save(Path(__file__).with_name('finish.png'),optimize=True)
if __name__=='__main__':write()
