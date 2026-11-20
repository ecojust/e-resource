"""Measured lancet rhythm, recessed stone tracery, and the two circular lights."""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

BRICK = 'red brick'
STONE = 'weathered pale stone'
BASE = 'granite base'
GLASS = 'recessed grey green glass'
FRAME = 'painted steel'
DOOR = 'dark timber'
TILE = 'burnt red roof tiles'
JOINT = 'warm brick bed joints'
RIDGE = 'clay ridge cap'
PALETTE = {
    BRICK: (.588,.313,.263), STONE: (.715,.716,.657), BASE: (.456,.445,.408),
    GLASS: (.195,.247,.255), FRAME: (.196,.215,.204), DOOR: (.273,.200,.147),
    TILE: (.540,.240,.160), JOINT: (.475,.323,.278), RIDGE: (.617,.288,.184),
}
PALETTE = {name: {'color': list(rgb), 'roughness': .30 if name == GLASS else .86}
           for name, rgb in PALETTE.items()}


def pointed(x, bottom, width, crown, rise, steps):
    """Two cubic arcs rise from upright jambs and meet at a single pointed apex."""
    half = width / 2
    spring = crown - rise
    side = []
    for step in range(steps + 1):
        t = step / steps
        rest = 1 - t
        xx = half * (rest**3 + 3 * rest*rest*t + 1.2 * rest*t*t)
        zz = spring + rise * (1.43 * rest*rest*t + 2.35 * rest*t*t + t**3)
        side.append((xx, zz))
    arch = [(x+dx,z) for dx,z in side] + [(x-dx,z) for dx,z in reversed(side[:-1])]
    return Polygon([(x-half,bottom),(x+half,bottom),*arch])


def glazing(f, hole, lod, columns=2, rows=3):
    x0,z0,x1,z1 = hole.bounds
    f.prism(hole.buffer(.012,join_style=2),-.36,-.327,GLASS,'inset glazing')
    inner = hole.buffer(-.064,join_style=2)
    bars = [box(x-.025,z0,x+.025,z1) for x in
            (x0+(x1-x0)*col/columns for col in range(1,columns))]
    rows = min(rows,2) if lod else rows
    bars.extend(box(x0,z-.025,x1,z+.025) for z in
                (z0+(z1-z0)*row/rows for row in range(1,rows)))
    frame = hole.buffer(-.023,join_style=2).difference(inner.difference(unary_union(bars)))
    f.prism(frame,-.28,-.205,FRAME,'metal glazing bars')


def rim(f, hole, width=.14):
    outer = hole.buffer(width,join_style=2)
    f.prism(outer.difference(hole),-.17,.089,STONE,'stone reveal')
    return outer


def rectangle(f, x, z, width, height, lod, columns=2):
    hole = box(x-width/2,z,x+width/2,z+height)
    glazing(f,hole,lod,columns,3)
    rim(f,hole,.105)
    f.box(x,z-.06,width+.32,.12,.47,.05,STONE,'projecting sill')
    return hole


def roundel(f, x, lod):
    opening = Point(x,10.31).buffer(1.00,quad_segs=10 if lod else 24)
    glazing(f,opening,lod,2,2)
    rim(f,opening,.19)
    if not lod:
        outer = opening.buffer(.22)
        f.prism(outer.difference(outer.buffer(-.057)),-.01,.133,STONE,'outer round mould')
    return opening


def twin_lancet(f, x, lod):
    outer = pointed(x,5.52,3.52,11.93,1.37,7 if lod else 15)
    holes = [pointed(x+side*.811,5.75,1.40,11.37,.70,7 if lod else 15)
             for side in (-1,1)]
    for aperture in holes:
        glazing(f,aperture,lod,2,4)
    f.prism(outer.difference(unary_union(holes)),-.20,.065,STONE,'bifurcated tracery')
    rim(f,outer,.125)
    f.box(x,5.45,3.80,.12,.42,.08,STONE,'lancet sill')
    return outer


def gable_lights(f, lod, parameters):
    g = parameters['gable']
    outer = pointed(0,g['tracery_sill'],g['tracery_outer_width'],
                    g['tracery_apex'],2.56,10 if lod else 24)
    holes = []
    pitch = 1.38
    for col in range(-2,3):
        x = pitch * col
        bottom = box(x-.49,5.57,x+.49,g['spandrel_bottom'])
        top = pointed(x,g['spandrel_top'],1.05,14.56-abs(col)*.88,.65,6 if lod else 14)
        for hole in [bottom,top]:
            glazing(f,hole,lod,1,3)
            holes.append(hole)
    stone = outer.difference(unary_union(holes))
    f.prism(stone,-.243,.082,STONE,'five paired lights and stone spandrel')
    rim(f,outer,.19)
    f.prism(outer.buffer(.238,join_style=2).difference(outer.buffer(.182,join_style=2)),
            -.046,.152,STONE,'rebated outer hood')
    f.box(0,5.255,8.62,.17,.53,.078,STONE,'main tracery sill')
    return outer


def recessed_portal(f, lod, parameters):
    g = parameters['gable']
    outer = pointed(0,.08,g['door_width'],g['door_height'],.85,8 if lod else 20)
    f.prism(outer.buffer(.010,join_style=2),-.82,-.785,DOOR,'recessed paired doors')
    f.box(0,1.70,.045,3.09,.060,-.741,FRAME,'double door seam')
    for sign in (-1,1):
        f.box(sign*.71,2.21,1.13,1.11,.045,-.744,GLASS,'portal upper glazing')
        if not lod:
            panel = box(sign*.71-.52,.36,sign*.71+.52,1.36)
            f.prism(panel.difference(panel.buffer(-.080,join_style=2)),-.781,-.740,DOOR,'door panel rails')
    for index in range(3):
        inside = outer.buffer(index*.169,join_style=2)
        casing = outer.buffer((index+1)*.169,join_style=2).difference(inside)
        f.prism(casing.intersection(box(-3,.080,3,6)),-.77,.046+.052*index,STONE,'splayed portal archivolt')
    for step in range(2):
        depth = .68 - .285 * step
        h = .081 * (step+1)
        f.box(0,h/2,4.21,h,depth,depth/2+.11,BASE,'entry step')
    return outer
