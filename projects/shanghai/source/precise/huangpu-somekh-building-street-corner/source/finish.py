"""Original rendering of the rice-grain aggregate recorded by the conservation architects."""
from pathlib import Path
import random

TEXTURE = Path(__file__).with_name('washed-aggregate.png')
WALL = 'warm grey washed aggregate'
GRANITE = 'warm granite'
TRIM = 'pale cut moulding'
BED = 'shadow in ashlar joint'
BASE = 'grey granite plinth'
IRON = 'dark forged iron'
SASH = 'slender steel casement'
GLASS = 'recessed blue grey glass'
DOOR = 'dark glazed timber'
TERRAZZO = 'restored terrazzo'
CAP = 'weathered drum cap'
LETTER = 'dark fascia lettering'
PALETTE = {name:{'color':rgb,'roughness':roughness} for name,rgb,roughness in [
    (WALL,[1,1,1],.89),(GRANITE,[.51,.45,.38],.82),(TRIM,[.64,.58,.48],.78),
    (BED,[.34,.30,.26],.91),(BASE,[.34,.33,.32],.85),(IRON,[.075,.072,.062],.55),
    (SASH,[.12,.135,.135],.58),(GLASS,[.21,.31,.34],.34),(DOOR,[.14,.094,.069],.57),
    (TERRAZZO,[.57,.55,.48],.73),(CAP,[.51,.48,.43],.84),(LETTER,[.077,.069,.059],.65)]}
PALETTE[WALL]['texture'] = str(TEXTURE)

def texture_uv(x,y,z):
    # Use a diagonal planar projection so the pattern runs on both street elevations.
    return ((x+.68*y)/1.36,z/1.20)

def make_texture():
    from PIL import Image,ImageDraw
    rng=random.Random(192104)
    width,height=448,320
    image=Image.new('RGB',(width,height))
    image.putdata([(173+t,163+t,148+t)for t in (rng.randint(-6,6)for _ in range(width*height))])
    draw=ImageDraw.Draw(image)
    for _ in range(14860):
        x,y=rng.randrange(width),rng.randrange(height)
        shade=rng.choices([(189,184,173),(163,155,146),(139,136,130)],weights=(7,5,1))[0]
        draw.point((x,y),shade)
    image.save(TEXTURE,optimize=True)

if __name__=='__main__':make_texture()
