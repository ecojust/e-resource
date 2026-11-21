"""Original running-bond brick colors and continuous horizontal and vertical UV coordinates."""
from pathlib import Path
from random import Random
from PIL import Image
def wall_uv(x,y,z):
    return (x+.35*y)/1.92,-z/.48
def generate(target):
    rng=Random(289704)
    out=Image.new('RGB',(192,48));px=out.load()
    colour={(r,c):rng.randrange(-11,10) for r in range(8)for c in range(8)}
    for y in range(48):
        row=y//6
        for x in range(192):
            u=(x+12*(row%2))%192;tone=colour[row,u//24]+rng.randrange(-5,6)
            base=(116,98,83) if u%24==0 or y%6==0 else (107,78,69)
            px[x,y]=tuple(ch+tone for ch in base)
    out.save(target,optimize=True)
if __name__=='__main__':generate(Path(__file__).with_name('brick.png'))
