"""Lower cross gable behind the stair, from the February 2020 east street photograph.

Coordinates use the same unscaled garden frame as the window registration. The
building builder applies the site scale once at export. The entrance-wall author
uses lower_wall_top() to close the front beneath the bargeboard.
"""
from math import ceil
from shapely.geometry import Point, Polygon, box

from placement import Facade
from residence_materials import IVORY_RENDER, SILL, LEAD, finish

RIDGE_X = -7.55
FAR_X = -10.70
NEAR_X = -2.91
FRONT = -.28
REAR = 8.13
RIDGE_Z = 8.02
FAR_Z = 6.80
NEAR_Z = 5.60
ROOF = '159 | weathered reddish clay of lower stair roof'
TILE_LIP = '159 | dark tile laps on lower stair roof'
PALETTE = {ROOF:finish((133,82,68),.93), TILE_LIP:finish((111,73,62),.94)}


def roof_top(x):
    edge, height = (FAR_X, FAR_Z) if x < RIDGE_X else (NEAR_X, NEAR_Z)
    return RIDGE_Z + (height - RIDGE_Z) * (x - RIDGE_X) / (edge - RIDGE_X)


def lower_wall_top(x):
    """Top of the supporting front wall at Y=0, measured in unscaled master units."""
    return roof_top(min(max(x, FAR_X), NEAR_X)) - .138


def _roof_strip(face, x0, x1, y0, y1, thickness, offset, material, label):
    z0, z1 = roof_top(x0) + offset, roof_top(x1) + offset
    section = Polygon([(x0,z0-thickness),(x1,z1-thickness),(x1,z1),(x0,z0)])
    face.solid(section,-y1,-y0,material,label)


def add_lower_gable(b,lod=False):
    """Build the tiled slopes, projecting dark fascia and pale verge, and chimney."""
    b.palette.update(PALETTE)
    face = Facade(b,label='159 | lower garden gable')
    for x0,x1 in ((FAR_X,RIDGE_X),(RIDGE_X,NEAR_X)):
        _roof_strip(face,x0,x1,FRONT,REAR,.14,0,ROOF,'clay slope')
        _roof_strip(face,x0,x1,FRONT-.018,FRONT+.12,.118,-.032,LEAD,'front fascia')
        _roof_strip(face,x0,x1,FRONT-.026,FRONT+.018,.037,-.012,SILL,'pale verge lip')
        # The high-resolution oblique shows tile courses across the visible right slope.
        # The outer slope screened by vegetation receives the same simple material.
        if x0 == RIDGE_X:
            courses = ceil((x1-x0)/(.40 if lod else .25))
            for i in range(1,courses):
                x = x0 + (x1-x0)*i/courses
                _roof_strip(face,x-.02,x+.014,FRONT+.025,REAR-.025,.018,.012,
                            TILE_LIP,'tile course')
            if not lod:
                for i in range(1,33):
                    y = FRONT+(REAR-FRONT)*i/33
                    face.rail([(x0+.05,y,roof_top(x0+.05)+.016),
                               (x1-.026,y,roof_top(x1-.026)+.016)],
                              .018,TILE_LIP,'tile roll',6)
    face.rail([(RIDGE_X,FRONT,RIDGE_Z+.017),(RIDGE_X,REAR,RIDGE_Z+.017)],
              .063,ROOF,'rounded ridge course',8 if lod else 12)
    # Its longer dimension, cap and three visible pots run across the ridge, as seen against the sky.
    cx,cy=-7.83,.19
    footprint=box(cx-.66,cy-.205,cx+.66,cy+.205)
    b.plan_prism(footprint,RIDGE_Z-.25,8.92,IVORY_RENDER,'159 | rendered chimney stack')
    b.plan_prism(footprint.buffer(.027,join_style=2),8.80,8.845,SILL,
                 '159 | lower chimney moulding')
    b.plan_prism(footprint.buffer(.064,join_style=2),8.92,9.015,SILL,
                 '159 | projecting chimney coping')
    for station in (-.38,0,.38):
        center=Point(cx+station,cy)
        segments=3 if lod else 6
        pot=center.buffer(.105,quad_segs=segments).difference(center.buffer(.067,quad_segs=segments))
        b.plan_prism(pot,9.005,9.61,SILL,'159 | open chimney pot')
