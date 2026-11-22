"""Original procedural roughcast surface and the tower's concrete and iron finishes."""
from pathlib import Path
from tower_frame import MASONRY, BORDER, LIP, IRON
from lookout import CAGE, STEPS, WINDOW, SASH, DECK

HERE = Path(__file__).resolve().parent
TEXTURE = HERE/'weathered-concrete.png'


def material(rgb, roughness, metal=0):
    c = [x/255 for x in rgb]
    linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in c]
    return {'color': linear, 'roughness': roughness, 'metallic': metal}


PALETTE = {
    MASONRY: material([153,148,131], .97),
    BORDER: material([113,108,96], .95),
    LIP: material([159,152,136], .93),
    IRON: material([80,77,69], .80, .30),
    CAGE: material([76,79,72], .73, .37),
    STEPS: material([103,98,88], .79, .32),
    WINDOW: material([121,140,137], .28, .20),
    SASH: material([74,72,61], .70, .20),
    DECK: material([120,119,106], .95),
}


def generate_texture():
    """Generate dust, exposed aggregate and vertical rain marks without image inputs."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(1909352)
    width,height = 660,1100
    def field(nx,ny):
        grid=rng.integers(0,256,(ny,nx),dtype=np.uint8)
        return np.asarray(Image.fromarray(grid).resize((width,height), Image.Resampling.BICUBIC),
                          dtype=float)/255
    coarse = field(27,43)
    streak = field(164,14)
    bloom = field(40,57)
    y = (np.arange(height)[:,None]+.5)/height
    z = 35.6*(1-y)
    factor = 1 - .14*np.exp(-z/2.8)
    for ledge in (9.17,16.70,24.06,29.15,33.29):
        below = ledge-z
        factor = factor - .16*np.exp(-np.maximum(below,0)/.95)*(below>=0)*(.28+streak)
    # Water concentrates above the cab's lower sill and at the base of the feet.
    # These irregular marks are generated, not sampled from the reference photographs.
    cabinet=np.exp(-((z-29.63)/.78)**2)
    lichen=np.clip((.60-bloom)*2.6,0,1)*np.clip((1.14+coarse*.97-z)/1.20,0,1)
    factor = factor - cabinet*(.045+.24*np.maximum(0,(streak-.27)*1.8)) - .20*lichen
    delta = (coarse-.5)*22 + (streak-.5)*17 + 19*np.maximum(bloom-.55,0)
    delta += rng.normal(0,4.3,(height,width))
    colors = np.array([155,150,135])
    rgb = np.clip(factor[...,None]*colors + delta[...,None],0,255).astype('uint8')
    Image.fromarray(rgb).quantize(colors=114,dither=Image.Dither.NONE).save(TEXTURE,optimize=True)


def apply(builder):
    if not TEXTURE.is_file():
        generate_texture()
    builder.palette[MASONRY] = dict(color=[1,1,1], roughness=.97, metallic=0, texture=str(TEXTURE))
    for part in builder.parts:
        if part['material'] == MASONRY:
            part['texcoords'] = [(.5+(x+1.17*y)*.027,1-(z+.12)/35.6) for x,y,z in part['vertices']]
            assert all(0 <= u <= 1 and 0 <= v <= 1 for u,v in part['texcoords'])


if __name__=='__main__':
    generate_texture()
