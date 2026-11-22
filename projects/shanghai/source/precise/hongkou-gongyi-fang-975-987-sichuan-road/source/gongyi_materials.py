"""Original material interpretations of the restored Gongyi Fang No. 3 street front."""
from pathlib import Path

SOURCE = Path(__file__).parent
BRICK = 'Gongyi 3 | cleaned running-bond brick'
STONE = 'Gongyi 3 | grey-beige washed aggregate'
TRIM = 'Gongyi 3 | pale stone dressings'
SOFFIT = 'Gongyi 3 | shaded mineral plaster'
WOOD = 'Gongyi 3 | red brown timber'
DOOR_GLASS = 'Gongyi 3 | reflected balcony glass'
STEEL = 'Gongyi 3 | slender shopfront metal'
SHOP_GLASS = 'Gongyi 3 | shop glazing'
SHOP_SHADE = 'Gongyi 3 | grey shop fascia'
SOUTH_RECESS = 'Gongyi 3 | shaded end-wall inset'
DARK_RECESS = 'Gongyi 3 | shaded open doorway'
TILE = 'Gongyi 3 | terracotta roof tile'
RIDGE = 'Gongyi 3 | clay ridge capping'


def paint(rgb, roughness, metal=0):
    def linear(v):
        s = v / 255
        return s / 12.92 if s < .04045 else ((s + .055) / 1.055) ** 2.4
    return dict(color=[linear(v) for v in rgb], roughness=roughness, metallic=metal)


PALETTE = {
    BRICK: dict(color=[1., 1., 1.], roughness=.96, texture=str(SOURCE / 'restored-brick.png')),
    STONE: paint((161, 151, 132), .93), TRIM: paint((196, 184, 158), .86),
    SOFFIT: paint((142, 136, 121), .95), WOOD: paint((73, 49, 40), .68),
    DOOR_GLASS: paint((94, 99, 98), .32, .16), STEEL: paint((39, 43, 40), .60, .20),
    SHOP_GLASS: paint((85, 103, 98), .31, .18), SHOP_SHADE: paint((103, 102, 93), .82),
    TILE: dict(color=[1., 1., 1.], roughness=.95, texture=str(SOURCE / 'clay-tile.png')),
    SOUTH_RECESS: paint((83, 62, 57), .95),
    RIDGE: paint((138, 97, 77), .89), DARK_RECESS: paint((33, 31, 29), .98),
}
