"""Build the three-storey rounded corner seen from Jiangxi Road and Sijing Road."""
from pathlib import Path
import math
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening
from brickwork import CENTER, EAST_AXIS, EAST_LENGTH, EAST_TANGENT, RADIUS, SOUTH_LENGTH, TURN, texture_uv

GREY = 'charcoal grey face brick'
RED = 'dull red face brick'
ARCH = 'radial red brick'
SILL = 'weathered pale sill'
GLASS = 'smoky window glass'
FRAME = 'dark painted sash'
BASE = 'dark stone plinth'
EAVE = 'pale eave soffit'
ROOF = 'dark edge flashing'
SOURCE = Path(__file__).resolve().parent
PALETTE = {
    GREY: {'color': [1., 1., 1.], 'roughness': .9, 'texture': str(SOURCE / 'grey-brick.png')},
    RED: {'color': [1., 1., 1.], 'roughness': .87, 'texture': str(SOURCE / 'red-brick.png')},
    ARCH: {'color': [.34, .135, .115], 'roughness': .88},
    SILL: {'color': [.54, .50, .43], 'roughness': .82},
    GLASS: {'color': [.105, .145, .151], 'roughness': .3, 'metallic': .12},
    FRAME: {'color': [.071, .078, .076], 'roughness': .59},
    BASE: {'color': [.066, .071, .073], 'roughness': .86},
    EAVE: {'color': [.55, .53, .44], 'roughness': .87},
    ROOF: {'color': [.116, .107, .102], 'roughness': .85},
    'carved pale stone': {'color': [.51, .47, .39], 'roughness': .83},
}

# The sill and head levels follow the photos. Only the street eave is shown above the third row.
LEVELS = [(1.01, 2.54, .24), (5.13, 2.49, .24), (8.71, 2.04, .20)]
BANDS = [(0., .46, .025, BASE), (1.17, 1.36, .012, RED), (3.27, 3.60, .015, RED),
         (4.20, 4.29, .10, RED), (4.29, 4.48, .18, RED), (4.48, 4.55, .23, SILL),
         (5.88, 5.99, .014, RED), (7.18, 7.63, .012, RED),
         (7.99, 8.09, .095, RED), (8.09, 8.16, .14, SILL), (9.36, 9.45, .012, RED),
         (10.43, 10.77, .017, RED), (11.16, 11.32, .095, RED),
         (11.32, 11.46, .32, EAVE), (11.46, 11.54, .35, ROOF)]


def arc_plan(back, front, segments):
    def points(offset):
        return [(CENTER[0] + (RADIUS + offset) * math.sin(TURN * i / segments),
                 CENTER[1] - (RADIUS + offset) * math.cos(TURN * i / segments)) for i in range(segments + 1)]
    return Polygon(points(front) + points(back)[::-1])


def arch_head(wall, u, bottom, width, height, rise, detail):
    spring = bottom + height - rise
    segments = 15 if detail else 7
    inner, outer = width * .5, width * .5 + .19
    for i in range(segments):
        a = math.pi * i / segments + (.003 if detail else 0)
        b = math.pi * (i + 1) / segments - (.003 if detail else 0)
        points = [(u + r * math.cos(t), spring + h * math.sin(t)) for r, h, t in (
            (inner, rise, a), (outer, rise + .19, a), (outer, rise + .19, b), (inner, rise, b))]
        wall.prism(Polygon(points), .015, .064, ARCH, 'segmental arch bricks')


def build_wall(builder, a, b, label, detail):
    wall = Facade(builder, a, b, label)
    lo, hi = -wall.length / 2, wall.length / 2
    is_south = label == 'Sijing'
    windows = []
    for floor, (bottom, height, rise) in enumerate(LEVELS):
        if not is_south and floor == 0:
            # The roadside photograph distinguishes a raised rectangular display opening from the door.
            windows.extend([(lo + 1.56, .91, 1.23, 2.33, 0., 'street display'),
                            (lo + 4.24, .15, 1.18, 3.03, 0., 'street door')])
            continue
        count = 3
        for index in range(count):
            u = lo + (wall.length / count) * (index + .5)
            width = (1.25 if is_south else 1.33) + (.07 if floor == 1 else 0)
            kind = 'street shutter' if floor == 0 else 'upper sash'
            windows.append((u, bottom, width, height, rise, kind))
    segments = 18 if detail else 8
    apertures = [opening(u,z,width,height,rise,segments) for u,z,width,height,rise,_ in windows]
    skin = wall.wall(0.,11.33,apertures,thickness=.44,material=GREY)
    for low, high, depth, material in BANDS:
        region = box(lo,low,hi,high)
        if high <= 11.33:
            region = region.intersection(skin)
        wall.prism(region,-.012,depth,material,'wrapped course '+material)
    for (u,z,width,height,rise,kind), aperture in zip(windows,apertures):
        if rise:
            arch_head(wall,u,z,width,height,rise,detail)
        wall.window(aperture,1 if kind.startswith('street') else 2,2,
                    frame=FRAME,glass=GLASS,trim=False,label=kind)
        if kind == 'street shutter':
            for i in range(8 if detail else 3):
                h=z+height-.23-i*(.064 if detail else .20)
                wall.box(u,h,width-.17,.037,.055,-.123,FRAME,'lower window shutters')
        if kind == 'upper sash':
            wall.box(u,z-.105,width+.31,.13,.34,.10,SILL,'projected stone sill')


def add_building(builder,lod=False):
    south_tangent = (CENTER[0],0.)
    west_end = (CENTER[0]-SOUTH_LENGTH,0.)
    north_end = tuple(v + EAST_LENGTH * d for v,d in zip(EAST_TANGENT,EAST_AXIS))
    build_wall(builder,west_end,south_tangent,'Sijing',not lod)
    build_wall(builder,EAST_TANGENT,north_end,'Jiangxi',not lod)
    segments = 20 if not lod else 9
    builder.plan_prism(arc_plan(-.44,0.,segments),0.,11.33,GREY,'rounded blind brick corner')
    for low,high,depth,material in BANDS:
        builder.plan_prism(arc_plan(-.015,depth,segments),low,high,material,'rounded '+material+' course')
    # A narrow, inward roof margin closes the visible eave while the rear roof stays in the city model.
    for start,end in [(west_end,south_tangent),(EAST_TANGENT,north_end)]:
        wall=Facade(builder,start,end,'street eave')
        wall.box(0,11.49,wall.length,.13,1.10,-.29,ROOF,'flat edge')
    builder.plan_prism(arc_plan(-.83,.27,segments),11.425,11.555,ROOF,'curved top edge')
    for part in builder.parts:
        if part['material'] in (GREY,RED):
            part['texcoords']=[(u,1-v) for u,v in (texture_uv(*xyz) for xyz in part['vertices'])]
            assert all(0<=u<=1 and 0<=v<=1 for u,v in part['texcoords'])
