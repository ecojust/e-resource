"""Original narrow reddish facade tiles with light vertical joints."""
from pathlib import Path
from random import Random
from PIL import Image
def wall_uv(x,y,z):
    return (x+.5*y)/1.68,-z/.96

def generate(path):
    image=Image.new('RGB',(168,96));px=image.load();rng=Random(3061930)
    shades={(c,r):rng.randrange(-12,13)for c in range(21)for r in range(4)}
    for y in range(96):
        for x in range(168):
            column,row=x//8,y//24
            colour=(171,147,135)if x%8==0 or y%24==0 else (161,92,73)
            delta=shades[column,row]+rng.randrange(-4,5)
            px[x,y]=tuple(c+delta for c in colour)
    image.save(path,optimize=True)
if __name__=='__main__':generate(Path(__file__).with_name('brick.png'))
