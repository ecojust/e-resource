"""Original surface finishes for the street portal, terrace and pavement."""
from pathlib import Path

BRICK = 'Gatehouse | grey reclaimed brick'
OCHRE = 'Gatehouse | warm mineral render'
WEST = 'Gatehouse | pale buff west wall'
CREAM = 'Gatehouse | buff stone cornice'
STONE = 'Gatehouse | weathered plinth stone'
CLAY = 'Gatehouse | orange brick string course'
STREET = 'Gatehouse | pavement flags'
SHADE = 'Gatehouse | shaded plaster'
SHEET = 'Gatehouse | weathered green sheet'
WINE = 'Gatehouse | faded mulberry awning'
ROSE = 'Gatehouse | warm awning seam'
LINING = 'Gatehouse | shaded canvas'
FITTING = 'Gatehouse | patinated metal frame'
BRONZE = 'Gatehouse | aged bronze'
BOARD = 'Gatehouse | ochre name panel'
CREST = 'Gatehouse | light rim'
GLASS = 'Gatehouse | side window glass'
WOOD = 'Gatehouse | dark side window timber'


def paint(rgb, roughness, metal=0):
    def linear(c):
        v = c / 255
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    return {'color': [linear(c) for c in rgb], 'roughness': roughness, 'metallic': metal}


PALETTE = {
    BRICK: {'color':[1.,1.,1.], 'roughness':.94,
            'texture': str(Path(__file__).with_name('grey-running-bond.png'))},
    OCHRE:paint((201,179,130),.93), WEST:paint((186,178,157),.92),
    CREAM:paint((206,195,168),.88), STONE:paint((135,128,112),.94), CLAY:paint((157,91,65),.86),
    STREET:paint((128,123,112),.97), SHADE:paint((150,146,127),.95),
    SHEET:paint((60,101,100),.64,.16), WINE:paint((147,87,94),.91),
    ROSE:paint((166,107,111),.89), LINING:paint((106,74,81),.93),
    FITTING:paint((105,102,89),.60,.31), BRONZE:paint((94,81,63),.54,.30),
    BOARD:paint((146,126,88),.90), CREST:paint((190,178,149),.81),
    GLASS:paint((111,128,128),.34,.12), WOOD:paint((93,88,74),.76)
}


def make_brick():
    import numpy as np
    from PIL import Image
    # One UV repeat is 1.282 m across and high. Six stretchers and twenty
    # courses approximate the visible facing in the 2025 municipal photograph.
    size = 360
    rng = np.random.default_rng(1376)
    rows, cols = np.indices((size,size))
    course = rows // 18
    running = (cols + (course % 2) * 30) % size
    unit = running // 60
    variation = rng.normal(0,8,(20,6))[course,unit]
    grain = rng.normal(0,4,(size,size))
    brick = np.array([123.,121.,111.]) + (variation+grain)[:,:,None]
    mortar = np.array([177.,171.,151.]) + grain[:,:,None] * .55
    edges = np.minimum(np.minimum(rows % 18, 18 - rows % 18),np.minimum(running % 60,60-running % 60))
    weight = np.clip((2.0-edges)/1.6,0,1)[:,:,None]
    rgb = np.clip(brick*(1-weight)+mortar*weight,0,255).astype('uint8')
    Image.fromarray(rgb).save(Path(__file__).with_name('grey-running-bond.png'),optimize=True)


if __name__ == '__main__':
    make_brick()
