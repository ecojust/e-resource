"""Original outlined brushwork for the eight raised characters on the historic garden wall."""
import math
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from garden_plane import hit
from materials import DARK

# Extents of the dark strokes, read from the 640 x 480 publication.
LETTERS = [
    ('right', 'li-1', '立', (267, 182, 285, 193)),
    ('right', 'yan',  '言', (267, 205, 286, 217)),
    ('right', 'li-2', '立', (266, 239, 285, 251)),
    ('right', 'si',   '思', (265, 262, 285, 275)),
    ('left',  'li-1', '立', (225, 238, 245, 250)),
    ('left',  'xing', '行', (225, 263, 245, 275)),
    ('left',  'li-2', '立', (224, 296, 245, 310)),
    ('left',  'zhi',  '志', (224, 322, 244, 336)),
]


def brush(*points):
    """Outline an authored brush centre line with per-knot stroke width."""
    left, right = [], []
    for i, (x, y, width) in enumerate(points):
        x0, y0, _ = points[max(0, i-1)]
        x1, y1, _ = points[min(len(points)-1, i+1)]
        length = math.hypot(x1-x0, y1-y0)
        nx, ny = (y0-y1)/length, (x1-x0)/length
        left.append((x+nx*width/2, y+ny*width/2))
        right.append((x-nx*width/2, y-ny*width/2))
    return Polygon(left + right[::-1]).buffer(0)


def horizontal(x0, x1, y, width, flourish=0):
    return brush((x0, y+1, width*.63),
                 (x0+(x1-x0)*.12, y-1, width),
                 (x0+(x1-x0)*.68, y, width*.83),
                 (x1-5, y, width+flourish),
                 (x1, y-2-flourish*.35, width*.22))


def heart(y):
    return [
        brush((10,y+4,2), (9,y+11,6), (5,y+18,7), (3,y+20,2)),
        brush((22,y,3), (26,y+5,6), (38,y+12,8), (59,y+21,10),
              (75,y+22,9), (85,y+17,6), (90,y+11,1)),
        brush((44,y-4,3), (48,y-.4,7), (51,y+5,3)),
        brush((65,y-1,3), (70,y+2,7), (76,y+3,2))]


def glyph(character):
    if character == '立':
        strokes = [brush((47,7,3),(51,4,8),(53,9,10),(53,18,6)),
                   horizontal(13,89,23,8,1),
                   brush((30,32,2),(33,36,6),(37,47,7),(38,57,2)),
                   brush((65,31,6),(68,32,8),(62,45,8),(55,59,2)),
                   horizontal(4,97,65,10,5)]
    elif character == '言':
        strokes = [brush((47,4,2),(51,5,8),(54,12,6)), horizontal(6,94,17,8,2),
                   horizontal(20,81,29,6), horizontal(21,80,40,6),
                   Polygon([(23,48),(79,48),(75,70),(24,71)],
                           [[(30,54),(31,64),(68,63),(70,54)]])]
    elif character == '思':
        strokes = [Polygon([(19,3),(79,2),(76,40),(21,41)],
                           [[(26,10),(27,33),(69,32),(71,9)]]),
                   horizontal(26,71,22,5), brush((46,6,5),(48,20,6),(47,35,6)), *heart(45)]
    elif character == '行':
        strokes = [brush((30,4,5),(25,12,8),(16,18,7),(8,20,2)),
                   brush((31,23,6),(24,33,8),(12,42,7),(4,45,2)),
                   brush((23,33,7),(22,52,7),(22,68,5)), horizontal(47,88,12,7),
                   horizontal(40,98,30,7,2),
                   brush((72,32,7),(72,46,7),(69,64,8),(65,67,5),(56,63,1))]
    elif character == '志':
        strokes = [brush((50,2,4),(53,6,9),(51,28,7)), horizontal(10,94,16,8,1),
                   horizontal(24,80,33,7,1), *heart(44)]
    else:
        raise ValueError(character)
    outline = unary_union(strokes)
    return affinity.scale(outline, yfact=-1, origin=(0,0))


def letter_shapes():
    for col, ident, c, (u0,v0,u1,v1) in LETTERS:
        tl, tr, br, bl = [hit(u,v,-.026) for u,v in [(u0,v0),(u1,v0),(u1,v1),(u0,v1)]]
        left = (tl[0]+bl[0])*.5
        right = (tr[0]+br[0])*.5
        base = (bl[1]+br[1])*.5
        head = (tl[1]+tr[1])*.5
        shape = glyph(c)
        x0,z0,x1,z1 = shape.bounds
        shape = affinity.translate(shape, -x0, -z0)
        shape = affinity.scale(shape, (right-left)/(x1-x0), (head-base)/(z1-z0), origin=(0,0))
        yield f'{col} {ident}', c, affinity.translate(shape,left,base)


def add_letters(front, lod=False):
    for tag, _, shape in letter_shapes():
        # Stroke depth is estimated from the 2017 shadows. Preserve the holes in 言 and 田.
        front.solid(shape.simplify(.002 if lod else .0003, preserve_topology=True),
                    .006, .032, DARK, 'inscription | '+tag)
