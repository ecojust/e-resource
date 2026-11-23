"""West lawn elevation of No. 8, including the lettering fastened to the brick flue."""
import json
from pathlib import Path

from shapely.geometry import Polygon, box

from garden_fabric import BRICK, BRONZE, CREAM, METAL, PLINTH, block, face, paint

SURVEY = Path(__file__).resolve().parents[1] / 'measurements/eight-chimney-lettering.json'
DARK = 'Hongji 8 | dark single-light surround'
SKY = 'Hongji 8 | upper garden window glass'
SHADE = 'Hongji 8 | shaded lower garden glass'
SILL = 'Hongji 8 | sand-grey sill'
RAIL = 'Hongji 8 | painted letter carrier'
PALETTE = {DARK: paint((48, 51, 46), .67), SKY: paint((75, 84, 81), .24, .19),
           SHADE: paint((52, 61, 53), .27, .13), SILL: paint((160, 158, 141)),
           RAIL: paint((169, 155, 134), .71, .16)}

# The measured heads and jamb positions use all three lawn cameras. Upper
# sills can be seen in both periods. Hedges obscure the recent lower sills.
WINDOWS = [('upper left', 1.4873, 2.4262, 3.724, 5.1514),
           ('upper right', 4.6833, 5.6055, 3.714, 5.1495),
           ('ground left', .8910, 1.7716, .085, 2.1598),
           ('ground right', 5.2506, 6.1475, .112, 2.1556)]


def front_openings(layout):
    return {tag: box(x, low, right, high) for tag, x, right, low, high in WINDOWS}


def windows(b, lod):
    for tag, x, right, low, top in WINDOWS:
        label = '8 | '+tag+' garden window '
        upper = tag.startswith('upper')
        outer = box(x, low, right, top)
        clear = box(x+.045, low+.060, right-.044, top-.058)
        face(b, outer.difference(clear), .032, .138, DARK, label+'frame')
        if not lod:
            rebate = clear.difference(clear.buffer(-.011, join_style=2))
            face(b, rebate, .090, .143, METAL, label+'inner glazing bead')
        face(b, clear, .145, .164, SKY if upper else SHADE, label+'single glass light')
        block(b, x-.033, right+.034, -.089, .057, low-.069, low-.005, SILL, label+'sill')
        if not upper:
            block(b, x-.017, right+.019, -.031, .044, top+.001, top+.058, SILL, label+'lintel')


def lettered_breast(b, lod, layout):
    peak = layout['eave_z'] + layout['gable_rise']
    lower = box(2.645, -.035, 4.419, .566)
    face(b, lower, -.230, .031, PLINTH, '8 | chimney plinth')
    silhouette = Polygon([(2.645,.566),(4.419,.566),(4.419,4.20),(4.446,4.26),
                          (4.39,4.35),(4.165,4.72),(4.165,peak-.626),
                          (3.129,peak-.626),(3.129,4.75),(2.795,4.38),
                          (2.645,4.28)])
    face(b, silhouette, -.207, .043, BRICK, '8 | brick breast and splayed shoulders')
    face(b, box(2.62,.561,4.439,.602), -.247, -.17, SILL, '8 | chimney plinth ledge')

    # Three pale vertical rails can be seen through the A and O and in the
    # spaces between the letters. Their screws carry the projecting metal.
    for i, x in enumerate((3.22,3.51,3.80), 1):
        block(b, x-.013,x+.013,-.297,-.204,.09,7.318,RAIL,'8 | letter carrier '+str(i))
    survey = json.loads(SURVEY.read_bytes())
    front = survey['face_y_m']
    for item in survey['letters']:
        outline = Polygon(item['outer_xz'], item['inner_xz'])
        if lod:
            outline = outline.simplify(.0034, preserve_topology=True)
        label = '8 | chimney letter %02d %s' % (item['rank'],item['letter'])
        face(b, outline, front, front+.031, BRONZE, label)
        for i,x in enumerate((3.22,3.51,3.80),1):
            seat = outline.intersection(box(x-.011,.09,x+.011,7.31))
            if seat.area > .0007:
                y = seat.representative_point().y
                block(b,x-.010,x+.010,front+.029,-.286,y-.015,y+.015,METAL,
                      label+' mount '+str(i))


def add_gable(b, lod, layout):
    b.palette.update(PALETTE)
    windows(b,lod)
    lettered_breast(b,lod,layout)
    width=layout['wall_width']
    # Staggered brick teeth end the cream render just below the gray rake.
    for side in (0,1):
        for course in range(6):
            length = .154 if course%2 else .277
            x = width-length if side else 0.
            z = 4.52 + course*.115
            block(b,x,x+length,-.018,.008,z,z+.095,BRICK,'8 | stepped corner brick')
    for x in (1.98,5.14):
        block(b,x-.035,x+.035,-.080,.009,3.59,3.65,METAL,'8 | metal sill fixing')
