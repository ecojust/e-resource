"""Paint, polished aggregate, joinery and shades seen on the garden facade."""
from pathlib import Path


def paint(rgb, roughness, metallic=0.):
    def linear(v):
        s=v/255
        return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
    return dict(color=[linear(v) for v in rgb],roughness=roughness,metallic=metallic)


MASONRY='Zhu residence | cream scored facade'
REVEAL='Zhu residence | grey painted arch margin'
PLASTER='Zhu residence | sheltered warm plaster'
STONE='Zhu residence | pale exposed aggregate'
STAIR='Zhu residence | rose and grey terrazzo'
STONE_EDGE='Zhu residence | projecting drip and sill'
WOOD='Zhu residence | deep brown timber'
GLASS='Zhu residence | sheltered door glazing'
GROOVE='Zhu residence | recessed horizontal joint'
PALETTE={
    MASONRY:paint((217,207,182),.93), REVEAL:paint((117,119,123),.86),
    PLASTER:paint((211,198,168),.95), STONE:paint((178,172,158),.89),
    STAIR:paint((161,143,138),.84), STONE_EDGE:paint((111,111,108),.88),
    WOOD:paint((63,49,40),.74), GLASS:paint((90,94,85),.38,.15),
    GROOVE:paint((133,126,112),.95),
}

PALETTE[STAIR].update(color=[1.,1.,1.],texture=str(Path(__file__).with_name('zhu-rose-terrazzo.png')))


def make_terrazzo():
    """A seamless, 0.25 m square synthetic sample of the exposed rose aggregate."""
    from PIL import Image, ImageDraw
    from random import Random
    rng=Random(19684)
    width=128
    image=Image.new('RGB',(width,width))
    def tone(base,variation):
        return tuple(max(0,min(255,value+variation)) for value in base)
    image.putdata([tone((155,135,127),rng.randint(-10,10)) for _ in range(width*width)])
    draw=ImageDraw.Draw(image)
    stones=[(111,100,97),(189,171,160),(207,197,182),(130,111,106),(164,148,137)]
    for _ in range(2800):
        x=rng.randrange(width);y=rng.randrange(width)
        reach=rng.choice([1,1,2,2,3])
        color=tone(rng.choice(stones),rng.randrange(-9,10))
        for left in (x,x-width) if x+reach>=width else (x,):
            for top in (y,y-width) if y+reach>=width else (y,):
                draw.polygon([(left,top+1),(left+reach,top),(left+reach-1,top+reach)],fill=color)
    image.save(Path(__file__).with_name('zhu-rose-terrazzo.png'),optimize=True)


if __name__=='__main__':
    make_terrazzo()
